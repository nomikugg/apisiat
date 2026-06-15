import uuid

from pydantic import BaseModel, ConfigDict


class ClienteBase(BaseModel):
    nombre_razon_social: str
    numero_documento: str
    complemento: str | None = None


class ClienteCreate(ClienteBase):
    pass


class ClienteRead(ClienteBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
