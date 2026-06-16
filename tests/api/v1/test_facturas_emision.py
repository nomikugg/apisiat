import pytest

import app.services.emision as emision_module
from app.core.config import settings
from app.integrations.siat.exceptions import SiatConnectionError
from app.integrations.siat.mock import MOCK_CUFD, start_mock_server_in_thread

_HOST, _PORT = "127.0.0.1", 8089
_BASE_URL = f"http://{_HOST}:{_PORT}"


@pytest.fixture(scope="module")
def mock_sin():
    server = start_mock_server_in_thread(_HOST, _PORT)
    yield
    server.shutdown()


@pytest.fixture
def siat_mock_settings(mock_sin, monkeypatch):
    monkeypatch.setattr(settings, "siat_wsdl_autenticacion", f"{_BASE_URL}/autenticacion?wsdl")
    monkeypatch.setattr(settings, "siat_wsdl_facturacion", f"{_BASE_URL}/facturacion?wsdl")


def _crear_factura(client, tenant, sucursal, punto_venta, dosificacion, cliente, monto="100.00"):
    return client.post(
        f"/api/v1/tenants/{tenant['id']}/facturas",
        json={
            "sucursal_id": sucursal["id"],
            "punto_venta_id": punto_venta["id"],
            "dosificacion_id": dosificacion["id"],
            "cliente_id": cliente["id"],
            "fecha_emision": "2026-06-15T10:00:00Z",
            "moneda": "BOB",
            "monto_total": monto,
            "tipo_documento_sector": 1,
            "items": [
                {
                    "descripcion": "Servicio de prueba",
                    "cantidad": "1",
                    "precio_unitario": monto,
                    "subtotal": monto,
                }
            ],
        },
    )


def _emision_payload(**overrides):
    payload = {
        "nit": 123456789,
        "login": "usuario.piloto",
        "password": "clave-piloto",
        "codigo_sistema": "APISIAT01",
        "municipio": "La Paz",
        "usuario": "pperez",
        "leyenda": "Ley N° 453: Tienes derecho a recibir información sobre los servicios que utilices.",
        "items": [
            {
                "actividad_economica": "620100",
                "codigo_producto_sin": 49111,
                "codigo_producto": "JN-131231",
                "unidad_medida": 1,
            }
        ],
    }
    payload.update(overrides)
    return payload


def test_emitir_factura_validada(
    client, siat_mock_settings, tenant, sucursal, punto_venta, dosificacion, cliente
):
    response = _crear_factura(client, tenant, sucursal, punto_venta, dosificacion, cliente)
    factura = response.json()

    response = client.post(f"/api/v1/facturas/{factura['id']}/emitir", json=_emision_payload())
    assert response.status_code == 200
    resultado = response.json()

    assert resultado["factura"]["estado"] == "validada"
    assert resultado["factura"]["cuf"]
    assert resultado["factura"]["cufd"] == MOCK_CUFD
    assert resultado["transaccion_recepcion"] is True
    assert resultado["estado_factura"] == "VALIDA"

    response = client.get(f"/api/v1/tenants/{tenant['id']}/audit-logs")
    assert response.status_code == 200
    logs = response.json()
    assert len(logs) == 1
    assert logs[0]["accion"] == "emision_factura"
    assert logs[0]["entidad"] == "factura"
    assert logs[0]["entidad_id"] == factura["id"]
    assert logs[0]["detalle"]["estado_anterior"] == "pendiente"
    assert logs[0]["detalle"]["estado_nuevo"] == "validada"
    assert logs[0]["detalle"]["cuf"] == resultado["factura"]["cuf"]


def test_emitir_factura_ya_emitida_409(
    client, siat_mock_settings, tenant, sucursal, punto_venta, dosificacion, cliente
):
    response = _crear_factura(client, tenant, sucursal, punto_venta, dosificacion, cliente)
    factura = response.json()

    response = client.post(f"/api/v1/facturas/{factura['id']}/emitir", json=_emision_payload())
    assert response.status_code == 200

    response = client.post(f"/api/v1/facturas/{factura['id']}/emitir", json=_emision_payload())
    assert response.status_code == 409


