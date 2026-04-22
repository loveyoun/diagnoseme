import uuid
from dataclasses import dataclass
from datetime import timedelta, timezone, datetime
from typing import Literal

import jwt

TokenType = Literal["access", "refresh"]

@dataclass(frozen=True)
class JwtConfig:
    secret: str
    algorithm: str = "HS256"
    access_ttl_minutes: int = 15
    refresh_ttl_days: int = 7
    issuer: str = "diagnoseme"
    audience: str = "diagnoseme-clients"

class JwtService:
    def __init__(self, config: JwtConfig):
        self._cfg = config

    @property
    def refresh_expires_delta(self) -> timedelta:
        return timedelta(days=self._cfg.refresh_ttl_days)

    def issue(self, *, token_type:TokenType, user_id:int, jti: str|None=None)-> str:
        now = datetime.now(tz=timezone.utc)
        if token_type == "access":
            exp = now + timedelta(minutes=self._cfg.access_ttl_minutes)
        else:
            exp = now + timedelta(days=self._cfg.refresh_ttl_days)

        payload = {
            "typ": token_type,
            "sub": str(user_id),
            "iss": self._cfg.issuer,
            "aud": self._cfg.audience,
            "iat": int(now.timestamp()),
            "exp": int(exp.timestamp()),}

        if token_type == "refresh":
            payload["jti"] = jti or str(uuid.uuid4())

        return jwt.encode(payload, self._cfg.secret, algorithm=self._cfg.algorithm)
