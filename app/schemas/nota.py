import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.facturacion import EstadoFactura, TipoDocumentoFiscal


class NotaCreate(BaseModel):
    tipo: TipoDocumentoFiscal
    motivo: str
    monto: Decimal
    codigo_documento_sector: int


class NotaRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    factura_id: uuid.UUID
    tipo: TipoDocumentoFiscal
    motivo: str
    monto: Decimal
    numero_nota: int
    codigo_documento_sector: int
    cuf: str | None
    cufd: str | None
    estado: EstadoFactura
    created_at: datetime


class NotaEmisionRequest(BaseModel):
    """Datos del SIN necesarios para emitir la nota (no derivables de la factura original)."""

    nit: int
    login: str
    password: str
    codigo_sistema: str
    codigo_ambiente: int = 2
    municipio: str
    codigo_metodo_pago: int = 1
    codigo_moneda: int = 1
    tipo_cambio: Decimal = Decimal("1.00")
    usuario: str
    leyenda: str
    telefono: str | None = None
    actividad_economica: str
    codigo_producto_sin: int
    codigo_producto: str
    unidad_medida: int


class NotaEmisionResponse(BaseModel):
    nota: NotaRead
    transaccion_recepcion: bool
    codigo_recepcion: str | None
    estado_factura: str | None
    observaciones: list[str]
