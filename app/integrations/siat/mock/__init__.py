"""
Mock local de los servicios SOAP del SIN, para desarrollo y pruebas del adapter
(`app/integrations/siat/`) sin depender de credenciales reales de SIAT en Línea.

Ver `server.py` para el detalle y la advertencia de que esto es una simulación.
"""

from app.integrations.siat.mock.server import (
    MOCK_CODIGO_CONTROL,
    MOCK_CUFD,
    MOCK_CUIS,
    MOCK_TOKEN,
    start_mock_server_in_thread,
)

__all__ = [
    "MOCK_CODIGO_CONTROL",
    "MOCK_CUFD",
    "MOCK_CUIS",
    "MOCK_TOKEN",
    "start_mock_server_in_thread",
]
