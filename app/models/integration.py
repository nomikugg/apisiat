import uuid
from datetime import datetime

from sqlalchemy import ARRAY, Boolean, DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin


class WebhookEndpoint(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "webhook_endpoints"

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True)
    url: Mapped[str] = mapped_column(String(500))
    eventos: Mapped[list[str]] = mapped_column(ARRAY(String))
    secret: Mapped[str] = mapped_column(String(100))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)


class AuditLog(UUIDPKMixin, Base):
    """Log inmutable de interacciones con el SIN y acciones sensibles."""

    __tablename__ = "audit_logs"

    tenant_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True)
    actor: Mapped[str] = mapped_column(String(255))
    accion: Mapped[str] = mapped_column(String(100))
    entidad: Mapped[str] = mapped_column(String(100))
    entidad_id: Mapped[str | None] = mapped_column(String(100))
    detalle: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
