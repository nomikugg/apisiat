"""
Clientes SOAP para los servicios del SIN (`ServicioAutenticacion` / `ServicioFacturacion`).

Wrappers genéricos sobre `zeep.Client`. Las URLs de los WSDL de piloto/producción se leen
de `settings.siat_wsdl_autenticacion` / `settings.siat_wsdl_facturacion`, que aún son
placeholders vacíos (ver docs/04-adapter-siat.md y docs/05-fase3-piloto-sin.md).

Flujo de autenticación (anexo técnico "Implementación de Servicios de Facturación",
siatanexo.impuestos.gob.bo): `SiatAuthClient.autenticar(nit, login, password)` llama a la
operación `autenticacion` de `ServicioAutenticacionSoap` con las credenciales de Oficina
Virtual ("SIAT en Línea") del contribuyente y devuelve un token JWT. Ese token se envía en
el header HTTP `Authorization: Token <jwt>` en cada llamada SOAP posterior a
`ServicioFacturacion` — `_build_transport()` configura ese header en la sesión `requests`
usada por `zeep`.

Los nombres de operación de `SiatSoapClient` (`solicitudCuis`, `solicitudCufd`,
`verificarComunicacion`, `RecepcionFactura`, `verificacionEstadoFactura`) corresponden a
los documentados en ese anexo técnico.
"""

from typing import Any

from requests import Session
from zeep import Client
from zeep.exceptions import Error as ZeepError
from zeep.transports import Transport

from app.core.config import settings
from app.integrations.siat.exceptions import SiatConnectionError


def _build_transport(token: str | None) -> Transport:
    session = Session()
    if token:
        session.headers["Authorization"] = f"Token {token}"
    return Transport(session=session)


class SiatAuthClient:
    """Wrapper sobre `zeep.Client` para `ServicioAutenticacionSoap` del SIN."""

    def __init__(self, wsdl_url: str | None = None) -> None:
        self._wsdl_url = wsdl_url or settings.siat_wsdl_autenticacion
        if not self._wsdl_url:
            raise SiatConnectionError(
                "Falta configurar settings.siat_wsdl_autenticacion (URL del WSDL "
                "ServicioAutenticacionSoap del SIN). Ver docs/04-adapter-siat.md."
            )
        self._client: Client | None = None

    @property
    def client(self) -> Client:
        if self._client is None:
            try:
                self._client = Client(self._wsdl_url)
            except ZeepError as exc:
                raise SiatConnectionError(f"No se pudo cargar el WSDL {self._wsdl_url}: {exc}") from exc
        return self._client

    def autenticar(self, *, nit: int, login: str, password: str) -> str:
        """
        Llama a la operación `autenticacion` con un `DatosUsuarioRequest` (nit, login,
        password de la Oficina Virtual del contribuyente) y devuelve el token JWT
        (`UsuarioAutenticacionDto.token`) para usar como `token` de `SiatSoapClient`.
        """
        try:
            resultado = self.client.service.autenticacion(
                DatosUsuarioRequest={
                    "nit": nit,
                    "login": login,
                    "password": password,
                    "client": None,
                    "ip": None,
                    "tipoClienteId": None,
                    "tipoUsuarioId": None,
                }
            )
        except ZeepError as exc:
            raise SiatConnectionError(f"Error llamando a autenticacion: {exc}") from exc
        if not getattr(resultado, "ok", False) or not getattr(resultado, "token", None):
            raise SiatConnectionError(
                f"Autenticación rechazada por el SIN: {getattr(resultado, 'mensajes', resultado)}"
            )
        return resultado.token


class SiatSoapClient:
    """Wrapper sobre `zeep.Client` para el WSDL `ServicioFacturacion` del SIN."""

    def __init__(self, wsdl_url: str | None = None, token: str | None = None) -> None:
        self._wsdl_url = wsdl_url or settings.siat_wsdl_facturacion
        if not self._wsdl_url:
            raise SiatConnectionError(
                "Falta configurar settings.siat_wsdl_facturacion (URL del WSDL "
                "ServicioFacturacion del SIN). Ver docs/04-adapter-siat.md."
            )
        self._transport = _build_transport(token)
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

    def solicitud_cuis(self, **kwargs: Any) -> Any:
        """Operación `solicitudCuis`: obtiene el CUIS (Código Único de Inicio de Sistemas)."""
        return self._call("solicitudCuis", **kwargs)

    def solicitud_cufd(self, **kwargs: Any) -> Any:
        """Operación `solicitudCufd`: obtiene el CUFD vigente (codigoCUFD y codigoControl)."""
        return self._call("solicitudCufd", **kwargs)

    def recepcion_factura(self, **kwargs: Any) -> Any:
        """Operación `RecepcionFactura`: envía el XML firmado de una factura individual."""
        return self._call("RecepcionFactura", **kwargs)

    def consulta_estado_factura(self, **kwargs: Any) -> Any:
        """Operación `verificacionEstadoFactura`: consulta el estado de una factura enviada."""
        return self._call("verificacionEstadoFactura", **kwargs)

    def anulacion_factura(self, **kwargs: Any) -> Any:
        """Operación `AnulacionFactura`: anula una factura ya recibida por el SIN."""
        return self._call("AnulacionFactura", **kwargs)
