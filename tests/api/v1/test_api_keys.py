"""Tests de autenticación por API keys. Usan `unauthed_client` que NO hace override de
`requerir_api_key`, para verificar el flujo real de autenticación."""

from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.main import app


@pytest.fixture
def unauthed_client(db_session: Session) -> Generator[TestClient, None, None]:
    """Cliente sin override de auth: valida API keys reales."""

    def _override_get_db() -> Generator[Session, None, None]:
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app, raise_server_exceptions=True) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_db, None)


def _crear_tenant(client: TestClient) -> dict:
    response = client.post(
        "/api/v1/tenants",
        json={"nit": "987654321", "razon_social": "Empresa Auth SRL", "modalidad": "computarizada_en_linea"},
    )
    assert response.status_code == 201
    return response.json()


def test_endpoint_sin_api_key_retorna_422(unauthed_client):
    """Header X-API-Key ausente → 422 (campo requerido faltante)."""
    response = unauthed_client.get("/api/v1/tenants")
    assert response.status_code == 200  # tenants list no requiere auth

    # facturas sí requiere auth
    response = unauthed_client.get("/api/v1/tenants/00000000-0000-0000-0000-000000000001/facturas")
    assert response.status_code == 422


def test_endpoint_con_api_key_invalida_retorna_401(unauthed_client):
    tenant = _crear_tenant(unauthed_client)
    response = unauthed_client.get(
        f"/api/v1/tenants/{tenant['id']}/facturas",
        headers={"X-API-Key": "sk_invalida_123456789"},
    )
    assert response.status_code == 401
    assert "inválida" in response.json()["detail"]


def test_crear_y_usar_api_key(unauthed_client):
    tenant = _crear_tenant(unauthed_client)

    # Crear API key (no requiere auth → bootstrap)
    response = unauthed_client.post(
        f"/api/v1/tenants/{tenant['id']}/api-keys",
        json={"nombre": "key-erp"},
    )
    assert response.status_code == 201
    creada = response.json()
    assert creada["nombre"] == "key-erp"
    assert creada["prefijo"].startswith("sk_")
    assert "clave" in creada
    clave_raw = creada["clave"]

    # Usar la clave para acceder a un endpoint protegido
    response = unauthed_client.get(
        f"/api/v1/tenants/{tenant['id']}/facturas",
        headers={"X-API-Key": clave_raw},
    )
    assert response.status_code == 200


def test_listar_api_keys(unauthed_client):
    tenant = _crear_tenant(unauthed_client)
    unauthed_client.post(f"/api/v1/tenants/{tenant['id']}/api-keys", json={"nombre": "key-a"})
    unauthed_client.post(f"/api/v1/tenants/{tenant['id']}/api-keys", json={"nombre": "key-b"})

    response = unauthed_client.get(f"/api/v1/tenants/{tenant['id']}/api-keys")
    assert response.status_code == 200
    keys = response.json()
    assert len(keys) == 2
    assert all(k["activa"] for k in keys)
    assert "clave_hash" not in keys[0]  # nunca expuesto


def test_desactivar_api_key(unauthed_client):
    tenant = _crear_tenant(unauthed_client)

    response = unauthed_client.post(f"/api/v1/tenants/{tenant['id']}/api-keys", json={"nombre": "key-temp"})
    creada = response.json()
    clave_raw = creada["clave"]

    # Desactivar
    response = unauthed_client.delete(f"/api/v1/api-keys/{creada['id']}")
    assert response.status_code == 204

    # La clave ya no sirve
    response = unauthed_client.get(
        f"/api/v1/tenants/{tenant['id']}/facturas",
        headers={"X-API-Key": clave_raw},
    )
    assert response.status_code == 401


def test_actor_en_audit_log_usa_nombre_api_key(unauthed_client, monkeypatch):
    """El campo `actor` del AuditLog refleja el nombre de la API key que hizo la llamada."""
    import app.services.emision as emision_module
    from app.integrations.siat.schemas import EmisionResultado

    _fake_resultado = EmisionResultado(
        cuf="CUF_FAKE_0000000000",
        cufd="CUFD_FAKE_0000",
        transaccion_recepcion=True,
        codigo_recepcion="REC-001",
        estado_factura="VALIDA",
        transaccion_estado=True,
        observaciones=[],
    )
    monkeypatch.setattr(emision_module, "emitir_factura_compra_venta", lambda *a, **kw: _fake_resultado)

    tenant = _crear_tenant(unauthed_client)

    response = unauthed_client.post(f"/api/v1/tenants/{tenant['id']}/api-keys", json={"nombre": "sistema-erp"})
    clave_raw = response.json()["clave"]
    headers = {"X-API-Key": clave_raw}

    sucursal = unauthed_client.post(
        f"/api/v1/tenants/{tenant['id']}/sucursales",
        json={"codigo_sucursal": 0, "nombre": "Casa Matriz"},
    ).json()
    punto_venta = unauthed_client.post(
        f"/api/v1/sucursales/{sucursal['id']}/puntos-venta",
        json={"codigo_punto_venta": 0, "nombre": "PV1"},
    ).json()
    actividad = unauthed_client.post(
        f"/api/v1/tenants/{tenant['id']}/actividades-economicas",
        json={"codigo_caeb": "620100", "descripcion": "TI"},
    ).json()
    dosificacion = unauthed_client.post(
        f"/api/v1/puntos-venta/{punto_venta['id']}/dosificaciones",
        json={
            "actividad_economica_id": actividad["id"],
            "tipo_documento_sector": 1,
            "numero_inicial": 1,
            "numero_final": 100,
            "clave_dosificacion_ref": "ref",
            "fecha_limite_emision": "2026-12-31T23:59:59Z",
        },
    ).json()
    cliente = unauthed_client.post(
        f"/api/v1/tenants/{tenant['id']}/clientes",
        json={"nombre_razon_social": "Cliente", "numero_documento": "1234567"},
    ).json()

    factura = unauthed_client.post(
        f"/api/v1/tenants/{tenant['id']}/facturas",
        json={
            "sucursal_id": sucursal["id"],
            "punto_venta_id": punto_venta["id"],
            "dosificacion_id": dosificacion["id"],
            "cliente_id": cliente["id"],
            "fecha_emision": "2026-06-15T10:00:00Z",
            "moneda": "BOB",
            "monto_total": "100.00",
            "tipo_documento_sector": 1,
            "items": [{"descripcion": "Srv", "cantidad": "1", "precio_unitario": "100.00", "subtotal": "100.00"}],
        },
        headers=headers,
    ).json()

    emision_payload = {
        "nit": 123456789,
        "login": "usuario.piloto",
        "password": "clave-piloto",
        "codigo_sistema": "APISIAT01",
        "municipio": "La Paz",
        "usuario": "pperez",
        "leyenda": "Ley N° 453",
        "items": [{"actividad_economica": "620100", "codigo_producto_sin": 49111, "codigo_producto": "P01", "unidad_medida": 1}],
    }
    response = unauthed_client.post(
        f"/api/v1/facturas/{factura['id']}/emitir", json=emision_payload, headers=headers
    )
    assert response.status_code == 200

    response = unauthed_client.get(f"/api/v1/tenants/{tenant['id']}/audit-logs", headers=headers)
    logs = response.json()
    assert len(logs) == 1
    assert logs[0]["actor"] == "sistema-erp"
