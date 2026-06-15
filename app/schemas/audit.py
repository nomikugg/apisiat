import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class AuditLogRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID | None
    actor: str
    accion: str
    entidad: str
    entidad_id: str | None
    detalle: dict | None
    created_at: datetime
