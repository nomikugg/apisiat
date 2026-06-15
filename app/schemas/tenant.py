import uuid

from pydantic import BaseModel, ConfigDict

from app.models.tenant import ModalidadFacturacion


class TenantBase(BaseModel):
    nit: str
    razon_social: str
    modalidad: ModalidadFacturacion


class TenantCreate(TenantBase):
    pass


class TenantUpdate(BaseModel):
    razon_social: str | None = None
    activo: bool | None = None


class TenantRead(TenantBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    activo: bool


class SucursalBase(BaseModel):
    codigo_sucursal: int
    nombre: str
    direccion: str | None = None


class SucursalCreate(SucursalBase):
    pass


class SucursalRead(SucursalBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID


class PuntoVentaBase(BaseModel):
    codigo_punto_venta: int
    nombre: str


class PuntoVentaCreate(PuntoVentaBase):
    pass


class PuntoVentaRead(PuntoVentaBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    sucursal_id: uuid.UUID


class ActividadEconomicaBase(BaseModel):
    codigo_caeb: str
    descripcion: str


class ActividadEconomicaCreate(ActividadEconomicaBase):
    pass


class ActividadEconomicaRead(ActividadEconomicaBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
