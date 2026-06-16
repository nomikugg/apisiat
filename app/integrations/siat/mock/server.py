"""
Servidor SOAP mock del SIN, para desarrollo y pruebas locales del adapter
(`app/integrations/siat/`) sin depender de credenciales reales de SIAT en Línea.

ADVERTENCIA: esto es una SIMULACIÓN local. No es el servicio real del SIN — las URLs,
tokens, CUIS/CUFD y demás respuestas son datos fijos ("canned"), pensados solo para
validar el flujo del adapter (autenticación -> CUIS -> CUFD -> generar CUF -> construir
XML -> firmar -> RecepcionFactura -> verificacionEstadoFactura). La estructura
(operaciones y nombres de campos) está basada en el anexo técnico "Implementación de
Servicios de Facturación" de siatanexo.impuestos.gob.bo, pero nunca debe usarse para nada
relacionado con el SIN real.

Operaciones soportadas:
  - `ServicioAutenticacionSoap`: `autenticacion`
  - `ServicioFacturacion`: `verificarComunicacion`, `solicitudCuis`, `solicitudCufd`,
    `RecepcionFactura`, `verificacionEstadoFactura`

Uso:
    python -m app.integrations.siat.mock.server
    # sirve los WSDL en:
    #   http://127.0.0.1:8089/autenticacion?wsdl
    #   http://127.0.0.1:8089/facturacion?wsdl
"""

from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

from lxml import etree

_WSDL_DIR = Path(__file__).parent / "wsdl"

_SOAP_NS = "http://schemas.xmlsoap.org/soap/envelope/"
_AUTH_NS = "urn:siat:mock:autenticacion"
_FACT_NS = "urn:siat:mock:facturacion"

# Código de control del ejemplo oficial del SIN ("Facturación en Línea > Algoritmos
# Utilizados > Generación CUF"). Se reutiliza aquí para que un flujo end-to-end contra
# este mock pueda reproducir exactamente ese ejemplo (ver test_cuf_generator.py).
MOCK_CODIGO_CONTROL = "A19E23EF34124CD"

MOCK_TOKEN = "mock.jwt.token"  # nosec - token falso, solo para el mock local
MOCK_CUIS = "ABCD1234EFGH5678"
MOCK_CUFD = "MOCKCUFD1234567890"


def _local_tag(element: etree._Element) -> str:
    return etree.QName(element.tag).localname


def _soap_response(ns: str, operation: str, body_xml: str) -> bytes:
    envelope = (
        '<?xml version="1.0" encoding="UTF-8"?>'
        f'<soapenv:Envelope xmlns:soapenv="{_SOAP_NS}" xmlns:tns="{ns}">'
        "<soapenv:Body>"
        f"<tns:{operation}Response>{body_xml}</tns:{operation}Response>"
        "</soapenv:Body></soapenv:Envelope>"
    )
    return envelope.encode("utf-8")


def _handle_autenticacion(request: etree._Element) -> bytes:
    return _soap_response(
        _AUTH_NS,
        "autenticacion",
        f"<return><ok>true</ok><token>{MOCK_TOKEN}</token></return>",
    )


def _handle_verificar_comunicacion(request: etree._Element) -> bytes:
    return _soap_response(_FACT_NS, "verificarComunicacion", "<return>true</return>")


def _handle_solicitud_cuis(request: etree._Element) -> bytes:
    vigencia = (datetime.now(timezone.utc) + timedelta(days=365)).strftime("%Y-%m-%dT%H:%M:%S")
    return _soap_response(
        _FACT_NS,
        "solicitudCuis",
        (
            "<return>"
            f"<codigoCuis>{MOCK_CUIS}</codigoCuis>"
            f"<fechaVigencia>{vigencia}</fechaVigencia>"
            "<transaccion>true</transaccion>"
            "<codigosRespuesta>"
            "<codigo>906</codigo><descripcion>CUIS generado correctamente (mock)</descripcion>"
            "</codigosRespuesta>"
            "</return>"
        ),
    )


