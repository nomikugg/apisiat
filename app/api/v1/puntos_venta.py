import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.facturacion import Dosificacion
from app.models.tenant import PuntoVenta
from app.schemas.factura import DosificacionCreate, DosificacionRead
from app.schemas.tenant import PuntoVentaRead

router = APIRouter(prefix="/puntos-venta", tags=["puntos-venta"])


def _get_punto_venta_or_404(db: Session, punto_venta_id: uuid.UUID) -> PuntoVenta:
    punto_venta = db.get(PuntoVenta, punto_venta_id)
    if punto_venta is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Punto de venta no encontrado")
    return punto_venta


@router.get("/{punto_venta_id}", response_model=PuntoVentaRead)
def obtener_punto_venta(punto_venta_id: uuid.UUID, db: Session = Depends(get_db)) -> PuntoVenta:
    return _get_punto_venta_or_404(db, punto_venta_id)


@router.post(
    "/{punto_venta_id}/dosificaciones",
    response_model=DosificacionRead,
    status_code=status.HTTP_201_CREATED,
)
def crear_dosificacion(
    punto_venta_id: uuid.UUID, payload: DosificacionCreate, db: Session = Depends(get_db)
) -> Dosificacion:
    _get_punto_venta_or_404(db, punto_venta_id)
    dosificacion = Dosificacion(
        punto_venta_id=punto_venta_id,
        numero_actual=payload.numero_inicial,
        **payload.model_dump(),
    )
    db.add(dosificacion)
    db.commit()
    db.refresh(dosificacion)
    return dosificacion


@router.get("/{punto_venta_id}/dosificaciones", response_model=list[DosificacionRead])
def listar_dosificaciones(punto_venta_id: uuid.UUID, db: Session = Depends(get_db)) -> list[Dosificacion]:
    _get_punto_venta_or_404(db, punto_venta_id)
    return list(db.query(Dosificacion).filter(Dosificacion.punto_venta_id == punto_venta_id).all())
