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


class EmisionItemExtra(BaseModel):
    """Datos de un ítem requeridos por el SIN que aún no se persisten en `FacturaItem`."""

    actividad_economica: str
    codigo_producto_sin: int
    codigo_producto: str
    unidad_medida: int
    monto_descuento: Decimal | None = None


class EmisionFacturaRequest(BaseModel):
    """
    Datos requeridos para emitir una factura PENDIENTE ante el SIN (mock) que aún no se
    persisten en nuestro esquema: credenciales de Oficina Virtual (hasta que exista
    resolución de secretos vía `Credential`/Vault) y campos del SIN sin catálogo propio
    (ver docs/04).
    """

    nit: int
    login: str
    password: str
    codigo_sistema: str
    codigo_ambiente: int = 2
    municipio: str
    codigo_metodo_pago: int = 1
    codigo_moneda: int = 1
    tipo_cambio: Decimal = Decimal("1.00")
    codigo_tipo_documento_identidad: int = 1
    usuario: str
    leyenda: str
    telefono: str | None = None
    items: list[EmisionItemExtra]


class EmisionFacturaResponse(BaseModel):
    factura: FacturaRead
    transaccion_recepcion: bool
    codigo_recepcion: str | None
    estado_factura: str | None
    observaciones: list[str]
