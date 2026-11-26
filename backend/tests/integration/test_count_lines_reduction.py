"""Isolation must hold across cooperative turns, not only on a fast machine."""
from copy import deepcopy
from types import SimpleNamespace

import pytest

from app.api.error_handlers import ApiError
import app.services.count_lines_reducer as module
from tests.integration.test_count_line_mutations import service, apply
from tests.fixtures_011 import line, frame, observation


class StepClock:
    """Advance only the reducer's clock so every frame exceeds its 5 ms turn."""

    def __init__(self):
        self.value = 0.0

    def __call__(self):
        self.value += 0.006
        return self.value


def force_frame_boundary(monkeypatch):
    # Replace the reducer's binding, not time.perf_counter shared by pytest/logging.
    monkeypatch.setattr(module, "time", SimpleNamespace(perf_counter=StepClock()))


@pytest.fixture(params=["ordinary", "forced-yield"])
def count_service(tmp_path, request, monkeypatch):
    if request.param == "forced-yield":
        force_frame_boundary(monkeypatch)
    store, state, counts = service(tmp_path)
    try:
        yield store, state, counts
    finally:
        store.db.close()


def reduce_until(counts, state, revision, at_us, expected, max_turns=20):
    """Bound reconstruction by observed status/revision without sleeps or retries."""
    for turn in range(max_turns + 1):
        snapshot = counts.snapshot("test", "owner", state["generation"], revision, at_us)
        values = {value["line_id"]: value for value in snapshot["lines"]}
        if values.keys() == expected.keys() and all(
            (values[line_id]["status"], values[line_id]["geometry_revision"]) == target
            for line_id, target in expected.items()
        ):
            return values
        if turn < max_turns:
            counts.reduce("test")
    pytest.fail(f"Coverage/status did not converge in {max_turns} turns: {values}")


def test_failure_of_pending_line_preserves_completed_line(count_service, monkeypatch):
    store, state, counts = count_service
    a = line("A")
    b = line("B", "#112233", .6)
    apply(counts, state, [a])
    store.publish("test", [frame(0, [observation(y=20)]), frame(1, [observation(y=80)])])
    before = reduce_until(counts, state, 1, 100000, {a["line_id"]: ("ready", 1)})
    assert before[a["line_id"]]["total"] == 1
    assert before[a["line_id"]]["covered_until_us"] == 200000
    apply(counts, state, [a, b], 1)

    def fail(*args):
        raise RuntimeError("controlled failure")

    monkeypatch.setattr(module, "advance", fail)
    values = reduce_until(counts, state, 2, 100000, {
        a["line_id"]: ("ready", 1), b["line_id"]: ("unavailable", 1),
    })
    assert values[a["line_id"]] == before[a["line_id"]]
    assert values[b["line_id"]]["error_code"] == "count_reducer_failed"
    assert values[b["line_id"]]["total"] is None


@pytest.mark.parametrize("operation", ["geometry", "delete", "retire"])
def test_failure_does_not_publish_into_changed_or_retired_context(count_service, monkeypatch, operation):
    store, state, counts = count_service
    a = line("A")
    apply(counts, state, [a])
    store.publish("test", [frame(0, [observation(y=20)])])

    def fail(*args):
        if operation == "geometry":
            moved = deepcopy(a)
            moved["segment"]["point_a"]["y"] = .7
            apply(counts, state, [moved], 1)
        elif operation == "delete":
            apply(counts, state, [], 1)
        else:
            with store.lock, store.db:
                store.db.execute("UPDATE p_video SET retired=1 WHERE job=?", ("test",))
        raise RuntimeError("controlled stale failure")

    monkeypatch.setattr(module, "advance", fail)
    if operation == "retire":
        with pytest.raises(ApiError):
            counts.reduce("test")
    else:
        counts.reduce("test")
    row = store.db.execute("SELECT error FROM p_count_lines WHERE job=?", ("test",)).fetchone()
    assert row["error"] is None


def fail_only_a(monkeypatch):
    original = module.advance

    def advance(state, point, geometry, *args):
        if geometry[0][1] == 50:
            raise RuntimeError("only A")
        return original(state, point, geometry, *args)

    monkeypatch.setattr(module, "advance", advance)


def test_one_failed_line_does_not_poison_another_pending_line(count_service, monkeypatch):
    store, state, counts = count_service
    a = line("A", y=.5)
    b = line("B", "#112233", .6)
    apply(counts, state, [a, b])
    store.publish("test", [frame(0, [observation(y=20)]), frame(1, [observation(y=80)])])
    fail_only_a(monkeypatch)
    values = reduce_until(counts, state, 1, 100000, {
        a["line_id"]: ("unavailable", 1), b["line_id"]: ("ready", 1),
    })
    assert values[a["line_id"]]["error_code"] == "count_reducer_failed"
    assert values[b["line_id"]]["error_code"] is None
    assert values[b["line_id"]]["total"] == 1
    assert values[b["line_id"]]["covered_until_us"] == 200000


def test_forced_budget_yield_keeps_pending_null_then_confirms_one_crossing(tmp_path, monkeypatch):
    force_frame_boundary(monkeypatch)
    store, state, counts = service(tmp_path)
    try:
        assert counts.settings.video_count_reducer_budget_ms == 5
        a = line("A", y=.5)
        b = line("B", "#112233", .6)
        apply(counts, state, [a, b])
        store.publish("test", [frame(0, [observation(y=20)]), frame(1, [observation(y=80)])])
        fail_only_a(monkeypatch)
        counts.reduce("test")
        first = counts.snapshot("test", "owner", state["generation"], 1, 100000)["lines"]
        assert first[0]["status"] == "unavailable"
        assert first[0]["error_code"] == "count_reducer_failed"
        assert first[1]["status"] == "pending"
        assert first[1]["geometry_revision"] == 1
        assert first[1]["covered_until_us"] == 100000
        assert first[1]["total"] is None
        assert first[1]["error_code"] is None
        # Zero is valid for the covered first frame, not for the pending second one.
        assert counts.snapshot("test", "owner", state["generation"], 1, 0)["lines"][1]["total"] == 0
        final = reduce_until(counts, state, 1, 100000, {
            a["line_id"]: ("unavailable", 1), b["line_id"]: ("ready", 1),
        })
        assert final[b["line_id"]]["covered_until_us"] == 200000
        assert final[b["line_id"]]["total"] == 1
        assert final[b["line_id"]]["error_code"] is None
        for _ in range(2):
            counts.reduce("test")
        assert counts.snapshot("test", "owner", state["generation"], 1, 100000)["lines"][1] == final[b["line_id"]]
        events = store.db.execute(
            "SELECT count(*) FROM p_count_lines_events WHERE job=? AND generation=? AND line_id=? AND geometry_revision=?",
            ("test", state["generation"], b["line_id"], 1),
        ).fetchone()[0]
        assert events == 1
    finally:
        store.db.close()
