def test_obtener_punto_venta(client, punto_venta):
    response = client.get(f"/api/v1/puntos-venta/{punto_venta['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == punto_venta["id"]


def test_punto_venta_404(client):
    response = client.get("/api/v1/puntos-venta/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_crear_y_listar_dosificaciones(client, dosificacion, punto_venta):
    assert dosificacion["numero_actual"] == dosificacion["numero_inicial"] == 1
    assert dosificacion["punto_venta_id"] == punto_venta["id"]

    response = client.get(f"/api/v1/puntos-venta/{punto_venta['id']}/dosificaciones")
    assert response.status_code == 200
    assert len(response.json()) == 1
