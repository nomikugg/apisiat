from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class CufdSolicitud(BaseModel):
    """Datos necesarios para solicitar/generar un CUFD para un punto de venta."""

    nit: int
    codigo_sucursal: int
    codigo_punto_venta: int
    codigo_modalidad: int
    codigo_ambiente: int  # 1=Producción, 2=Piloto/Pruebas


class CufdResultado(BaseModel):
    codigo: str
    direccion: str | None = None
    vigente_desde: datetime
    vigente_hasta: datetime


class FacturaSiatItem(BaseModel):
    """Item de una factura, espejo de `app.models.facturacion.FacturaItem`."""

    descripcion: str
    cantidad: Decimal
    precio_unitario: Decimal
    subtotal: Decimal


class FacturaSiatPayload(BaseModel):
    """Datos de una factura listos para generar su XML y enviarlos al SIN."""

    nit_emisor: int
    razon_social_emisor: str
    municipio: str
    numero_factura: int
    cuf: str
    cufd: str
    fecha_emision: datetime
    codigo_sucursal: int
    codigo_punto_venta: int
    tipo_documento_sector: int
    cliente_nombre_razon_social: str
    cliente_numero_documento: str
    cliente_complemento: str | None = None
    moneda: str = "BOB"
    monto_total: Decimal
    items: list[FacturaSiatItem]


class RecepcionResultado(BaseModel):
    """Resultado de enviar una factura (o paquete) al SIN."""

    transaccion: bool
    codigo_recepcion: str | None = None
    codigo_descripcion: str | None = None
    observaciones: list[str] = []
