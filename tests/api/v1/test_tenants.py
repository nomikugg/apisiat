def _crear_tenant(client, nit="123456789", razon_social="Empresa de Prueba SRL"):
    response = client.post(
        "/api/v1/tenants",
        json={"nit": nit, "razon_social": razon_social, "modalidad": "computarizada_en_linea"},
    )
    assert response.status_code == 201
    return response.json()


def test_crear_y_obtener_tenant(client):
    tenant = _crear_tenant(client)
    assert tenant["nit"] == "123456789"
    assert tenant["activo"] is True

    response = client.get(f"/api/v1/tenants/{tenant['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == tenant["id"]


def test_listar_tenants(client):
    _crear_tenant(client, nit="111111111")
    _crear_tenant(client, nit="222222222")

    response = client.get("/api/v1/tenants")
    assert response.status_code == 200
    nits = {t["nit"] for t in response.json()}
    assert {"111111111", "222222222"} <= nits


def test_obtener_tenant_404(client):
    response = client.get("/api/v1/tenants/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_actualizar_tenant(client):
    tenant = _crear_tenant(client, nit="333333333")

    response = client.patch(f"/api/v1/tenants/{tenant['id']}", json={"activo": False})
    assert response.status_code == 200
    assert response.json()["activo"] is False


def test_crear_sucursal_actividad_y_cliente(client):
    tenant = _crear_tenant(client, nit="444444444")
    tenant_id = tenant["id"]

    response = client.post(
        f"/api/v1/tenants/{tenant_id}/sucursales",
        json={"codigo_sucursal": 0, "nombre": "Casa Matriz"},
    )
    assert response.status_code == 201
    sucursal = response.json()
    assert sucursal["tenant_id"] == tenant_id

    response = client.get(f"/api/v1/tenants/{tenant_id}/sucursales")
    assert response.status_code == 200
    assert len(response.json()) == 1

    response = client.post(
        f"/api/v1/tenants/{tenant_id}/actividades-economicas",
        json={"codigo_caeb": "620100", "descripcion": "Programación informática"},
    )
    assert response.status_code == 201

    response = client.post(
        f"/api/v1/tenants/{tenant_id}/clientes",
        json={"nombre_razon_social": "Cliente de Prueba", "numero_documento": "9999999"},
    )
    assert response.status_code == 201
    cliente = response.json()

    response = client.get(f"/api/v1/clientes/{cliente['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == cliente["id"]