def test_emitir_factura_404(client, siat_mock_settings):
    response = client.post(
        "/api/v1/facturas/00000000-0000-0000-0000-000000000000/emitir", json=_emision_payload()
    )
    assert response.status_code == 404


def _anulacion_payload(**overrides):
    payload = {
        "nit": 123456789,
        "login": "usuario.piloto",
        "password": "clave-piloto",
        "codigo_sistema": "APISIAT01",
    }
    payload.update(overrides)
    return payload


def test_anular_factura_validada(
    client, siat_mock_settings, tenant, sucursal, punto_venta, dosificacion, cliente
):
    factura = _crear_factura(client, tenant, sucursal, punto_venta, dosificacion, cliente).json()
    client.post(f"/api/v1/facturas/{factura['id']}/emitir", json=_emision_payload())

    response = client.post(f"/api/v1/facturas/{factura['id']}/anular", json=_anulacion_payload())
    assert response.status_code == 200
    assert response.json()["estado"] == "anulada"

    logs = client.get(f"/api/v1/tenants/{tenant['id']}/audit-logs").json()
    anulacion_logs = [lg for lg in logs if lg["accion"] == "anulacion_factura"]
    assert len(anulacion_logs) == 1
    assert anulacion_logs[0]["detalle"]["estado_anterior"] == "validada"
    assert anulacion_logs[0]["detalle"]["codigo_estado_sin"] == "ANULADA"


def test_anular_factura_pendiente_409(
    client, siat_mock_settings, tenant, sucursal, punto_venta, dosificacion, cliente
):
    factura = _crear_factura(client, tenant, sucursal, punto_venta, dosificacion, cliente).json()
    response = client.post(f"/api/v1/facturas/{factura['id']}/anular", json=_anulacion_payload())
    assert response.status_code == 409


def test_anular_factura_dos_veces_409(
    client, siat_mock_settings, tenant, sucursal, punto_venta, dosificacion, cliente
):
    factura = _crear_factura(client, tenant, sucursal, punto_venta, dosificacion, cliente).json()
    client.post(f"/api/v1/facturas/{factura['id']}/emitir", json=_emision_payload())
    client.post(f"/api/v1/facturas/{factura['id']}/anular", json=_anulacion_payload())

    response = client.post(f"/api/v1/facturas/{factura['id']}/anular", json=_anulacion_payload())
    assert response.status_code == 409


def test_emitir_factura_contingencia(
    client, siat_mock_settings, monkeypatch, tenant, sucursal, punto_venta, dosificacion, cliente
):
    def _falla_conexion(*args, **kwargs):
        raise SiatConnectionError("El SIN no respondió")

    monkeypatch.setattr(emision_module, "emitir_factura_compra_venta", _falla_conexion)

    response = _crear_factura(client, tenant, sucursal, punto_venta, dosificacion, cliente)
    factura = response.json()

    response = client.post(f"/api/v1/facturas/{factura['id']}/emitir", json=_emision_payload())
    assert response.status_code == 200
    resultado = response.json()

    assert resultado["factura"]["estado"] == "contingencia"
    assert resultado["transaccion_recepcion"] is False
    assert resultado["observaciones"] == ["El SIN no respondió"]

    response = client.get(f"/api/v1/tenants/{tenant['id']}/audit-logs")
    assert response.status_code == 200
    logs = response.json()
    assert len(logs) == 1
    assert logs[0]["accion"] == "emision_factura"
    assert logs[0]["entidad_id"] == factura["id"]
    assert logs[0]["detalle"]["estado_anterior"] == "pendiente"
    assert logs[0]["detalle"]["estado_nuevo"] == "contingencia"
    assert logs[0]["detalle"]["error"] == "El SIN no respondió"
