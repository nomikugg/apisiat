import app.services.emision as emision_module
from app.integrations.siat.exceptions import SiatConnectionError
from app.integrations.siat.schemas import EmisionResultado

_FAKE_RESULTADO = EmisionResultado(
    cuf="CUF_FAKE_RETRY_OK",
    cufd="CUFD_FAKE_RETRY",
    transaccion_recepcion=True,
    codigo_recepcion="REC-RETRY-001",
    estado_factura="VALIDA",
    transaccion_estado=True,
    observaciones=[],
)


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
                    "descripcion": "Servicio",
                    "cantidad": "1",
                    "precio_unitario": monto,
                    "subtotal": monto,
                }
            ],
        },
    ).json()


def _emision_payload(**overrides):
    payload = {
        "nit": 123456789,
        "login": "usuario.piloto",
        "password": "clave-piloto",
        "codigo_sistema": "APISIAT01",
        "municipio": "La Paz",
        "usuario": "pperez",
        "leyenda": "Ley N° 453",
        "items": [
            {
                "actividad_economica": "620100",
                "codigo_producto_sin": 49111,
                "codigo_producto": "P01",
                "unidad_medida": 1,
            }
        ],
    }
    payload.update(overrides)
    return payload


def test_siat_error_crea_evento_y_vincula_factura(
    client, monkeypatch, tenant, sucursal, punto_venta, dosificacion, cliente
):
    monkeypatch.setattr(emision_module, "emitir_factura_compra_venta", lambda *a, **kw: (_ for _ in ()).throw(SiatConnectionError("timeout")))

    factura = _crear_factura(client, tenant, sucursal, punto_venta, dosificacion, cliente)
    response = client.post(f"/api/v1/facturas/{factura['id']}/emitir", json=_emision_payload())
    assert response.status_code == 200
    assert response.json()["factura"]["estado"] == "contingencia"

    response = client.get(f"/api/v1/tenants/{tenant['id']}/contingency-events")
    assert response.status_code == 200
    eventos = response.json()
    assert len(eventos) == 1
    assert eventos[0]["resuelto"] is False
    assert "timeout" in eventos[0]["motivo"]

    evento_id = eventos[0]["id"]
    response = client.get(f"/api/v1/contingency-events/{evento_id}")
    assert response.status_code == 200


def test_dos_errores_comparten_un_evento_abierto(
    client, monkeypatch, tenant, sucursal, punto_venta, dosificacion, cliente
):
    """Dos errores consecutivos en el mismo punto de venta → un solo evento."""
    monkeypatch.setattr(emision_module, "emitir_factura_compra_venta", lambda *a, **kw: (_ for _ in ()).throw(SiatConnectionError("no route")))

    f1 = _crear_factura(client, tenant, sucursal, punto_venta, dosificacion, cliente)
    f2 = _crear_factura(client, tenant, sucursal, punto_venta, dosificacion, cliente)
    client.post(f"/api/v1/facturas/{f1['id']}/emitir", json=_emision_payload())
    client.post(f"/api/v1/facturas/{f2['id']}/emitir", json=_emision_payload())

    response = client.get(f"/api/v1/tenants/{tenant['id']}/contingency-events")
    assert len(response.json()) == 1


def test_abrir_evento_manual(client, tenant, punto_venta):
    response = client.post(
        f"/api/v1/tenants/{tenant['id']}/contingency-events",
        json={"punto_venta_id": punto_venta["id"], "motivo": "Mantenimiento programado"},
    )
    assert response.status_code == 201
    evento = response.json()
    assert evento["resuelto"] is False
    assert evento["motivo"] == "Mantenimiento programado"


def test_cerrar_evento(client, tenant, punto_venta):
    response = client.post(
        f"/api/v1/tenants/{tenant['id']}/contingency-events",
        json={"punto_venta_id": punto_venta["id"], "motivo": "Test cerrar"},
    )
    evento_id = response.json()["id"]

    response = client.post(f"/api/v1/contingency-events/{evento_id}/cerrar")
    assert response.status_code == 200
    assert response.json()["resuelto"] is True
    assert response.json()["fin"] is not None

    # Cerrar de nuevo → 409
    response = client.post(f"/api/v1/contingency-events/{evento_id}/cerrar")
    assert response.status_code == 409


def test_reintentar_evento_exito(
    client, monkeypatch, tenant, sucursal, punto_venta, dosificacion, cliente
):
    """Las facturas en CONTINGENCIA pasan a VALIDADA tras reintentar con éxito."""
    # Primer intento falla
    monkeypatch.setattr(
        emision_module,
        "emitir_factura_compra_venta",
        lambda *a, **kw: (_ for _ in ()).throw(SiatConnectionError("down")),
    )
    factura = _crear_factura(client, tenant, sucursal, punto_venta, dosificacion, cliente)
    client.post(f"/api/v1/facturas/{factura['id']}/emitir", json=_emision_payload())

    evento_id = client.get(f"/api/v1/tenants/{tenant['id']}/contingency-events").json()[0]["id"]

    # SIN vuelve a estar disponible
    monkeypatch.setattr(emision_module, "emitir_factura_compra_venta", lambda *a, **kw: _FAKE_RESULTADO)

    response = client.post(
        f"/api/v1/contingency-events/{evento_id}/reintentar",
        json={
            "nit": 123456789,
            "login": "usuario.piloto",
            "password": "clave-piloto",
            "codigo_sistema": "APISIAT01",
        },
    )
    assert response.status_code == 200
    resultado = response.json()
    assert resultado["exitosas"] == 1
    assert resultado["fallidas"] == 0

    # La factura ahora está VALIDADA
    response = client.get(f"/api/v1/facturas/{factura['id']}")
    assert response.json()["estado"] == "validada"


def test_reintentar_evento_falla_nuevamente(
    client, monkeypatch, tenant, sucursal, punto_venta, dosificacion, cliente
):
    monkeypatch.setattr(
        emision_module,
        "emitir_factura_compra_venta",
        lambda *a, **kw: (_ for _ in ()).throw(SiatConnectionError("still down")),
    )
    factura = _crear_factura(client, tenant, sucursal, punto_venta, dosificacion, cliente)
    client.post(f"/api/v1/facturas/{factura['id']}/emitir", json=_emision_payload())

    evento_id = client.get(f"/api/v1/tenants/{tenant['id']}/contingency-events").json()[0]["id"]

    response = client.post(
        f"/api/v1/contingency-events/{evento_id}/reintentar",
        json={
            "nit": 123456789,
            "login": "usuario.piloto",
            "password": "clave-piloto",
            "codigo_sistema": "APISIAT01",
        },
    )
    assert response.status_code == 200
    resultado = response.json()
    assert resultado["exitosas"] == 0
    assert resultado["fallidas"] == 1
    assert "still down" in resultado["errores"][0]

    # La factura sigue en CONTINGENCIA
    assert client.get(f"/api/v1/facturas/{factura['id']}").json()["estado"] == "contingencia"
