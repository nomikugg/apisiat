import datetime
from datetime import datetime as dt
from decimal import Decimal

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from lxml import etree

from app.integrations.siat.schemas import FacturaSiatItem, FacturaSiatPayload
from app.integrations.siat.signing import firmar_xml
from app.integrations.siat.xml_builder import build_factura_compra_venta_xml, validar_contra_xsd


def _payload() -> FacturaSiatPayload:
    return FacturaSiatPayload(
        nit_emisor=1003579028,
        razon_social_emisor="Empresa de Prueba SRL",
        municipio="La Paz",
        telefono="2846005",
        numero_factura=1,
        cuf="44AAEC00DBD34C819B4D7AFD5F91900D3A059E06A467A75AC82F24C74",
        cufd="BQUE+QytqQUDBKVUFOSVRPQkxVRFZNVFVJBMDAwMDAwM",
        codigo_sucursal=0,
        direccion="AV. JORGE LOPEZ #123",
        codigo_punto_venta=0,
        fecha_emision=dt(2026, 1, 15, 10, 30, 0),
        nombre_razon_social="Cliente de Prueba",
        codigo_tipo_documento_identidad=1,
        numero_documento="9999999",
        codigo_cliente="9999999",
        codigo_metodo_pago=1,
        monto_total=Decimal("116.00"),
        monto_total_sujeto_iva=Decimal("116.00"),
        codigo_moneda=1,
        tipo_cambio=Decimal("1.00"),
        monto_total_moneda=Decimal("116.00"),
        leyenda="Ley N° 453: Tienes derecho a recibir información sobre los servicios que utilices.",
        usuario="pperez",
        items=[
            FacturaSiatItem(
                actividad_economica="451010",
                codigo_producto_sin=49111,
                codigo_producto="JN-131231",
                descripcion="Producto A",
                cantidad=Decimal("2"),
                unidad_medida=1,
                precio_unitario=Decimal("50.00"),
                subtotal=Decimal("100.00"),
            ),
        ],
    )


def _generar_certificado_prueba():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    nombre = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "prueba")])
    ahora = dt.now(datetime.timezone.utc)
    certificado = (
        x509.CertificateBuilder()
        .subject_name(nombre)
        .issuer_name(nombre)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(ahora)
        .not_valid_after(ahora + datetime.timedelta(days=1))
        .sign(key, hashes.SHA256())
    )
    return key, certificado


def test_build_factura_compra_venta_xml_is_well_formed():
    xml = build_factura_compra_venta_xml(_payload())
    root = etree.fromstring(xml.encode("utf-8"))
    assert root.tag == "facturaElectronicaCompraVenta"


def test_build_factura_compra_venta_xml_contains_expected_fields():
    xml = build_factura_compra_venta_xml(_payload())
    root = etree.fromstring(xml.encode("utf-8"))

    cabecera = root.find("cabecera")
    assert cabecera.find("nitEmisor").text == "1003579028"
    assert cabecera.find("cuf").text == "44AAEC00DBD34C819B4D7AFD5F91900D3A059E06A467A75AC82F24C74"
    assert cabecera.find("montoTotal").text == "116.00"

    detalles = root.findall("detalle")
    assert len(detalles) == 1
    assert detalles[0].find("descripcion").text == "Producto A"


def test_build_factura_compra_venta_xml_marca_campos_opcionales_ausentes_como_nil():
    xml = build_factura_compra_venta_xml(_payload())
    root = etree.fromstring(xml.encode("utf-8"))

    cabecera = root.find("cabecera")
    complemento = cabecera.find("complemento")
    assert complemento.get("{http://www.w3.org/2001/XMLSchema-instance}nil") == "true"


def test_build_factura_computarizada_compra_venta_xml_valida_contra_xsd_oficial():
    xml = build_factura_compra_venta_xml(_payload(), modalidad="computarizada")
    root = etree.fromstring(xml.encode("utf-8"))
    assert root.tag == "facturaComputarizadaCompraVenta"

    validar_contra_xsd(xml, modalidad="computarizada")


def test_build_factura_electronica_compra_venta_xml_firmada_valida_contra_xsd_oficial():
    key, certificado = _generar_certificado_prueba()
    xml = build_factura_compra_venta_xml(_payload(), modalidad="electronica")
    firmado = firmar_xml(xml, key, certificado)

    validar_contra_xsd(firmado, modalidad="electronica")
