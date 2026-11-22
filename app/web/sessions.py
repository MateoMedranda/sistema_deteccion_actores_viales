from __future__ import annotations
from dataclasses import dataclass,field
from datetime import UTC,datetime,timedelta
import hashlib,hmac,secrets,threading
from uuid import uuid4

@dataclass
class WebSession:
    epoch:str
    csrf:str
    created_at:datetime
    expires_at:datetime
    policy:dict
    intents:dict=field(default_factory=dict)

class SessionStore:
    """Bounded, absolute-expiry RAM sessions; cookie values are never retained."""
    def __init__(self,ttl=900,maximum=128,clock=None):
        self.ttl,self.maximum=ttl,maximum
        self.clock=clock or (lambda:datetime.now(UTC))
        self.sessions:dict[str,WebSession]={}
        self.secret=secrets.token_bytes(32)
        self.lock=threading.RLock()
    @staticmethod
    def digest(token):return hashlib.sha256(token.encode()).hexdigest()
    def cleanup(self):
        with self.lock:
            now=self.clock()
            for key in list(self.sessions):
                if self.sessions[key].expires_at<=now:del self.sessions[key]
    def create(self,policy):
        with self.lock:
            self.cleanup()
            if len(self.sessions)>=self.maximum:raise OverflowError("session_capacity")
            token=secrets.token_urlsafe(32);now=self.clock()
            session=WebSession(str(uuid4()),secrets.token_urlsafe(32),now,now+timedelta(seconds=self.ttl),policy)
            self.sessions[self.digest(token)]=session
            return token,session
    def get(self,token):
        if not token or len(token)>128:return None
        self.cleanup()
        with self.lock:return self.sessions.get(self.digest(token))
    def remove(self,token):
        if token:
            with self.lock:self.sessions.pop(self.digest(token),None)
    def close(self):
        with self.lock:self.sessions.clear()
    def upstream_key(self,token,operation,intent):
        return hmac.new(self.secret,(self.digest(token)+"|"+operation+"|"+intent).encode(),hashlib.sha256).hexdigest()
