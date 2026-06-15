"""Registro de auditoría (`audit_logs`): trazabilidad de interacciones con el SIN y
cambios de estado de facturas, exigida por la normativa SIN (ver docs/01)."""

import uuid

from sqlalchemy.orm import Session

from app.models.integration import AuditLog


def registrar_auditoria(
    db: Session,
    *,
    tenant_id: uuid.UUID | None,
    actor: str,
    accion: str,
    entidad: str,
    entidad_id: uuid.UUID | str,
    detalle: dict | None = None,
) -> AuditLog:
    """Agrega un `AuditLog` a la sesión. No hace commit: el llamador decide cuándo."""
    registro = AuditLog(
        tenant_id=tenant_id,
        actor=actor,
        accion=accion,
        entidad=entidad,
        entidad_id=str(entidad_id),
        detalle=detalle,
    )
    db.add(registro)
    return registro
