def test_obtener_sucursal(client, sucursal):
    response = client.get(f"/api/v1/sucursales/{sucursal['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == sucursal["id"]


def test_sucursal_404(client):
    response = client.get("/api/v1/sucursales/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_crear_y_listar_puntos_venta(client, sucursal):
    response = client.post(
        f"/api/v1/sucursales/{sucursal['id']}/puntos-venta",
        json={"codigo_punto_venta": 0, "nombre": "Punto de Venta Principal"},
    )
    assert response.status_code == 201
    punto_venta = response.json()
    assert punto_venta["sucursal_id"] == sucursal["id"]

    response = client.get(f"/api/v1/sucursales/{sucursal['id']}/puntos-venta")
    assert response.status_code == 200
    assert len(response.json()) == 1
