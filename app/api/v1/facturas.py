import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import requerir_api_key
from app.integrations.siat.exceptions import SiatConnectionError, SiatValidationError
from app.models.facturacion import Cliente, Dosificacion, EstadoFactura, Factura, FacturaItem
from app.models.integration import ApiKey
from app.models.tenant import ModalidadFacturacion, PuntoVenta, Sucursal, Tenant
from app.schemas.factura import EmisionFacturaRequest, EmisionFacturaResponse, FacturaCreate, FacturaRead
from app.services.auditoria import registrar_auditoria
from app.services.contingencia import obtener_o_crear_evento
from app.services.emision import emitir_factura

router = APIRouter(tags=["facturas"])


def _get_tenant_or_404(db: Session, tenant_id: uuid.UUID) -> Tenant:
    tenant = db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")
    return tenant


@router.post("/tenants/{tenant_id}/facturas", response_model=FacturaRead, status_code=status.HTTP_201_CREATED)
def crear_factura(
    tenant_id: uuid.UUID,
    payload: FacturaCreate,
    db: Session = Depends(get_db),
    _: ApiKey = Depends(requerir_api_key),
) -> Factura:
    _get_tenant_or_404(db, tenant_id)

    sucursal = db.get(Sucursal, payload.sucursal_id)
    if sucursal is None or sucursal.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sucursal no encontrada")

    punto_venta = db.get(PuntoVenta, payload.punto_venta_id)
    if punto_venta is None or punto_venta.sucursal_id != payload.sucursal_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Punto de venta no encontrado")

    dosificacion = db.get(Dosificacion, payload.dosificacion_id)
    if dosificacion is None or dosificacion.punto_venta_id != payload.punto_venta_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dosificación no encontrada")

    cliente = db.get(Cliente, payload.cliente_id)
    if cliente is None or cliente.tenant_id != tenant_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")

    if dosificacion.numero_actual > dosificacion.numero_final:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Dosificación agotada")

    factura = Factura(
        tenant_id=tenant_id,
        sucursal_id=payload.sucursal_id,
        punto_venta_id=payload.punto_venta_id,
        dosificacion_id=payload.dosificacion_id,
        cliente_id=payload.cliente_id,
        numero_factura=dosificacion.numero_actual,
        fecha_emision=payload.fecha_emision,
        moneda=payload.moneda,
        monto_total=payload.monto_total,
        tipo_documento_sector=payload.tipo_documento_sector,
        items=[FacturaItem(**item.model_dump()) for item in payload.items],
    )
    dosificacion.numero_actual += 1

    db.add(factura)
    db.commit()
    db.refresh(factura)
    return factura


@router.get("/tenants/{tenant_id}/facturas", response_model=list[FacturaRead])
def listar_facturas(
    tenant_id: uuid.UUID,
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    _: ApiKey = Depends(requerir_api_key),
) -> list[Factura]:
    _get_tenant_or_404(db, tenant_id)
    return list(
        db.query(Factura)
        .filter(Factura.tenant_id == tenant_id)
        .order_by(Factura.created_at)
        .offset(offset)
        .limit(limit)
        .all()
    )


@router.get("/facturas/{factura_id}", response_model=FacturaRead)
def obtener_factura(
    factura_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: ApiKey = Depends(requerir_api_key),
) -> Factura:
    factura = db.get(Factura, factura_id)
    if factura is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Factura no encontrada")
    return factura


@router.post("/facturas/{factura_id}/emitir", response_model=EmisionFacturaResponse)
def emitir_factura_endpoint(
    factura_id: uuid.UUID,
    payload: EmisionFacturaRequest,
    db: Session = Depends(get_db),
    api_key: ApiKey = Depends(requerir_api_key),
) -> EmisionFacturaResponse:
    factura = db.get(Factura, factura_id)
    if factura is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Factura no encontrada")

    if factura.estado != EstadoFactura.PENDIENTE:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="La factura ya fue procesada")

    tenant = db.get(Tenant, factura.tenant_id)
    if tenant.modalidad != ModalidadFacturacion.COMPUTARIZADA_EN_LINEA:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Modalidad de facturación no soportada por el orquestador todavía",
        )

    if len(payload.items) != len(factura.items):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="La cantidad de 'items' no coincide con los ítems de la factura",
        )

    sucursal = db.get(Sucursal, factura.sucursal_id)
    punto_venta = db.get(PuntoVenta, factura.punto_venta_id)
    cliente = db.get(Cliente, factura.cliente_id)

    try:
        resultado = emitir_factura(db, factura, tenant, sucursal, punto_venta, cliente, payload, actor=api_key.nombre)
    except SiatConnectionError as exc:
        estado_anterior = factura.estado.value
        factura.estado = EstadoFactura.CONTINGENCIA
        evento = obtener_o_crear_evento(
            db, tenant_id=factura.tenant_id, punto_venta_id=factura.punto_venta_id, motivo=str(exc)
        )
        db.flush()  # obtiene evento.id antes del commit
        factura.contingency_event_id = evento.id
        factura.emision_sin_json = payload.model_dump(mode="json", exclude={"nit", "login", "password"})
        registrar_auditoria(
            db,
            tenant_id=factura.tenant_id,
            actor=api_key.nombre,
            accion="emision_factura",
            entidad="factura",
            entidad_id=factura.id,
            detalle={
                "estado_anterior": estado_anterior,
                "estado_nuevo": factura.estado.value,
                "error": str(exc),
                "contingency_event_id": str(evento.id),
            },
        )
        db.commit()
        db.refresh(factura)
        return EmisionFacturaResponse(
            factura=factura,
            transaccion_recepcion=False,
            codigo_recepcion=None,
            estado_factura=None,
            observaciones=[str(exc)],
        )
    except SiatValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    db.refresh(factura)
    return EmisionFacturaResponse(
        factura=factura,
        transaccion_recepcion=resultado.transaccion_recepcion,
        codigo_recepcion=resultado.codigo_recepcion,
        estado_factura=resultado.estado_factura,
        observaciones=resultado.observaciones,
    )
