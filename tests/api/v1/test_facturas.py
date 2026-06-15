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


def test_crear_factura_asigna_numero_y_descuenta_dosificacion(
    client, tenant, sucursal, punto_venta, dosificacion, cliente
):
    response = _crear_factura(client, tenant, sucursal, punto_venta, dosificacion, cliente)
    assert response.status_code == 201
    factura = response.json()
    assert factura["numero_factura"] == dosificacion["numero_actual"]
    assert factura["estado"] == "pendiente"
    assert factura["cuf"] is None
    assert factura["cufd"] is None
    assert len(factura["items"]) == 1

    response = _crear_factura(client, tenant, sucursal, punto_venta, dosificacion, cliente)
    assert response.status_code == 201
    factura2 = response.json()
    assert factura2["numero_factura"] == factura["numero_factura"] + 1


def test_obtener_y_listar_facturas(client, tenant, sucursal, punto_venta, dosificacion, cliente):
    response = _crear_factura(client, tenant, sucursal, punto_venta, dosificacion, cliente)
    factura = response.json()

    response = client.get(f"/api/v1/facturas/{factura['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == factura["id"]

    response = client.get(f"/api/v1/tenants/{tenant['id']}/facturas")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_factura_404(client):
    response = client.get("/api/v1/facturas/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_crear_factura_con_dosificacion_agotada(
    client, tenant, sucursal, punto_venta, cliente, actividad_economica
):
    response = client.post(
        f"/api/v1/puntos-venta/{punto_venta['id']}/dosificaciones",
        json={
            "actividad_economica_id": actividad_economica["id"],
            "tipo_documento_sector": 1,
            "numero_inicial": 1,
            "numero_final": 1,
            "clave_dosificacion_ref": "secret-ref-test",
            "fecha_limite_emision": "2026-12-31T23:59:59Z",
        },
    )
    assert response.status_code == 201
    dosificacion_agotable = response.json()

    response = _crear_factura(client, tenant, sucursal, punto_venta, dosificacion_agotable, cliente)
    assert response.status_code == 201

    response = _crear_factura(client, tenant, sucursal, punto_venta, dosificacion_agotable, cliente)
    assert response.status_code == 409
