import enum
import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin


class EstadoSuscripcion(str, enum.Enum):
    ACTIVA = "activa"
    SUSPENDIDA = "suspendida"
    CANCELADA = "cancelada"


class Plan(UUIDPKMixin, TimestampMixin, Base):
    """Plan comercial: cuota mensual + tarifa marginal por factura (estilo CUCU)."""

    __tablename__ = "plans"

    nombre: Mapped[str] = mapped_column(String(100), unique=True)
    precio_mensual: Mapped[float] = mapped_column(Numeric(10, 2))
    precio_por_factura: Mapped[float] = mapped_column(Numeric(10, 4))
    facturas_incluidas: Mapped[int] = mapped_column(default=0)

    suscripciones: Mapped[list["Subscription"]] = relationship(back_populates="plan")


class Subscription(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "subscriptions"

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True)
    plan_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("plans.id"))
    estado: Mapped[EstadoSuscripcion] = mapped_column(
        Enum(EstadoSuscripcion, name="estado_suscripcion"), default=EstadoSuscripcion.ACTIVA
    )
    fecha_inicio: Mapped[date] = mapped_column(Date)
    fecha_fin: Mapped[date | None] = mapped_column(Date)

    plan: Mapped["Plan"] = relationship(back_populates="suscripciones")


class UsageRecord(UUIDPKMixin, Base):
    """Registro de uso (1 factura emitida) para el cobro de la tarifa marginal."""

    __tablename__ = "usage_records"

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True)
    factura_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("facturas.id"), unique=True)
    periodo: Mapped[str] = mapped_column(String(7))  # formato YYYY-MM
    monto_cobrado: Mapped[float] = mapped_column(Numeric(10, 4))
    facturado: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
