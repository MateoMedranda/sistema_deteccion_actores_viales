"""Periodic TTL enforcement independent of incoming HTTP traffic."""
import threading

class PeriodicCleanup:
    def __init__(self, resources, logger, interval=1.0):
        self.resources, self.logger, self.interval = resources, logger, interval
        self.stop_event = threading.Event()
        self.thread = threading.Thread(target=self._run, daemon=True, name="temporary-cleanup")

    def start(self):
        self.thread.start()

    def run_once(self):
        for resource in self.resources:
            try:
                resource.cleanup()
            except Exception:
                self.logger.error("temporary_cleanup_failed", extra={"error_code":"cleanup_failed"})

    def _run(self):
        while not self.stop_event.wait(self.interval):
            self.run_once()

    def close(self):
        self.stop_event.set()
        if self.thread.is_alive():
            self.thread.join()
