"""Tests de notas de crédito/débito. Usan monkeypatch para el orquestador SIAT."""

import app.api.v1.notas as notas_module
import app.services.emision as emision_module
from app.integrations.siat.schemas import EmisionResultado

_RESULTADO_FACTURA = EmisionResultado(
    cuf="CUF_FACTURA_BASE",
    cufd="CUFD_FACTURA_BASE",
    transaccion_recepcion=True,
    estado_factura="VALIDA",
    transaccion_estado=True,
)

_RESULTADO_NOTA = EmisionResultado(
    cuf="CUF_NOTA_FAKE_0000",
    cufd="CUFD_NOTA_FAKE",
    transaccion_recepcion=True,
    codigo_recepcion="REC-NOTA-001",
    estado_factura="VALIDA",
    transaccion_estado=True,
    observaciones=[],
)

_NOTA_PAYLOAD = {
    "tipo": "nota_credito",
    "motivo": "Devolución parcial",
    "monto": "50.00",
    "codigo_documento_sector": 2,
}

_EMISION_NOTA_PAYLOAD = {
    "nit": 123456789,
    "login": "usuario.piloto",
    "password": "clave-piloto",
    "codigo_sistema": "APISIAT01",
    "municipio": "La Paz",
    "usuario": "pperez",
    "leyenda": "Ley N° 453",
    "actividad_economica": "620100",
    "codigo_producto_sin": 49111,
    "codigo_producto": "P01",
    "unidad_medida": 1,
}


def _crear_factura_validada(client, monkeypatch, tenant, sucursal, punto_venta, dosificacion, cliente):
    """Crea y emite una factura (monkeypatch en emision_module) para tener una VALIDADA."""
    monkeypatch.setattr(emision_module, "emitir_factura_compra_venta", lambda *a, **kw: _RESULTADO_FACTURA)
    factura = client.post(
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
    ).json()
    emision_payload = {
        "nit": 123456789, "login": "u", "password": "p", "codigo_sistema": "S01",
        "municipio": "LP", "usuario": "u", "leyenda": "L",
        "items": [{"actividad_economica": "620100", "codigo_producto_sin": 49111, "codigo_producto": "P01", "unidad_medida": 1}],
    }
    client.post(f"/api/v1/facturas/{factura['id']}/emitir", json=emision_payload)
    return factura


def test_crear_nota(client, monkeypatch, tenant, sucursal, punto_venta, dosificacion, cliente):
    factura = _crear_factura_validada(client, monkeypatch, tenant, sucursal, punto_venta, dosificacion, cliente)

    response = client.post(f"/api/v1/facturas/{factura['id']}/notas-credito-debito", json=_NOTA_PAYLOAD)
    assert response.status_code == 201
    nota = response.json()
    assert nota["tipo"] == "nota_credito"
    assert nota["estado"] == "pendiente"
    assert nota["cuf"] is None
    assert nota["codigo_documento_sector"] == 2
    assert nota["numero_nota"] >= 1


def test_crear_nota_sobre_factura_pendiente_409(client, tenant, sucursal, punto_venta, dosificacion, cliente):
    factura = client.post(
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
            "items": [{"descripcion": "X", "cantidad": "1", "precio_unitario": "100.00", "subtotal": "100.00"}],
        },
    ).json()
    response = client.post(f"/api/v1/facturas/{factura['id']}/notas-credito-debito", json=_NOTA_PAYLOAD)
    assert response.status_code == 409


def test_emitir_nota_validada(client, monkeypatch, tenant, sucursal, punto_venta, dosificacion, cliente):
    factura = _crear_factura_validada(client, monkeypatch, tenant, sucursal, punto_venta, dosificacion, cliente)
    nota = client.post(f"/api/v1/facturas/{factura['id']}/notas-credito-debito", json=_NOTA_PAYLOAD).json()
    assert nota.get("id"), f"La nota no se creó: {nota}"

    monkeypatch.setattr(notas_module, "emitir_factura_compra_venta", lambda *a, **kw: _RESULTADO_NOTA)

    response = client.post(f"/api/v1/notas/{nota['id']}/emitir", json=_EMISION_NOTA_PAYLOAD)
    assert response.status_code == 200
    resultado = response.json()

    assert resultado["nota"]["estado"] == "validada"
    assert resultado["nota"]["cuf"] == "CUF_NOTA_FAKE_0000"
    assert resultado["nota"]["cufd"] == "CUFD_NOTA_FAKE"
    assert resultado["transaccion_recepcion"] is True
    assert resultado["estado_factura"] == "VALIDA"


def test_emitir_nota_ya_emitida_409(client, monkeypatch, tenant, sucursal, punto_venta, dosificacion, cliente):
    factura = _crear_factura_validada(client, monkeypatch, tenant, sucursal, punto_venta, dosificacion, cliente)
    nota = client.post(f"/api/v1/facturas/{factura['id']}/notas-credito-debito", json=_NOTA_PAYLOAD).json()

    monkeypatch.setattr(notas_module, "emitir_factura_compra_venta", lambda *a, **kw: _RESULTADO_NOTA)
    client.post(f"/api/v1/notas/{nota['id']}/emitir", json=_EMISION_NOTA_PAYLOAD)

    response = client.post(f"/api/v1/notas/{nota['id']}/emitir", json=_EMISION_NOTA_PAYLOAD)
    assert response.status_code == 409


def test_listar_notas(client, monkeypatch, tenant, sucursal, punto_venta, dosificacion, cliente):
    factura = _crear_factura_validada(client, monkeypatch, tenant, sucursal, punto_venta, dosificacion, cliente)

    client.post(f"/api/v1/facturas/{factura['id']}/notas-credito-debito", json=_NOTA_PAYLOAD)
    client.post(
        f"/api/v1/facturas/{factura['id']}/notas-credito-debito",
        json={**_NOTA_PAYLOAD, "tipo": "nota_debito", "monto": "10.00"},
    )

    response = client.get(f"/api/v1/facturas/{factura['id']}/notas-credito-debito")
    assert response.status_code == 200
    notas = response.json()
    assert len(notas) == 2


def test_audit_log_emision_nota(client, monkeypatch, tenant, sucursal, punto_venta, dosificacion, cliente):
    factura = _crear_factura_validada(client, monkeypatch, tenant, sucursal, punto_venta, dosificacion, cliente)
    nota = client.post(f"/api/v1/facturas/{factura['id']}/notas-credito-debito", json=_NOTA_PAYLOAD).json()

    monkeypatch.setattr(notas_module, "emitir_factura_compra_venta", lambda *a, **kw: _RESULTADO_NOTA)
    client.post(f"/api/v1/notas/{nota['id']}/emitir", json=_EMISION_NOTA_PAYLOAD)

    logs = client.get(f"/api/v1/tenants/{tenant['id']}/audit-logs").json()
    nota_logs = [lg for lg in logs if lg["accion"] == "emision_nota"]
    assert len(nota_logs) == 1
    assert nota_logs[0]["entidad"] == "nota_credito_debito"
    assert nota_logs[0]["detalle"]["tipo"] == "nota_credito"
    assert nota_logs[0]["detalle"]["cuf_factura_original"] == "CUF_FACTURA_BASE"
