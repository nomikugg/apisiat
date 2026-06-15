import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import generar_api_key
from app.models.integration import ApiKey
from app.models.tenant import Tenant
from app.schemas.api_key import ApiKeyCreate, ApiKeyCreated, ApiKeyRead

router = APIRouter(tags=["api-keys"])


def _get_tenant_or_404(db: Session, tenant_id: uuid.UUID) -> Tenant:
    tenant = db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")
    return tenant


@router.post(
    "/tenants/{tenant_id}/api-keys",
    response_model=ApiKeyCreated,
    status_code=status.HTTP_201_CREATED,
)
def crear_api_key(tenant_id: uuid.UUID, payload: ApiKeyCreate, db: Session = Depends(get_db)) -> ApiKeyCreated:
    _get_tenant_or_404(db, tenant_id)
    clave_raw, prefijo, clave_hash = generar_api_key()
    api_key = ApiKey(
        tenant_id=tenant_id,
        nombre=payload.nombre,
        prefijo=prefijo,
        clave_hash=clave_hash,
    )
    db.add(api_key)
    db.commit()
    db.refresh(api_key)
    return ApiKeyCreated(
        id=api_key.id,
        tenant_id=api_key.tenant_id,
        nombre=api_key.nombre,
        prefijo=api_key.prefijo,
        clave=clave_raw,
        created_at=api_key.created_at,
    )


@router.get("/tenants/{tenant_id}/api-keys", response_model=list[ApiKeyRead])
def listar_api_keys(tenant_id: uuid.UUID, db: Session = Depends(get_db)) -> list[ApiKey]:
    _get_tenant_or_404(db, tenant_id)
    return list(
        db.query(ApiKey)
        .filter(ApiKey.tenant_id == tenant_id)
        .order_by(ApiKey.created_at.desc())
        .all()
    )


@router.delete("/api-keys/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
def desactivar_api_key(key_id: uuid.UUID, db: Session = Depends(get_db)) -> None:
    api_key = db.get(ApiKey, key_id)
    if api_key is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key no encontrada")
    api_key.activa = False
    db.commit()
