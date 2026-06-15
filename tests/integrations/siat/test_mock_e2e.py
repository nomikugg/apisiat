"""
Test end-to-end del adapter SIAT contra el mock local (`app/integrations/siat/mock`).

Cubre el flujo completo: autenticación (JWT) -> CUIS -> CUFD -> generar CUF -> construir
XML -> firmar/huella -> RecepcionFactura -> verificacionEstadoFactura.

No usa credenciales ni endpoints reales del SIN (ver mock/server.py).
"""

import gzip
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from app.integrations.siat.cuf import generar_cuf
from app.integrations.siat.mock import (
    MOCK_CODIGO_CONTROL,
    MOCK_CUFD,
    MOCK_CUIS,
    MOCK_TOKEN,
    start_mock_server_in_thread,
)
from app.integrations.siat.schemas import FacturaSiatItem, FacturaSiatPayload
from app.integrations.siat.signing import huella_digital
from app.integrations.siat.soap_client import SiatAuthClient, SiatSoapClient
from app.integrations.siat.xml_builder import build_factura_compra_venta_xml, validar_contra_xsd

_HOST, _PORT = "127.0.0.1", 8089
_BASE_URL = f"http://{_HOST}:{_PORT}"


@pytest.fixture(scope="module")
def mock_sin():
    server = start_mock_server_in_thread(_HOST, _PORT)
    yield
    server.shutdown()


def _autenticar() -> str:
    auth = SiatAuthClient(wsdl_url=f"{_BASE_URL}/autenticacion?wsdl")
    return auth.autenticar(nit=123456789, login="usuario.piloto", password="clave-piloto")


def test_autenticacion_devuelve_token_mock(mock_sin):
    assert _autenticar() == MOCK_TOKEN


def test_flujo_completo_emision_factura_contra_mock(mock_sin):
    token = _autenticar()
    cliente = SiatSoapClient(wsdl_url=f"{_BASE_URL}/facturacion?wsdl", token=token)

    assert cliente.verificar_comunicacion() is True

    cuis = cliente.solicitud_cuis(
        codigoAmbiente=2,
        codigoSistema="APISIAT01",
        nit=123456789,
        codigoModalidad=1,
        codigoSucursal=0,
        codigoPuntoVenta=0,
    )
    assert cuis.codigoCuis == MOCK_CUIS

    cufd = cliente.solicitud_cufd(
        codigoAmbiente=2,
        codigoSistema="APISIAT01",
        nit=123456789,
        codigoModalidad=1,
        codigoSucursal=0,
        codigoPuntoVenta=0,
        cuis=cuis.codigoCuis,
    )
    assert cufd.codigoCufd == MOCK_CUFD
    assert cufd.codigoControl == MOCK_CODIGO_CONTROL

    # El mock devuelve el codigoControl del ejemplo oficial del SIN, así que con los
    # mismos datos de ese ejemplo el CUF generado coincide con él (ver
    # test_cuf_generator.py).
    fecha_emision = datetime(2019, 1, 13, 16, 37, 21, 231_000)
    cuf = generar_cuf(
        nit=123456789,
        fecha_hora_emision=fecha_emision,
        sucursal=0,
        modalidad=1,
        tipo_emision=1,
        tipo_factura_documento_ajuste=1,
        tipo_documento_sector=1,
        numero_factura=1,
        punto_venta=0,
        codigo_control=cufd.codigoControl,
    )
    assert cuf == "8727F63A15F8976591FDDE5B387C5D015A29E06A1A19E23EF34124CD"

    payload = FacturaSiatPayload(
        nit_emisor=123456789,
        razon_social_emisor="Empresa de Prueba SRL",
        municipio="La Paz",
        telefono="2846005",
        numero_factura=1,
        cuf=cuf,
        cufd=cufd.codigoCufd,
        codigo_sucursal=0,
        direccion=cufd.direccion,
        codigo_punto_venta=0,
        fecha_emision=fecha_emision,
        nombre_razon_social="Cliente de Prueba",
        codigo_tipo_documento_identidad=1,
        numero_documento="9999999",
        codigo_cliente="9999999",
        codigo_metodo_pago=1,
        monto_total=Decimal("100.00"),
        monto_total_sujeto_iva=Decimal("100.00"),
        codigo_moneda=1,
        tipo_cambio=Decimal("1.00"),
        monto_total_moneda=Decimal("100.00"),
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

    xml = build_factura_compra_venta_xml(payload, modalidad="computarizada")
    validar_contra_xsd(xml, modalidad="computarizada")

    recepcion = cliente.recepcion_factura(
        codigoAmbiente=2,
        codigoModalidad=2,
        codigoEmision=1,
        codigoDocumentoSector=1,
        codigoSistema="APISIAT01",
        nit=123456789,
        cuis=cuis.codigoCuis,
        cufd=cufd.codigoCufd,
        codigoMetodoEnvio=1,
        archivo=gzip.compress(xml.encode("utf-8")),
        fechaEnvio=datetime.now(timezone.utc),
        hashArchivo=huella_digital(xml),
    )
    assert recepcion.transaccion is True
    assert recepcion.codigoRecepcion == "MOCK-00000001"

    estado = cliente.consulta_estado_factura(
        codigoAmbiente=2,
        codigoModalidad=2,
        codigoSistema="APISIAT01",
        nit=123456789,
        cuf=cuf,
    )
    assert estado.transaccion is True
    assert estado.codigoEstado == "VALIDA"
