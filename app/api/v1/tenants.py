import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.facturacion import Cliente
from app.models.tenant import ActividadEconomica, Sucursal, Tenant
from app.schemas.cliente import ClienteCreate, ClienteRead
from app.schemas.tenant import (
    ActividadEconomicaCreate,
    ActividadEconomicaRead,
    SucursalCreate,
    SucursalRead,
    TenantCreate,
    TenantRead,
    TenantUpdate,
)

router = APIRouter(prefix="/tenants", tags=["tenants"])
clientes_router = APIRouter(tags=["clientes"])


def _get_tenant_or_404(db: Session, tenant_id: uuid.UUID) -> Tenant:
    tenant = db.get(Tenant, tenant_id)
    if tenant is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tenant no encontrado")
    return tenant


@router.post("", response_model=TenantRead, status_code=status.HTTP_201_CREATED)
def crear_tenant(payload: TenantCreate, db: Session = Depends(get_db)) -> Tenant:
    tenant = Tenant(**payload.model_dump())
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


@router.get("", response_model=list[TenantRead])
def listar_tenants(limit: int = 50, offset: int = 0, db: Session = Depends(get_db)) -> list[Tenant]:
    return list(db.query(Tenant).order_by(Tenant.created_at).offset(offset).limit(limit).all())


@router.get("/{tenant_id}", response_model=TenantRead)
def obtener_tenant(tenant_id: uuid.UUID, db: Session = Depends(get_db)) -> Tenant:
    return _get_tenant_or_404(db, tenant_id)


@router.patch("/{tenant_id}", response_model=TenantRead)
def actualizar_tenant(tenant_id: uuid.UUID, payload: TenantUpdate, db: Session = Depends(get_db)) -> Tenant:
    tenant = _get_tenant_or_404(db, tenant_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(tenant, field, value)
    db.commit()
    db.refresh(tenant)
    return tenant


@router.post("/{tenant_id}/sucursales", response_model=SucursalRead, status_code=status.HTTP_201_CREATED)
def crear_sucursal(tenant_id: uuid.UUID, payload: SucursalCreate, db: Session = Depends(get_db)) -> Sucursal:
    _get_tenant_or_404(db, tenant_id)
    sucursal = Sucursal(tenant_id=tenant_id, **payload.model_dump())
    db.add(sucursal)
    db.commit()
    db.refresh(sucursal)
    return sucursal


@router.get("/{tenant_id}/sucursales", response_model=list[SucursalRead])
def listar_sucursales(tenant_id: uuid.UUID, db: Session = Depends(get_db)) -> list[Sucursal]:
    _get_tenant_or_404(db, tenant_id)
    return list(db.query(Sucursal).filter(Sucursal.tenant_id == tenant_id).all())


@router.post(
    "/{tenant_id}/actividades-economicas",
    response_model=ActividadEconomicaRead,
    status_code=status.HTTP_201_CREATED,
)
def crear_actividad_economica(
    tenant_id: uuid.UUID, payload: ActividadEconomicaCreate, db: Session = Depends(get_db)
) -> ActividadEconomica:
    _get_tenant_or_404(db, tenant_id)
    actividad = ActividadEconomica(tenant_id=tenant_id, **payload.model_dump())
    db.add(actividad)
    db.commit()
    db.refresh(actividad)
    return actividad


@router.get("/{tenant_id}/actividades-economicas", response_model=list[ActividadEconomicaRead])
def listar_actividades_economicas(tenant_id: uuid.UUID, db: Session = Depends(get_db)) -> list[ActividadEconomica]:
    _get_tenant_or_404(db, tenant_id)
    return list(db.query(ActividadEconomica).filter(ActividadEconomica.tenant_id == tenant_id).all())


@router.post("/{tenant_id}/clientes", response_model=ClienteRead, status_code=status.HTTP_201_CREATED)
def crear_cliente(tenant_id: uuid.UUID, payload: ClienteCreate, db: Session = Depends(get_db)) -> Cliente:
    _get_tenant_or_404(db, tenant_id)
    cliente = Cliente(tenant_id=tenant_id, **payload.model_dump())
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente


@router.get("/{tenant_id}/clientes", response_model=list[ClienteRead])
def listar_clientes(tenant_id: uuid.UUID, db: Session = Depends(get_db)) -> list[Cliente]:
    _get_tenant_or_404(db, tenant_id)
    return list(db.query(Cliente).filter(Cliente.tenant_id == tenant_id).all())


@clientes_router.get("/clientes/{cliente_id}", response_model=ClienteRead)
def obtener_cliente(cliente_id: uuid.UUID, db: Session = Depends(get_db)) -> Cliente:
    cliente = db.get(Cliente, cliente_id)
    if cliente is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente no encontrado")
    return cliente
