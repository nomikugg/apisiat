from datetime import datetime
from decimal import Decimal

from lxml import etree

from app.integrations.siat.schemas import FacturaSiatItem, FacturaSiatPayload
from app.integrations.siat.xml_builder import build_factura_compra_venta_xml


def _payload() -> FacturaSiatPayload:
    return FacturaSiatPayload(
        nit_emisor=123456789,
        razon_social_emisor="Empresa de Prueba SRL",
        municipio="La Paz",
        numero_factura=1,
        cuf="6A-DC-53-05-14",
        cufd="AA-BB-CC-DD-EE",
        fecha_emision=datetime(2026, 1, 15, 10, 30, 0),
        codigo_sucursal=0,
        codigo_punto_venta=0,
        tipo_documento_sector=1,
        cliente_nombre_razon_social="Cliente de Prueba",
        cliente_numero_documento="9999999",
        monto_total=Decimal("116.00"),
        items=[
            FacturaSiatItem(
                descripcion="Producto A",
                cantidad=Decimal("2"),
                precio_unitario=Decimal("50.00"),
                subtotal=Decimal("100.00"),
            ),
        ],
    )


def test_build_factura_compra_venta_xml_is_well_formed():
    xml = build_factura_compra_venta_xml(_payload())
    root = etree.fromstring(xml.encode("utf-8"))
    assert root.tag == "facturaElectronicaCompraVenta"


def test_build_factura_compra_venta_xml_contains_expected_fields():
    xml = build_factura_compra_venta_xml(_payload())
    root = etree.fromstring(xml.encode("utf-8"))

    cabecera = root.find("cabecera")
    assert cabecera.find("nitEmisor").text == "123456789"
    assert cabecera.find("cuf").text == "6A-DC-53-05-14"
    assert cabecera.find("montoTotal").text == "116.00"

    items = root.findall("detalle/item")
    assert len(items) == 1
    assert items[0].find("descripcion").text == "Producto A"
