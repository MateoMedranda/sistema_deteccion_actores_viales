"""Bounded durable ownership receipts for temporary image files; no media or secrets."""
from datetime import UTC,datetime,timedelta
import json
from pathlib import Path
from threading import RLock
from uuid import uuid4
import re

class ManagedImageFiles:
    def __init__(self,root:Path,namespace:str,clock=None):
        self.root=Path(root)
        self.root.mkdir(parents=True,exist_ok=True)
        self.namespace=namespace
        self.clock=clock or (lambda:datetime.now(UTC))
        self.lock=RLock()

    def _receipt(self,path):
        return path.with_name(path.name+".expiry.json")

    def save(self,data:bytes,suffix:str,expires_at):
        with self.lock:
            path=self.root/(self.namespace+"-"+uuid4().hex+suffix)
            receipt=self._receipt(path)
            # Durable ownership/deadline is recorded before writing any sensitive bytes.
            with receipt.open("x",encoding="utf-8") as handle:
                json.dump({"version":1,"expires_at":expires_at.isoformat()},handle)
            try:path.write_bytes(data)
            except BaseException:
                path.unlink(missing_ok=True);receipt.unlink(missing_ok=True);raise
            return path

    def limit_expiry(self,path,expires_at):
        path=Path(path)
        if path.parent.resolve()!=self.root.resolve():raise ValueError("outside_owned_root")
        with self.lock:
            receipt=self._receipt(path)
            record=json.loads(receipt.read_text(encoding="utf-8"))
            expiry=min(datetime.fromisoformat(record["expires_at"]),expires_at)
            if expiry.isoformat()!=record["expires_at"]:
                temporary=receipt.with_name(receipt.name+".new")
                temporary.write_text(json.dumps({"version":1,"expires_at":expiry.isoformat()}),encoding="utf-8")
                temporary.replace(receipt)

    def remove(self,path):
        path=Path(path)
        if path.parent.resolve()!=self.root.resolve():raise ValueError("outside_owned_root")
        with self.lock:
            path.unlink(missing_ok=True);self._receipt(path).unlink(missing_ok=True)

    def cleanup(self,now=None):
        now=now or self.clock()
        with self.lock:
            # Only files with our exact namespace and durable receipt are managed.
            for receipt in self.root.glob(self.namespace+"-*.expiry.json"):
                name=receipt.name.removesuffix(".expiry.json")
                if not re.fullmatch(re.escape(self.namespace)+r"-[0-9a-f]{32}\.(png|jpg)",name):continue
                try:
                    data=json.loads(receipt.read_text(encoding="utf-8"))
                    expiry=datetime.fromisoformat(data["expires_at"])
                    if data.get("version")!=1 or expiry.tzinfo is None:continue
                except (OSError,ValueError,KeyError,TypeError):continue
                if expiry<=now:self.remove(self.root/name)
