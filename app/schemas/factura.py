import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.facturacion import EstadoFactura


class DosificacionBase(BaseModel):
    actividad_economica_id: uuid.UUID
    tipo_documento_sector: int
    numero_inicial: int
    numero_final: int
    clave_dosificacion_ref: str
    fecha_limite_emision: datetime


class DosificacionCreate(DosificacionBase):
    pass


class DosificacionRead(DosificacionBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    punto_venta_id: uuid.UUID
    numero_actual: int


class FacturaItemBase(BaseModel):
    descripcion: str
    cantidad: Decimal
    precio_unitario: Decimal
    subtotal: Decimal


class FacturaItemCreate(FacturaItemBase):
    pass


class FacturaItemRead(FacturaItemBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID


class FacturaCreate(BaseModel):
    sucursal_id: uuid.UUID
    punto_venta_id: uuid.UUID
    dosificacion_id: uuid.UUID
    cliente_id: uuid.UUID
    fecha_emision: datetime
    moneda: str = "BOB"
    monto_total: Decimal
    tipo_documento_sector: int
    items: list[FacturaItemCreate]


class FacturaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    sucursal_id: uuid.UUID
    punto_venta_id: uuid.UUID
    dosificacion_id: uuid.UUID
    cliente_id: uuid.UUID
    numero_factura: int
    cuf: str | None
    cufd: str | None
    fecha_emision: datetime
    moneda: str
    monto_total: Decimal
    tipo_documento_sector: int
    estado: EstadoFactura
    items: list[FacturaItemRead]
