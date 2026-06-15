"""
Servicio de emisión de facturas ante el SIN: mapea una `Factura` (BD) + datos extra del
SIN a un `FacturaSiatPayload` y ejecuta el orquestador de `app.integrations.siat`.

Ver `app/integrations/siat/orchestrator.py` para el flujo SOAP en sí y
`app/schemas/factura.py::EmisionFacturaRequest` para los campos del SIN que aún no se
persisten en nuestro esquema (brecha documentada en el plan de esta tarea).
"""

from sqlalchemy.orm import Session

from app.integrations.siat.orchestrator import emitir_factura_compra_venta
from app.integrations.siat.schemas import AutenticacionSolicitud, EmisionResultado, FacturaSiatItem, FacturaSiatPayload
from app.models.facturacion import Cliente, EstadoFactura, Factura
from app.models.tenant import PuntoVenta, Sucursal, Tenant
from app.schemas.factura import EmisionFacturaRequest
from app.services.auditoria import registrar_auditoria

_PLACEHOLDER = "PENDIENTE"


def construir_payload_siat(
    factura: Factura,
    tenant: Tenant,
    sucursal: Sucursal,
    punto_venta: PuntoVenta,
    cliente: Cliente,
    extra: EmisionFacturaRequest,
) -> FacturaSiatPayload:
    """
    Mapeo puro (sin acceso a BD) de `factura` + datos relacionados + `extra` a
    `FacturaSiatPayload`. `cuf`, `cufd` y `direccion` son placeholders que
    `emitir_factura_compra_venta` sobreescribe con los valores de CUFD/CUF.
    """
    return FacturaSiatPayload(
        nit_emisor=int(tenant.nit),
        razon_social_emisor=tenant.razon_social,
        municipio=extra.municipio,
        telefono=extra.telefono,
        numero_factura=factura.numero_factura,
        cuf=_PLACEHOLDER,
        cufd=_PLACEHOLDER,
        codigo_sucursal=sucursal.codigo_sucursal,
        direccion=_PLACEHOLDER,
        codigo_punto_venta=punto_venta.codigo_punto_venta,
        fecha_emision=factura.fecha_emision,
        nombre_razon_social=cliente.nombre_razon_social,
        codigo_tipo_documento_identidad=extra.codigo_tipo_documento_identidad,
        numero_documento=cliente.numero_documento,
        complemento=cliente.complemento,
        codigo_cliente=cliente.numero_documento,
        codigo_metodo_pago=extra.codigo_metodo_pago,
        monto_total=factura.monto_total,
        monto_total_sujeto_iva=factura.monto_total,
        codigo_moneda=extra.codigo_moneda,
        tipo_cambio=extra.tipo_cambio,
        monto_total_moneda=factura.monto_total,
        leyenda=extra.leyenda,
        usuario=extra.usuario,
        codigo_documento_sector=factura.tipo_documento_sector,
        items=[
            FacturaSiatItem(
                actividad_economica=item_extra.actividad_economica,
                codigo_producto_sin=item_extra.codigo_producto_sin,
                codigo_producto=item_extra.codigo_producto,
                descripcion=item.descripcion,
                cantidad=item.cantidad,
                unidad_medida=item_extra.unidad_medida,
                precio_unitario=item.precio_unitario,
                monto_descuento=item_extra.monto_descuento,
                subtotal=item.subtotal,
            )
            for item, item_extra in zip(factura.items, extra.items, strict=True)
        ],
    )


def emitir_factura(
    db: Session,
    factura: Factura,
    tenant: Tenant,
    sucursal: Sucursal,
    punto_venta: PuntoVenta,
    cliente: Cliente,
    extra: EmisionFacturaRequest,
    *,
    actor: str,
) -> EmisionResultado:
    """
    Construye el payload, ejecuta el orquestador SIAT y actualiza `estado`/`cuf`/`cufd`
    de `factura`. Si el SIN no responde (`SiatConnectionError`), la excepción se propaga
    sin modificar `factura` — el llamador decide cómo reflejar la contingencia.
    """
    payload = construir_payload_siat(factura, tenant, sucursal, punto_venta, cliente, extra)

    resultado = emitir_factura_compra_venta(
        payload,
        auth=AutenticacionSolicitud(nit=extra.nit, login=extra.login, password=extra.password),
        codigo_sistema=extra.codigo_sistema,
        codigo_ambiente=extra.codigo_ambiente,
        codigo_sucursal=sucursal.codigo_sucursal,
        codigo_punto_venta=punto_venta.codigo_punto_venta,
    )

    estado_anterior = factura.estado.value
    factura.cuf = resultado.cuf
    factura.cufd = resultado.cufd
    if resultado.transaccion_recepcion and resultado.estado_factura == "VALIDA":
        factura.estado = EstadoFactura.VALIDADA
    else:
        factura.estado = EstadoFactura.RECHAZADA

    registrar_auditoria(
        db,
        tenant_id=factura.tenant_id,
        actor=actor,
        accion="emision_factura",
        entidad="factura",
        entidad_id=factura.id,
        detalle={
            "estado_anterior": estado_anterior,
            "estado_nuevo": factura.estado.value,
            "cuf": resultado.cuf,
            "cufd": resultado.cufd,
            "codigo_recepcion": resultado.codigo_recepcion,
            "estado_factura_sin": resultado.estado_factura,
            "transaccion_recepcion": resultado.transaccion_recepcion,
            "observaciones": resultado.observaciones,
        },
    )

    db.commit()
    return resultado
