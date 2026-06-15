from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class CodigoRespuesta(BaseModel):
    """Item de `codigosRespuestas`: mensaje (código + descripción) devuelto por el SIN."""

    codigo: str
    descripcion: str


class AutenticacionSolicitud(BaseModel):
    """
    Credenciales de Oficina Virtual ("SIAT en Línea") del contribuyente, para
    `ServicioAutenticacionSoap` (`DatosUsuarioRequest`). Devuelve el token JWT usado en
    el header `Authorization: Token <jwt>` de los demás servicios.
    """

    nit: int
    login: str
    password: str


class AutenticacionResultado(BaseModel):
    ok: bool
    token: str | None = None
    mensajes: list[CodigoRespuesta] = []


class CuisSolicitud(BaseModel):
    """Datos para `solicitudCuis` (Código Único de Inicio de Sistemas)."""

    codigo_ambiente: int = Field(ge=1, le=2)  # 1=Producción, 2=Pruebas y Piloto
    codigo_sistema: str
    nit: int
    codigo_modalidad: int = Field(ge=1, le=2)  # 1=Electrónica en Línea, 2=Computarizada en Línea
    codigo_sucursal: int
    codigo_punto_venta: int = 0  # 0 si no corresponde a un punto de venta


class CuisResultado(BaseModel):
    codigo_cuis: str
    fecha_vigencia: datetime
    transaccion: bool
    codigos_respuestas: list[CodigoRespuesta] = []


class CufdSolicitud(BaseModel):
    """Datos para `solicitudCufd` (Código Único de Facturación Diaria)."""

    codigo_ambiente: int = Field(ge=1, le=2)  # 1=Producción, 2=Pruebas y Piloto
    codigo_sistema: str
    nit: int
    codigo_modalidad: int = Field(ge=1, le=2)  # 1=Electrónica en Línea, 2=Computarizada en Línea
    codigo_sucursal: int
    codigo_punto_venta: int = 0  # 0 si no corresponde a un punto de venta
    cuis: str


class CufdResultado(BaseModel):
    """
    Resultado de `solicitudCufd`.

    `codigo_cufd` (campo `codigoCUFD`) es el valor que va en `<cufd>` de la factura y en
    `RecepcionFactura`. `codigo_control` (campo `codigoControl`) es el "código de
    control" que se concatena como sufijo del CUF (ver `cuf/cuf_generator.py`) — son
    campos distintos, no intercambiables.
    """

    codigo_cufd: str
    codigo_control: str
    direccion: str | None = None
    fecha_vigencia: datetime
    transaccion: bool
    codigos_respuestas: list[CodigoRespuesta] = []


class FacturaSiatItem(BaseModel):
    """
    Un `<detalle>` de "Factura Compra Venta" (electrónica/computarizada).

    Nombres y restricciones según el XSD oficial del SIN
    (`app/integrations/siat/xsd/facturas/facturaElectronicaCompraVenta.xsd`).
    """

    actividad_economica: str = Field(min_length=1, max_length=10)
    codigo_producto_sin: int = Field(ge=1, le=99999999)
    codigo_producto: str = Field(min_length=1, max_length=50)
    descripcion: str = Field(min_length=1, max_length=500)
    cantidad: Decimal = Field(gt=0)
    unidad_medida: int = Field(ge=1, le=200)
    precio_unitario: Decimal = Field(gt=0)
    monto_descuento: Decimal | None = Field(default=None, ge=0)
    subtotal: Decimal = Field(gt=0)
    numero_serie: str | None = Field(default=None, max_length=1500)
    numero_imei: str | None = Field(default=None, max_length=1500)


class FacturaSiatPayload(BaseModel):
    """
    Datos de una "Factura Compra Venta" (electrónica/computarizada) listos para generar
    su XML y enviarlos al SIN.

    Nombres y restricciones según el XSD oficial del SIN
    (`app/integrations/siat/xsd/facturas/facturaElectronicaCompraVenta.xsd`), salvo
    `items` (lista de `<detalle>`, 1 a 500 según el XSD).
    """

    nit_emisor: int = Field(ge=1, le=9999999999999)
    razon_social_emisor: str = Field(min_length=1, max_length=200)
    municipio: str = Field(min_length=1, max_length=25)
    telefono: str | None = Field(default=None, min_length=1, max_length=25)
    numero_factura: int = Field(ge=1, le=9999999999)
    cuf: str = Field(min_length=1, max_length=100)
    cufd: str = Field(min_length=1, max_length=100)
    codigo_sucursal: int = Field(ge=0, le=9999)
    direccion: str = Field(min_length=1, max_length=500)
    codigo_punto_venta: int | None = Field(default=None, ge=0, le=9999)
    fecha_emision: datetime
    nombre_razon_social: str | None = Field(default=None, min_length=1, max_length=500)
    codigo_tipo_documento_identidad: int = Field(ge=1, le=5)
    numero_documento: str = Field(min_length=1, max_length=20)
    complemento: str | None = Field(default=None, max_length=5)
    codigo_cliente: str = Field(min_length=1, max_length=100)
    codigo_metodo_pago: int = Field(ge=1, le=308)
    numero_tarjeta: int | None = Field(default=None, ge=0, le=9999999999999999)
    monto_total: Decimal = Field(gt=0)
    monto_total_sujeto_iva: Decimal = Field(ge=0)
    codigo_moneda: int = Field(ge=1, le=154)
    tipo_cambio: Decimal = Field(gt=0)
    monto_total_moneda: Decimal = Field(gt=0)
    monto_gift_card: Decimal | None = Field(default=None, ge=0)
    descuento_adicional: Decimal | None = Field(default=None, ge=0)
    codigo_excepcion: int | None = Field(default=None, ge=0, le=1)
    cafc: str | None = Field(default=None, min_length=1, max_length=50)
    leyenda: str = Field(min_length=1, max_length=200)
    usuario: str = Field(min_length=1, max_length=100)
    codigo_documento_sector: int = 1
    items: list[FacturaSiatItem] = Field(min_length=1, max_length=500)


class RecepcionResultado(BaseModel):
    """Resultado de enviar una factura (o paquete) al SIN."""

    transaccion: bool
    codigo_recepcion: str | None = None
    codigo_descripcion: str | None = None
    observaciones: list[str] = []


class EmisionResultado(BaseModel):
    """Resultado del flujo completo de emisión de una "Factura Compra Venta"."""

    cuf: str
    cufd: str
    transaccion_recepcion: bool
    codigo_recepcion: str | None = None
    estado_factura: str | None = None
    transaccion_estado: bool | None = None
    observaciones: list[str] = []
