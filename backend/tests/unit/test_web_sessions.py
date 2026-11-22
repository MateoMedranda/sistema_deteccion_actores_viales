import pytest
from tests.fixtures_008 import Clock
from app.web.sessions import SessionStore
def test_sessions_are_absolute_bounded_hashed_and_revocable():
 clock=Clock();store=SessionStore(ttl=60,maximum=1,clock=clock)
 token,session=store.create({"capabilities":{}})
 assert token not in store.sessions and len(session.csrf)==43
 assert store.get(token) is session
 with pytest.raises(OverflowError):store.create({})
 clock.advance(59);assert store.get(token) is session
 clock.advance(2);assert store.get(token) is None
 assert not store.sessions
 token,_=store.create({});store.remove(token);assert store.get(token) is None
