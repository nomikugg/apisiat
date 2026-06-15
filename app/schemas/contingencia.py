import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ContingencyEventCreate(BaseModel):
    punto_venta_id: uuid.UUID
    motivo: str


class ContingencyEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    punto_venta_id: uuid.UUID
    inicio: datetime
    fin: datetime | None
    motivo: str
    resuelto: bool
    created_at: datetime


class ReintentoRequest(BaseModel):
    nit: int
    login: str
    password: str
    codigo_sistema: str
    codigo_ambiente: int = 2


class ReintentoResponse(BaseModel):
    exitosas: int
    fallidas: int
    errores: list[str]
