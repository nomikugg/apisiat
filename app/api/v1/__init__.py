from fastapi import APIRouter

from app.api.v1.api_keys import router as api_keys_router
from app.api.v1.contingencia import router as contingencia_router
from app.api.v1.facturas import router as facturas_router
from app.api.v1.health import router as health_router
from app.api.v1.puntos_venta import router as puntos_venta_router
from app.api.v1.sucursales import router as sucursales_router
from app.api.v1.tenants import clientes_router, router as tenants_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(tenants_router)
api_router.include_router(clientes_router)
api_router.include_router(sucursales_router)
api_router.include_router(puntos_venta_router)
api_router.include_router(facturas_router)
api_router.include_router(api_keys_router)
api_router.include_router(contingencia_router)
