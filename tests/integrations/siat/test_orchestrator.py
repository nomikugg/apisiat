"""Test del orquestador (`app.integrations.siat.orchestrator`) contra el mock local."""

from datetime import datetime
from decimal import Decimal

import pytest

from app.integrations.siat.cuf import generar_cuf
from app.integrations.siat.mock import MOCK_CODIGO_CONTROL, MOCK_CUFD, start_mock_server_in_thread
from app.integrations.siat.orchestrator import emitir_factura_compra_venta
from app.integrations.siat.schemas import AutenticacionSolicitud, FacturaSiatItem, FacturaSiatPayload

# El WSDL del mock hardcodea `soap:address location="http://127.0.0.1:8089/..."`
# (ver app/integrations/siat/mock/wsdl/*.wsdl), así que el mock debe servirse en este
# puerto. pytest corre los módulos de test secuencialmente, por lo que no hay conflicto
# con el fixture `mock_sin` de `test_mock_e2e.py` (cada uno arranca/detiene su servidor).
_HOST, _PORT = "127.0.0.1", 8089
_BASE_URL = f"http://{_HOST}:{_PORT}"


@pytest.fixture(scope="module")
def mock_sin():
    server = start_mock_server_in_thread(_HOST, _PORT)
    yield
    server.shutdown()


def test_emitir_factura_compra_venta_contra_mock(mock_sin):
    fecha_emision = datetime(2019, 1, 13, 16, 37, 21, 231_000)

    payload = FacturaSiatPayload(
        nit_emisor=123456789,
        razon_social_emisor="Empresa de Prueba SRL",
        municipio="La Paz",
        telefono="2846005",
        numero_factura=1,
        cuf="PENDIENTE",
        cufd="PENDIENTE",
        codigo_sucursal=0,
        direccion="PENDIENTE",
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

    resultado = emitir_factura_compra_venta(
        payload,
        auth=AutenticacionSolicitud(nit=123456789, login="usuario.piloto", password="clave-piloto"),
        codigo_sistema="APISIAT01",
        codigo_ambiente=2,
        codigo_sucursal=0,
        codigo_punto_venta=0,
        wsdl_autenticacion=f"{_BASE_URL}/autenticacion?wsdl",
        wsdl_facturacion=f"{_BASE_URL}/facturacion?wsdl",
    )

    cuf_esperado = generar_cuf(
        nit=123456789,
        fecha_hora_emision=fecha_emision,
        sucursal=0,
        modalidad=2,  # computarizada: orchestrator solo soporta esta modalidad
        tipo_emision=1,
        tipo_factura_documento_ajuste=1,
        tipo_documento_sector=1,
        numero_factura=1,
        punto_venta=0,
        codigo_control=MOCK_CODIGO_CONTROL,
    )

    assert resultado.cuf == cuf_esperado
    assert resultado.cufd == MOCK_CUFD
    assert resultado.transaccion_recepcion is True
    assert resultado.codigo_recepcion == "MOCK-00000001"
    assert resultado.estado_factura == "VALIDA"
    assert resultado.transaccion_estado is True

    assert payload.cuf == resultado.cuf
    assert payload.cufd == MOCK_CUFD
    assert payload.direccion == "Av. Mock 123 (mock)"
