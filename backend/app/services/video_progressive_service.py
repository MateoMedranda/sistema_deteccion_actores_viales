"""Read operations never enqueue inference."""



class ProgressiveService:
    def __init__(self, store, legacy):
        self.store, self.legacy = store, legacy

    def snapshot(self, job, owner):
        return self.store.snapshot(job, owner)

    def withdraw(self, job, owner):
        self.store.withdraw(job, owner)

    def frames(self, *args, **kwargs):
        return self.store.frames(*args, **kwargs)
