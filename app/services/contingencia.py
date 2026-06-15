"""Gestión de eventos de contingencia (ventanas sin conectividad con el SIN)."""

import uuid
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.models.facturacion import ContingencyEvent


def obtener_o_crear_evento(
    db: Session,
    *,
    tenant_id: uuid.UUID,
    punto_venta_id: uuid.UUID,
    motivo: str,
) -> ContingencyEvent:
    """Retorna el evento abierto para este tenant+punto_venta, o crea uno nuevo.

    No hace commit; el llamador lo incluye en su transacción.
    """
    evento = (
        db.query(ContingencyEvent)
        .filter(
            ContingencyEvent.tenant_id == tenant_id,
            ContingencyEvent.punto_venta_id == punto_venta_id,
            ContingencyEvent.resuelto.is_(False),
        )
        .first()
    )
    if evento is None:
        evento = ContingencyEvent(
            tenant_id=tenant_id,
            punto_venta_id=punto_venta_id,
            inicio=datetime.now(timezone.utc),
            motivo=motivo,
        )
        db.add(evento)
    return evento
