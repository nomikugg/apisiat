import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ApiKeyCreate(BaseModel):
    nombre: str


class ApiKeyCreated(BaseModel):
    """Respuesta de creación: incluye la clave en texto plano, sólo visible una vez."""

    id: uuid.UUID
    tenant_id: uuid.UUID | None
    nombre: str
    prefijo: str
    clave: str
    created_at: datetime


class ApiKeyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID | None
    nombre: str
    prefijo: str
    activa: bool
    created_at: datetime
    ultimo_uso: datetime | None
