"""
Generador de XML para el documento "Factura Compra Venta" (tipo de documento sector
más común), modalidades Electrónica y Computarizada.

La estructura de `<cabecera>`/`<detalle>` (nombres de campos, orden, restricciones de
tipo/longitud) sigue el XSD oficial del SIN, descargado de
siatinfo.impuestos.gob.bo ("Facturación en Línea > Archivos XML / XSD de Facturas
Electrónicas > Factura de Compra y Venta") y guardado en
`app/integrations/siat/xsd/facturas/`:

- `facturaElectronicaCompraVenta.xsd` (modalidad Electrónica, requiere `<Signature>`
  XML-DSig como último hijo de la raíz — ver `signing.firmar_xml`).
- `facturaComputarizadaCompraVenta.xsd` (modalidad Computarizada, sin `<Signature>`;
  usa "huella digital" — ver `signing.huella_digital`).

Ambos XSD comparten exactamente los mismos campos de `<cabecera>` y `<detalle>`; solo
difiere el nombre del elemento raíz y la presencia de `<Signature>`.
"""

from pathlib import Path

from lxml import etree

from app.integrations.siat.redondeo import redondear_monto
from app.integrations.siat.schemas import FacturaSiatItem, FacturaSiatPayload

_XSI_NS = "http://www.w3.org/2001/XMLSchema-instance"
_XSI_NIL = f"{{{_XSI_NS}}}nil"

_XSD_DIR = Path(__file__).parent / "xsd" / "facturas"

_ROOT_TAGS = {
    "electronica": "facturaElectronicaCompraVenta",
    "computarizada": "facturaComputarizadaCompraVenta",
}

_XSD_FILES = {
    "electronica": "facturaElectronicaCompraVenta.xsd",
    "computarizada": "facturaComputarizadaCompraVenta.xsd",
}


def _set_text(parent: etree._Element, tag: str, value: object) -> None:
    etree.SubElement(parent, tag).text = str(value)


def _set_nillable(parent: etree._Element, tag: str, value: object | None) -> None:
    elemento = etree.SubElement(parent, tag)
    if value is None:
        elemento.set(_XSI_NIL, "true")
    else:
        elemento.text = str(value)


def _redondear_opcional(valor):
    return None if valor is None else redondear_monto(valor)


def _build_cabecera(root: etree._Element, payload: FacturaSiatPayload) -> None:
    cabecera = etree.SubElement(root, "cabecera")
    _set_text(cabecera, "nitEmisor", payload.nit_emisor)
    _set_text(cabecera, "razonSocialEmisor", payload.razon_social_emisor)
    _set_text(cabecera, "municipio", payload.municipio)
    _set_nillable(cabecera, "telefono", payload.telefono)
    _set_text(cabecera, "numeroFactura", payload.numero_factura)
    _set_text(cabecera, "cuf", payload.cuf)
    _set_text(cabecera, "cufd", payload.cufd)
    _set_text(cabecera, "codigoSucursal", payload.codigo_sucursal)
    _set_text(cabecera, "direccion", payload.direccion)
    _set_nillable(cabecera, "codigoPuntoVenta", payload.codigo_punto_venta)
    _set_text(cabecera, "fechaEmision", payload.fecha_emision.isoformat())
    _set_nillable(cabecera, "nombreRazonSocial", payload.nombre_razon_social)
    _set_text(cabecera, "codigoTipoDocumentoIdentidad", payload.codigo_tipo_documento_identidad)
    _set_text(cabecera, "numeroDocumento", payload.numero_documento)
    _set_nillable(cabecera, "complemento", payload.complemento)
    _set_text(cabecera, "codigoCliente", payload.codigo_cliente)
    _set_text(cabecera, "codigoMetodoPago", payload.codigo_metodo_pago)
    _set_nillable(cabecera, "numeroTarjeta", payload.numero_tarjeta)
    _set_text(cabecera, "montoTotal", redondear_monto(payload.monto_total))
    _set_text(cabecera, "montoTotalSujetoIva", redondear_monto(payload.monto_total_sujeto_iva))
    _set_text(cabecera, "codigoMoneda", payload.codigo_moneda)
    _set_text(cabecera, "tipoCambio", redondear_monto(payload.tipo_cambio))
    _set_text(cabecera, "montoTotalMoneda", redondear_monto(payload.monto_total_moneda))
    _set_nillable(cabecera, "montoGiftCard", _redondear_opcional(payload.monto_gift_card))
    _set_nillable(cabecera, "descuentoAdicional", _redondear_opcional(payload.descuento_adicional))
    _set_nillable(cabecera, "codigoExcepcion", payload.codigo_excepcion)
    _set_nillable(cabecera, "cafc", payload.cafc)
    _set_text(cabecera, "leyenda", payload.leyenda)
    _set_text(cabecera, "usuario", payload.usuario)
    _set_text(cabecera, "codigoDocumentoSector", payload.codigo_documento_sector)


def _build_detalle(root: etree._Element, item: FacturaSiatItem) -> None:
    detalle = etree.SubElement(root, "detalle")
    _set_text(detalle, "actividadEconomica", item.actividad_economica)
    _set_text(detalle, "codigoProductoSin", item.codigo_producto_sin)
    _set_text(detalle, "codigoProducto", item.codigo_producto)
    _set_text(detalle, "descripcion", item.descripcion)
    _set_text(detalle, "cantidad", redondear_monto(item.cantidad))
    _set_text(detalle, "unidadMedida", item.unidad_medida)
    _set_text(detalle, "precioUnitario", redondear_monto(item.precio_unitario))
    _set_nillable(detalle, "montoDescuento", _redondear_opcional(item.monto_descuento))
    _set_text(detalle, "subTotal", redondear_monto(item.subtotal))
    _set_nillable(detalle, "numeroSerie", item.numero_serie)
    _set_nillable(detalle, "numeroImei", item.numero_imei)


def build_factura_compra_venta_xml(payload: FacturaSiatPayload, modalidad: str = "electronica") -> str:
    """
    Construye el XML de una "Factura Compra Venta" a partir de `payload`.

    `modalidad` es `"electronica"` (raíz `facturaElectronicaCompraVenta`, requiere
    firmar el resultado con `signing.firmar_xml`) o `"computarizada"` (raíz
    `facturaComputarizadaCompraVenta`, sin `<Signature>`).
    """
    if modalidad not in _ROOT_TAGS:
        raise ValueError(f"modalidad desconocida: {modalidad!r}")

    root = etree.Element(_ROOT_TAGS[modalidad], nsmap={"xsi": _XSI_NS})
    _build_cabecera(root, payload)
    for item in payload.items:
        _build_detalle(root, item)

    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", pretty_print=True).decode("utf-8")


def validar_contra_xsd(xml: str, modalidad: str = "electronica") -> None:
    """
    Valida `xml` contra el XSD oficial del SIN para "Factura Compra Venta".

    Levanta `lxml.etree.DocumentInvalid` si `xml` no cumple el XSD. Para la modalidad
    "electronica", `xml` debe incluir el `<Signature>` (ver `signing.firmar_xml`), que
    el XSD exige como último elemento.
    """
    if modalidad not in _XSD_FILES:
        raise ValueError(f"modalidad desconocida: {modalidad!r}")

    schema = etree.XMLSchema(etree.parse(str(_XSD_DIR / _XSD_FILES[modalidad])))
    schema.assertValid(etree.fromstring(xml.encode("utf-8")))