def _handle_solicitud_cufd(request: etree._Element) -> bytes:
    vigencia = (datetime.now(timezone.utc) + timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S")
    return _soap_response(
        _FACT_NS,
        "solicitudCufd",
        (
            "<return>"
            f"<codigoCufd>{MOCK_CUFD}</codigoCufd>"
            f"<codigoControl>{MOCK_CODIGO_CONTROL}</codigoControl>"
            "<direccion>Av. Mock 123 (mock)</direccion>"
            f"<fechaVigencia>{vigencia}</fechaVigencia>"
            "<transaccion>true</transaccion>"
            "<codigosRespuesta>"
            "<codigo>905</codigo><descripcion>CUFD generado correctamente (mock)</descripcion>"
            "</codigosRespuesta>"
            "</return>"
        ),
    )


def _handle_recepcion_factura(request: etree._Element) -> bytes:
    return _soap_response(
        _FACT_NS,
        "RecepcionFactura",
        (
            "<return>"
            "<transaccion>true</transaccion>"
            "<codigoRecepcion>MOCK-00000001</codigoRecepcion>"
            "<codigoDescripcion>RECIBIDA (mock)</codigoDescripcion>"
            "</return>"
        ),
    )


def _handle_verificacion_estado_factura(request: etree._Element) -> bytes:
    return _soap_response(
        _FACT_NS,
        "verificacionEstadoFactura",
        (
            "<return>"
            "<codigoEstado>VALIDA</codigoEstado>"
            "<codigoDescripcion>Factura validada (mock)</codigoDescripcion>"
            "<transaccion>true</transaccion>"
            "</return>"
        ),
    )


def _handle_anulacion_factura(request: etree._Element) -> bytes:
    return _soap_response(
        _FACT_NS,
        "AnulacionFactura",
        (
            "<return>"
            "<transaccion>true</transaccion>"
            "<codigoEstado>ANULADA</codigoEstado>"
            "<codigoDescripcion>Factura anulada correctamente (mock)</codigoDescripcion>"
            "</return>"
        ),
    )


_HANDLERS = {
    "autenticacion": _handle_autenticacion,
    "verificarComunicacion": _handle_verificar_comunicacion,
    "solicitudCuis": _handle_solicitud_cuis,
    "solicitudCufd": _handle_solicitud_cufd,
    "RecepcionFactura": _handle_recepcion_factura,
    "verificacionEstadoFactura": _handle_verificacion_estado_factura,
    "AnulacionFactura": _handle_anulacion_factura,
}


class MockSinHandler(BaseHTTPRequestHandler):
    """Sirve los WSDL mock (`GET ...?wsdl`) y responde operaciones SOAP (`POST`)."""

    def log_message(self, format_: str, *args: object) -> None:
        pass

    def do_GET(self) -> None:
        if "wsdl" in self.path:
            if self.path.startswith("/autenticacion"):
                self._send_file(_WSDL_DIR / "servicio_autenticacion.wsdl")
                return
            if self.path.startswith("/facturacion"):
                self._send_file(_WSDL_DIR / "servicio_facturacion.wsdl")
                return
        self.send_error(404)

    def do_POST(self) -> None:
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        envelope = etree.fromstring(body)
        soap_body = envelope.find(f"{{{_SOAP_NS}}}Body")
        operation_element = soap_body[0]
        operation = _local_tag(operation_element)

        handler = _HANDLERS.get(operation)
        if handler is None:
            self.send_error(400, f"Operación no soportada por el mock: {operation}")
            return

        response = handler(operation_element)
        self.send_response(200)
        self.send_header("Content-Type", "text/xml; charset=utf-8")
        self.send_header("Content-Length", str(len(response)))
        self.end_headers()
        self.wfile.write(response)

    def _send_file(self, path: Path) -> None:
        content = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "text/xml; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)


def run_mock_server(host: str = "127.0.0.1", port: int = 8089) -> HTTPServer:
    """Crea (sin iniciar el loop) un `HTTPServer` con el mock. Llamar `.serve_forever()`."""
    return HTTPServer((host, port), MockSinHandler)


def start_mock_server_in_thread(host: str = "127.0.0.1", port: int = 8089) -> HTTPServer:
    """Inicia el mock en un hilo daemon y devuelve el `HTTPServer` (llamar `.shutdown()` para detenerlo)."""
    server = run_mock_server(host, port)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server


if __name__ == "__main__":
    mock_server = run_mock_server()
    host, port = mock_server.server_address
    print(f"Mock SIN escuchando en http://{host}:{port} (autenticacion / facturacion)")
    mock_server.serve_forever()
