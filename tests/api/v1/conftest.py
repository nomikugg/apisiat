import pytest


@pytest.fixture
def tenant(client):
    response = client.post(
        "/api/v1/tenants",
        json={
            "nit": "123456789",
            "razon_social": "Empresa de Prueba SRL",
            "modalidad": "computarizada_en_linea",
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def sucursal(client, tenant):
    response = client.post(
        f"/api/v1/tenants/{tenant['id']}/sucursales",
        json={"codigo_sucursal": 0, "nombre": "Casa Matriz"},
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def punto_venta(client, sucursal):
    response = client.post(
        f"/api/v1/sucursales/{sucursal['id']}/puntos-venta",
        json={"codigo_punto_venta": 0, "nombre": "Punto de Venta Principal"},
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def actividad_economica(client, tenant):
    response = client.post(
        f"/api/v1/tenants/{tenant['id']}/actividades-economicas",
        json={"codigo_caeb": "620100", "descripcion": "Programación informática"},
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def dosificacion(client, punto_venta, actividad_economica):
    response = client.post(
        f"/api/v1/puntos-venta/{punto_venta['id']}/dosificaciones",
        json={
            "actividad_economica_id": actividad_economica["id"],
            "tipo_documento_sector": 1,
            "numero_inicial": 1,
            "numero_final": 100,
            "clave_dosificacion_ref": "secret-ref-test",
            "fecha_limite_emision": "2026-12-31T23:59:59Z",
        },
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def cliente(client, tenant):
    response = client.post(
        f"/api/v1/tenants/{tenant['id']}/clientes",
        json={"nombre_razon_social": "Cliente de Prueba", "numero_documento": "9999999"},
    )
    assert response.status_code == 201
    return response.json()
