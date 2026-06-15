import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.tenant import PuntoVenta, Sucursal
from app.schemas.tenant import PuntoVentaCreate, PuntoVentaRead, SucursalRead

router = APIRouter(prefix="/sucursales", tags=["sucursales"])


def _get_sucursal_or_404(db: Session, sucursal_id: uuid.UUID) -> Sucursal:
    sucursal = db.get(Sucursal, sucursal_id)
    if sucursal is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sucursal no encontrada")
    return sucursal


@router.get("/{sucursal_id}", response_model=SucursalRead)
def obtener_sucursal(sucursal_id: uuid.UUID, db: Session = Depends(get_db)) -> Sucursal:
    return _get_sucursal_or_404(db, sucursal_id)


@router.post("/{sucursal_id}/puntos-venta", response_model=PuntoVentaRead, status_code=status.HTTP_201_CREATED)
def crear_punto_venta(
    sucursal_id: uuid.UUID, payload: PuntoVentaCreate, db: Session = Depends(get_db)
) -> PuntoVenta:
    _get_sucursal_or_404(db, sucursal_id)
    punto_venta = PuntoVenta(sucursal_id=sucursal_id, **payload.model_dump())
    db.add(punto_venta)
    db.commit()
    db.refresh(punto_venta)
    return punto_venta


@router.get("/{sucursal_id}/puntos-venta", response_model=list[PuntoVentaRead])
def listar_puntos_venta(sucursal_id: uuid.UUID, db: Session = Depends(get_db)) -> list[PuntoVenta]:
    _get_sucursal_or_404(db, sucursal_id)
    return list(db.query(PuntoVenta).filter(PuntoVenta.sucursal_id == sucursal_id).all())
