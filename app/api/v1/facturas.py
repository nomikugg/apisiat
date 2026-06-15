import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.facturacion import Cliente, Dosificacion, Factura, FacturaItem
from app.models.tenant import PuntoVenta, Sucursal, Tenant
from app.schemas.factura import FacturaCreate, FacturaRead

router = APIRouter(tags=["facturas"])


def _get_tenant_or_404(db: Session, tenant_id: uuid.UUID) -> Tenant:
    tenant = db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")
    return tenant


@router.post("/tenants/{tenant_id}/facturas", response_model=FacturaRead, status_code=status.HTTP_201_CREATED)
def crear_factura(tenant_id: uuid.UUID, payload: FacturaCreate, db: Session = Depends(get_db)) -> Factura:
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
    tenant_id: uuid.UUID, limit: int = 50, offset: int = 0, db: Session = Depends(get_db)
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
def obtener_factura(factura_id: uuid.UUID, db: Session = Depends(get_db)) -> Factura:
    factura = db.get(Factura, factura_id)
    if factura is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Factura no encontrada")
    return factura
