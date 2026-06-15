import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Enum, ForeignKey, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin


class TipoDocumentoFiscal(str, enum.Enum):
    FACTURA = "factura"
    NOTA_CREDITO = "nota_credito"
    NOTA_DEBITO = "nota_debito"


class EstadoFactura(str, enum.Enum):
    PENDIENTE = "pendiente"
    VALIDADA = "validada"
    CONTINGENCIA = "contingencia"
    RECHAZADA = "rechazada"
    ANULADA = "anulada"


class Dosificacion(UUIDPKMixin, TimestampMixin, Base):
    """Rango de numeración autorizado por el SIN para un punto de venta + actividad."""

    __tablename__ = "dosificaciones"

    punto_venta_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("puntos_venta.id"), index=True)
    actividad_economica_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("actividades_economicas.id")
    )
    tipo_documento_sector: Mapped[int]
    numero_inicial: Mapped[int]
    numero_final: Mapped[int]
    numero_actual: Mapped[int]
    # Clave de dosificación: secreto usado por el algoritmo del Código de Control (CUF).
    # El valor real vive en Vault/KMS; aquí solo una referencia.
    clave_dosificacion_ref: Mapped[str] = mapped_column(String(255))
    fecha_limite_emision: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class CUFDCache(UUIDPKMixin, TimestampMixin, Base):
    """Código Único de Facturación Diaria, vigencia de 24h por punto de venta."""

    __tablename__ = "cufd_cache"

    punto_venta_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("puntos_venta.id"), index=True)
    codigo: Mapped[str] = mapped_column(String(100))
    vigente_desde: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    vigente_hasta: Mapped[datetime] = mapped_column(DateTime(timezone=True))


class Cliente(UUIDPKMixin, TimestampMixin, Base):
    """Cliente/comprador de una factura (NIT o CI)."""

    __tablename__ = "clientes"

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True)
    nombre_razon_social: Mapped[str] = mapped_column(String(255))
    numero_documento: Mapped[str] = mapped_column(String(20))
    complemento: Mapped[str | None] = mapped_column(String(10))


class Factura(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "facturas"

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True)
    sucursal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sucursales.id"))
    punto_venta_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("puntos_venta.id"))
    dosificacion_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("dosificaciones.id"))
    cliente_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("clientes.id"))

    numero_factura: Mapped[int]
    cuf: Mapped[str | None] = mapped_column(String(100), unique=True, index=True)
    cufd: Mapped[str | None] = mapped_column(String(100))
    fecha_emision: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    moneda: Mapped[str] = mapped_column(String(3), default="BOB")
    monto_total: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    tipo_documento_sector: Mapped[int]
    estado: Mapped[EstadoFactura] = mapped_column(Enum(EstadoFactura, name="estado_factura"), default=EstadoFactura.PENDIENTE)
    xml_path: Mapped[str | None] = mapped_column(String(500))
    pdf_path: Mapped[str | None] = mapped_column(String(500))
    contingency_event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("contingency_events.id"), index=True
    )
    emision_sin_json: Mapped[dict | None] = mapped_column(JSONB)

    items: Mapped[list["FacturaItem"]] = relationship(back_populates="factura")


class FacturaItem(UUIDPKMixin, Base):
    __tablename__ = "factura_items"

    factura_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("facturas.id"), index=True)
    descripcion: Mapped[str] = mapped_column(String(500))
    cantidad: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    precio_unitario: Mapped[Decimal] = mapped_column(Numeric(18, 4))
    subtotal: Mapped[Decimal] = mapped_column(Numeric(18, 2))

    factura: Mapped["Factura"] = relationship(back_populates="items")


class NotaCreditoDebito(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "notas_credito_debito"

    factura_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("facturas.id"), index=True)
    tipo: Mapped[TipoDocumentoFiscal] = mapped_column(Enum(TipoDocumentoFiscal, name="tipo_documento_fiscal"))
    motivo: Mapped[str] = mapped_column(String(500))
    monto: Mapped[Decimal] = mapped_column(Numeric(18, 2))
    cuf: Mapped[str | None] = mapped_column(String(100), unique=True, index=True)
    estado: Mapped[EstadoFactura] = mapped_column(Enum(EstadoFactura, name="estado_nota"), default=EstadoFactura.PENDIENTE)


class ContingencyEvent(UUIDPKMixin, TimestampMixin, Base):
    """Ventana en la que SIAT no respondió y las facturas se emitieron offline."""

    __tablename__ = "contingency_events"

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True)
    punto_venta_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("puntos_venta.id"))
    inicio: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    fin: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    motivo: Mapped[str] = mapped_column(String(500))
    resuelto: Mapped[bool] = mapped_column(default=False)
