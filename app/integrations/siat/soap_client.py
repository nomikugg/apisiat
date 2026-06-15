"""
Cliente SOAP para los servicios del SIN (ServicioFacturacion / ServicioCodigos).

Wrapper genérico sobre `zeep.Client`. Las URLs de los WSDL de sandbox/piloto/producción
se leen de `settings.siat_wsdl_facturacion` / `settings.siat_wsdl_codigos`, que aún son
placeholders vacíos (ver docs/04-adapter-siat.md). Los nombres de operación
(`verificarComunicacion`, `cufdEnLinea`, `recepcionFactura`, `consultaCufd`,
`consultaCodigoEstadoFactura`, etc.) corresponden a las operaciones documentadas
públicamente del WSDL `ServicioFacturacion` del SIN.

Cada llamada al SIN debe incluir el Token Delegado del contribuyente en el header HTTP
`apikey: TokenApi <token>` (portal SIN, "Facturación en Línea > Solicitud Token
Delegado"). `_build_transport()` configura ese header en la sesión `requests` usada por
`zeep`.
"""

from typing import Any

from requests import Session
from zeep import Client
from zeep.exceptions import Error as ZeepError
from zeep.transports import Transport

from app.core.config import settings
from app.integrations.siat.exceptions import SiatConnectionError


def _build_transport(token_delegado: str | None) -> Transport:
    session = Session()
    if token_delegado:
        session.headers["apikey"] = f"TokenApi {token_delegado}"
    return Transport(session=session)


class SiatSoapClient:
    """Wrapper sobre `zeep.Client` para el WSDL `ServicioFacturacion` del SIN."""

    def __init__(self, wsdl_url: str | None = None, token_delegado: str | None = None) -> None:
        self._wsdl_url = wsdl_url or settings.siat_wsdl_facturacion
        if not self._wsdl_url:
            raise SiatConnectionError(
                "Falta configurar settings.siat_wsdl_facturacion (URL del WSDL "
                "ServicioFacturacion del SIN). Ver docs/04-adapter-siat.md."
            )
        self._transport = _build_transport(token_delegado)
        self._client: Client | None = None

    @property
    def client(self) -> Client:
        if self._client is None:
            try:
                self._client = Client(self._wsdl_url, transport=self._transport)
            except ZeepError as exc:
                raise SiatConnectionError(f"No se pudo cargar el WSDL {self._wsdl_url}: {exc}") from exc
        return self._client

    def _call(self, operation: str, **kwargs: Any) -> Any:
        try:
            return getattr(self.client.service, operation)(**kwargs)
        except ZeepError as exc:
            raise SiatConnectionError(f"Error llamando a {operation}: {exc}") from exc

    def verificar_comunicacion(self) -> Any:
        """Operación `verificarComunicacion`: chequeo de disponibilidad del servicio."""
        return self._call("verificarComunicacion")

    def obtener_cufd(self, **kwargs: Any) -> Any:
        """Operación `cufdEnLinea`: solicita el CUFD vigente para un punto de venta."""
        return self._call("cufdEnLinea", **kwargs)

    def recepcion_factura(self, **kwargs: Any) -> Any:
        """Operación `recepcionFactura`: envía el XML firmado de una factura individual."""
        return self._call("recepcionFactura", **kwargs)

    def consulta_codigo_estado_factura(self, **kwargs: Any) -> Any:
        """Operación `consultaCodigoEstadoFactura`: consulta el estado de una factura enviada."""
        return self._call("consultaCodigoEstadoFactura", **kwargs)
