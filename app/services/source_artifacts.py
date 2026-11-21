from datetime import UTC,datetime,timedelta
from pathlib import Path
from app.services.managed_image_files import ManagedImageFiles

class SourceArtifactStore:
    """Private image files with durable, non-sensitive expiry receipts."""
    def __init__(self,root:Path):
        self.root=Path(root)
        self.files=ManagedImageFiles(self.root,"source")
        self._created=set()

    def save(self,data:bytes,suffix=".bin",*,expires_at=None):
        expiry=expires_at or datetime.now(UTC)+timedelta(minutes=15)
        path=self.files.save(data,suffix,expiry)
        self._created.add(path)
        return path

    def remove(self,path):
        self.files.remove(path);self._created.discard(path)

    def limit_expiry(self,path,expires_at):
        self.files.limit_expiry(path,expires_at)

    def cleanup(self,now=None):
        self.files.cleanup(now)

    def close(self):
        for path in list(self._created):self.remove(path)
