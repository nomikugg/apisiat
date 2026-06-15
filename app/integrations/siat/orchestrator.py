"""
Orquestador del flujo completo de emisión de una "Factura Compra Venta" (modalidad
Computarizada en Línea) ante el SIN.

Ensambla, como una sola función reutilizable, el flujo ya validado contra el mock local
en `tests/integrations/siat/test_mock_e2e.py`: autenticación -> CUIS -> CUFD -> generar
CUF -> construir XML -> validar contra XSD -> huella digital -> `RecepcionFactura` ->
`verificacionEstadoFactura`.

Solo soporta modalidad Computarizada (`codigoModalidad=2`, sin firma XML-DSig). La
modalidad Electrónica requiere certificado PKCS#12 (`signing.firmar_xml`) y no está
cubierta aquí.
"""

from datetime import datetime, timezone

from lxml import etree

from app.integrations.siat.exceptions import SiatValidationError
from app.integrations.siat.paquetes import comprimir_gzip
from app.integrations.siat.schemas import AutenticacionSolicitud, EmisionResultado, FacturaSiatPayload
from app.integrations.siat.signing import huella_digital
from app.integrations.siat.soap_client import SiatAuthClient, SiatSoapClient
from app.integrations.siat.xml_builder import build_factura_compra_venta_xml, validar_contra_xsd

from .cuf import generar_cuf

_CODIGO_MODALIDAD_COMPUTARIZADA = 2


def emitir_factura_compra_venta(
    payload: FacturaSiatPayload,
    *,
    auth: AutenticacionSolicitud,
    codigo_sistema: str,
    codigo_ambiente: int,
    codigo_sucursal: int,
    codigo_punto_venta: int,
    wsdl_autenticacion: str | None = None,
    wsdl_facturacion: str | None = None,
) -> EmisionResultado:
    """
    Ejecuta el flujo completo de emisión de `payload` (modalidad Computarizada).

    `payload.cuf`, `payload.cufd` y `payload.direccion` se sobreescriben con los valores
    obtenidos de CUFD/CUF antes de construir el XML (los del `payload` de entrada son
    placeholders).
    """
    auth_client = SiatAuthClient(wsdl_autenticacion)
    token = auth_client.autenticar(nit=auth.nit, login=auth.login, password=auth.password)

    cliente = SiatSoapClient(wsdl_facturacion, token=token)
    cliente.verificar_comunicacion()

    cuis = cliente.solicitud_cuis(
        codigoAmbiente=codigo_ambiente,
        codigoSistema=codigo_sistema,
        nit=auth.nit,
        codigoModalidad=_CODIGO_MODALIDAD_COMPUTARIZADA,
        codigoSucursal=codigo_sucursal,
        codigoPuntoVenta=codigo_punto_venta,
    )

    cufd = cliente.solicitud_cufd(
        codigoAmbiente=codigo_ambiente,
        codigoSistema=codigo_sistema,
        nit=auth.nit,
        codigoModalidad=_CODIGO_MODALIDAD_COMPUTARIZADA,
        codigoSucursal=codigo_sucursal,
        codigoPuntoVenta=codigo_punto_venta,
        cuis=cuis.codigoCuis,
    )

    cuf = generar_cuf(
        nit=auth.nit,
        fecha_hora_emision=payload.fecha_emision,
        sucursal=codigo_sucursal,
        modalidad=_CODIGO_MODALIDAD_COMPUTARIZADA,
        tipo_emision=1,
        tipo_factura_documento_ajuste=1,
        tipo_documento_sector=payload.codigo_documento_sector,
        numero_factura=payload.numero_factura,
        punto_venta=codigo_punto_venta,
        codigo_control=cufd.codigoControl,
    )

    payload.cuf = cuf
    payload.cufd = cufd.codigoCufd
    if cufd.direccion:
        payload.direccion = cufd.direccion

    xml = build_factura_compra_venta_xml(payload, modalidad="computarizada")
    try:
        validar_contra_xsd(xml, modalidad="computarizada")
    except etree.DocumentInvalid as exc:
        raise SiatValidationError(f"XML de factura inválido según el XSD del SIN: {exc}") from exc

    recepcion = cliente.recepcion_factura(
        codigoAmbiente=codigo_ambiente,
        codigoModalidad=_CODIGO_MODALIDAD_COMPUTARIZADA,
        codigoEmision=1,
        codigoDocumentoSector=payload.codigo_documento_sector,
        codigoSistema=codigo_sistema,
        nit=auth.nit,
        cuis=cuis.codigoCuis,
        cufd=cufd.codigoCufd,
        codigoMetodoEnvio=1,
        archivo=comprimir_gzip(xml),
        fechaEnvio=datetime.now(timezone.utc),
        hashArchivo=huella_digital(xml),
    )

    estado = cliente.consulta_estado_factura(
        codigoAmbiente=codigo_ambiente,
        codigoModalidad=_CODIGO_MODALIDAD_COMPUTARIZADA,
        codigoSistema=codigo_sistema,
        nit=auth.nit,
        cuf=cuf,
    )

    observaciones = []
    for descripcion in (getattr(recepcion, "codigoDescripcion", None), getattr(estado, "codigoDescripcion", None)):
        if descripcion:
            observaciones.append(str(descripcion))

    return EmisionResultado(
        cuf=cuf,
        cufd=cufd.codigoCufd,
        transaccion_recepcion=bool(recepcion.transaccion),
        codigo_recepcion=getattr(recepcion, "codigoRecepcion", None),
        estado_factura=getattr(estado, "codigoEstado", None),
        transaccion_estado=bool(estado.transaccion),
        observaciones=observaciones,
    )
