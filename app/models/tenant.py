import enum
import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.mixins import TimestampMixin, UUIDPKMixin


class ModalidadFacturacion(str, enum.Enum):
    ELECTRONICA_EN_LINEA = "electronica_en_linea"
    COMPUTARIZADA_EN_LINEA = "computarizada_en_linea"
    PORTAL_WEB = "portal_web"


class TipoCredencial(str, enum.Enum):
    TOKEN_PROPIO = "token_propio"
    TOKEN_DELEGADO = "token_delegado"
    CERTIFICADO_DIGITAL = "certificado_digital"


class Tenant(UUIDPKMixin, TimestampMixin, Base):
    """Empresa cliente de la plataforma (el contribuyente que emite facturas)."""

    __tablename__ = "tenants"

    nit: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    razon_social: Mapped[str] = mapped_column(String(255))
    modalidad: Mapped[ModalidadFacturacion] = mapped_column(Enum(ModalidadFacturacion, name="modalidad_facturacion"))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

    sucursales: Mapped[list["Sucursal"]] = relationship(back_populates="tenant")
    actividades_economicas: Mapped[list["ActividadEconomica"]] = relationship(back_populates="tenant")
    credenciales: Mapped[list["Credential"]] = relationship(back_populates="tenant")


class Sucursal(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "sucursales"

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True)
    codigo_sucursal: Mapped[int]
    nombre: Mapped[str] = mapped_column(String(255))
    direccion: Mapped[str | None] = mapped_column(String(500))

    tenant: Mapped["Tenant"] = relationship(back_populates="sucursales")
    puntos_venta: Mapped[list["PuntoVenta"]] = relationship(back_populates="sucursal")


class PuntoVenta(UUIDPKMixin, TimestampMixin, Base):
    __tablename__ = "puntos_venta"

    sucursal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("sucursales.id"), index=True)
    codigo_punto_venta: Mapped[int]
    nombre: Mapped[str] = mapped_column(String(255))

    sucursal: Mapped["Sucursal"] = relationship(back_populates="puntos_venta")


class ActividadEconomica(UUIDPKMixin, TimestampMixin, Base):
    """Actividad económica (CAEB) registrada en el Padrón del tenant."""

    __tablename__ = "actividades_economicas"

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True)
    codigo_caeb: Mapped[str] = mapped_column(String(10))
    descripcion: Mapped[str] = mapped_column(String(255))

    tenant: Mapped["Tenant"] = relationship(back_populates="actividades_economicas")


class Credential(UUIDPKMixin, TimestampMixin, Base):
    """Referencia a credenciales sensibles (token delegado / certificado).

    El valor real (token, PKCS#12) vive en Vault/KMS; aquí solo se guarda
    una referencia/secret-ref y metadatos de vigencia.
    """

    __tablename__ = "credentials"

    tenant_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("tenants.id"), index=True)
    tipo: Mapped[TipoCredencial] = mapped_column(Enum(TipoCredencial, name="tipo_credencial"))
    secret_ref: Mapped[str] = mapped_column(String(255))
    vigente_desde: Mapped[str | None] = mapped_column(String(20))
    vigente_hasta: Mapped[str | None] = mapped_column(String(20))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)

    tenant: Mapped["Tenant"] = relationship(back_populates="credenciales")
