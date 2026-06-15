import hashlib
import secrets

from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.integration import ApiKey

_KEY_PREFIX = "sk_"
_KEY_BYTES = 32


def generar_api_key() -> tuple[str, str, str]:
    """Retorna (clave_raw, prefijo, clave_hash). La clave_raw sólo se muestra una vez."""
    raw = _KEY_PREFIX + secrets.token_urlsafe(_KEY_BYTES)
    prefijo = raw[:12]
    clave_hash = hashlib.sha256(raw.encode()).hexdigest()
    return raw, prefijo, clave_hash


def _hash_key(raw: str) -> str:
    return hashlib.sha256(raw.encode()).hexdigest()


def requerir_api_key(
    x_api_key: str = Header(..., alias="X-API-Key"),
    db: Session = Depends(get_db),
) -> ApiKey:
    clave_hash = _hash_key(x_api_key)
    api_key = (
        db.query(ApiKey).filter(ApiKey.clave_hash == clave_hash, ApiKey.activa.is_(True)).first()
    )
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="API key inválida o inactiva")
    return api_key
