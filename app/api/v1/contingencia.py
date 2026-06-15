import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import requerir_api_key
from app.integrations.siat.exceptions import SiatConnectionError, SiatValidationError
from app.models.facturacion import ContingencyEvent, EstadoFactura, Factura
from app.models.integration import ApiKey
from app.models.tenant import PuntoVenta, Sucursal, Tenant
from app.schemas.contingencia import ContingencyEventCreate, ContingencyEventRead, ReintentoRequest, ReintentoResponse
from app.schemas.factura import EmisionFacturaRequest
from app.services.emision import emitir_factura

router = APIRouter(tags=["contingencia"])


def _get_tenant_or_404(db: Session, tenant_id: uuid.UUID) -> Tenant:
    tenant = db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")
    return tenant


def _get_evento_or_404(db: Session, event_id: uuid.UUID) -> ContingencyEvent:
    evento = db.get(ContingencyEvent, event_id)
    if evento is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evento de contingencia no encontrado")
    return evento


@router.post(
    "/tenants/{tenant_id}/contingency-events",
    response_model=ContingencyEventRead,
    status_code=status.HTTP_201_CREATED,
)
def abrir_evento(
    tenant_id: uuid.UUID,
    payload: ContingencyEventCreate,
    db: Session = Depends(get_db),
    _: ApiKey = Depends(requerir_api_key),
) -> ContingencyEvent:
    """Abre un evento de contingencia manualmente (p. ej. mantenimiento programado)."""
    _get_tenant_or_404(db, tenant_id)
    punto_venta = db.get(PuntoVenta, payload.punto_venta_id)
    if punto_venta is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Punto de venta no encontrado")
    evento = ContingencyEvent(
        tenant_id=tenant_id,
        punto_venta_id=payload.punto_venta_id,
        inicio=datetime.now(timezone.utc),
        motivo=payload.motivo,
    )
    db.add(evento)
    db.commit()
    db.refresh(evento)
    return evento


@router.get("/tenants/{tenant_id}/contingency-events", response_model=list[ContingencyEventRead])
def listar_eventos(
    tenant_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: ApiKey = Depends(requerir_api_key),
) -> list[ContingencyEvent]:
    _get_tenant_or_404(db, tenant_id)
    return list(
        db.query(ContingencyEvent)
        .filter(ContingencyEvent.tenant_id == tenant_id)
        .order_by(ContingencyEvent.inicio.desc())
        .all()
    )


@router.get("/contingency-events/{event_id}", response_model=ContingencyEventRead)
def obtener_evento(
    event_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: ApiKey = Depends(requerir_api_key),
) -> ContingencyEvent:
    return _get_evento_or_404(db, event_id)


@router.post("/contingency-events/{event_id}/cerrar", response_model=ContingencyEventRead)
def cerrar_evento(
    event_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: ApiKey = Depends(requerir_api_key),
) -> ContingencyEvent:
    evento = _get_evento_or_404(db, event_id)
    if evento.resuelto:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="El evento ya está cerrado")
    evento.fin = datetime.now(timezone.utc)
    evento.resuelto = True
    db.commit()
    db.refresh(evento)
    return evento


@router.post("/contingency-events/{event_id}/reintentar", response_model=ReintentoResponse)
def reintentar_evento(
    event_id: uuid.UUID,
    credenciales: ReintentoRequest,
    db: Session = Depends(get_db),
    api_key: ApiKey = Depends(requerir_api_key),
) -> ReintentoResponse:
    """Reintenta emitir ante el SIN todas las facturas en CONTINGENCIA de este evento."""
    _get_evento_or_404(db, event_id)

    facturas = (
        db.query(Factura)
        .filter(
            Factura.contingency_event_id == event_id,
            Factura.estado == EstadoFactura.CONTINGENCIA,
        )
        .all()
    )

    exitosas, fallidas = 0, 0
    errores: list[str] = []

    for factura in facturas:
        if not factura.emision_sin_json:
            fallidas += 1
            errores.append(f"Factura {factura.id}: sin payload almacenado para reintentar")
            continue

        extra_data = {
            **factura.emision_sin_json,
            "nit": credenciales.nit,
            "login": credenciales.login,
            "password": credenciales.password,
            "codigo_sistema": credenciales.codigo_sistema,
            "codigo_ambiente": credenciales.codigo_ambiente,
        }
        try:
            extra = EmisionFacturaRequest(**extra_data)
            tenant = db.get(Tenant, factura.tenant_id)
            sucursal = db.get(Sucursal, factura.sucursal_id)
            punto_venta = db.get(PuntoVenta, factura.punto_venta_id)
            from app.models.facturacion import Cliente  # local para evitar ciclo circular con schemas
            cliente = db.get(Cliente, factura.cliente_id)
            emitir_factura(db, factura, tenant, sucursal, punto_venta, cliente, extra, actor=api_key.nombre)
            exitosas += 1
        except (SiatConnectionError, SiatValidationError) as exc:
            fallidas += 1
            errores.append(f"Factura {factura.id}: {exc}")

    return ReintentoResponse(exitosas=exitosas, fallidas=fallidas, errores=errores)
