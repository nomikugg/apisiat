"""
Generador de XML para el documento "Factura Compra Venta" (tipo de documento sector
más común, modalidad Electrónica/Computarizada en línea).

La estructura de elementos (cabecera/detalle, nombres de campos) está basada en el
conocimiento general de los esquemas SFE del SIN documentados en docs/01 y docs/02
(NIT emisor, municipio, CUF/CUFD, datos del cliente, items con cantidad/precio/subtotal,
montos totales). NO está validada contra el XSD oficial del SIN — eso es un pendiente
documentado en docs/04-adapter-siat.md.
"""

from lxml import etree

from app.integrations.siat.redondeo import redondear_monto
from app.integrations.siat.schemas import FacturaSiatPayload


def build_factura_compra_venta_xml(payload: FacturaSiatPayload) -> str:
    """Construye el XML de una Factura Compra Venta a partir de `payload`."""
    root = etree.Element("facturaElectronicaCompraVenta")

    cabecera = etree.SubElement(root, "cabecera")
    etree.SubElement(cabecera, "nitEmisor").text = str(payload.nit_emisor)
    etree.SubElement(cabecera, "razonSocialEmisor").text = payload.razon_social_emisor
    etree.SubElement(cabecera, "municipio").text = payload.municipio
    etree.SubElement(cabecera, "codigoSucursal").text = str(payload.codigo_sucursal)
    etree.SubElement(cabecera, "codigoPuntoVenta").text = str(payload.codigo_punto_venta)
    etree.SubElement(cabecera, "numeroFactura").text = str(payload.numero_factura)
    etree.SubElement(cabecera, "cuf").text = payload.cuf
    etree.SubElement(cabecera, "cufd").text = payload.cufd
    etree.SubElement(cabecera, "fechaEmision").text = payload.fecha_emision.isoformat()
    etree.SubElement(cabecera, "codigoDocumentoSector").text = str(payload.tipo_documento_sector)
    etree.SubElement(cabecera, "nombreRazonSocialCliente").text = payload.cliente_nombre_razon_social
    etree.SubElement(cabecera, "numeroDocumentoCliente").text = payload.cliente_numero_documento
    if payload.cliente_complemento:
        etree.SubElement(cabecera, "complementoCliente").text = payload.cliente_complemento
    etree.SubElement(cabecera, "codigoMoneda").text = payload.moneda
    etree.SubElement(cabecera, "montoTotal").text = str(redondear_monto(payload.monto_total))

    detalle = etree.SubElement(root, "detalle")
    for item in payload.items:
        item_el = etree.SubElement(detalle, "item")
        etree.SubElement(item_el, "descripcion").text = item.descripcion
        etree.SubElement(item_el, "cantidad").text = str(item.cantidad)
        etree.SubElement(item_el, "precioUnitario").text = str(redondear_monto(item.precio_unitario))
        etree.SubElement(item_el, "subTotal").text = str(redondear_monto(item.subtotal))

    return etree.tostring(root, xml_declaration=True, encoding="UTF-8", pretty_print=True).decode("utf-8")
