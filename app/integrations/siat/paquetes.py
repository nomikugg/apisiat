"""
Compresión GZIP de paquetes de facturas.

El portal del SIN (siatinfo.impuestos.gob.bo, "Algoritmos Utilizados > Comprimir GZIP")
especifica que, para "Recepción Paquete Factura" (envío por contingencia o masivo), cada
archivo XML se comprime con GZIP antes de enviarse (el ejemplo Java usa
`GZIPOutputStream` y nombra el resultado con sufijo ".zip", aunque el formato es gzip
real, no zip).

TODO: falta confirmar la codificación del campo SOAP que recibe el contenido comprimido
(habitualmente Base64 para campos binarios en WSDL) — ver docs/04-adapter-siat.md.
"""

import gzip


def comprimir_gzip(xml: str) -> bytes:
    """Comprime un XML (UTF-8) con GZIP, como requiere "Recepción Paquete Factura"."""
    return gzip.compress(xml.encode("utf-8"))


def descomprimir_gzip(data: bytes) -> str:
    """Descomprime un paquete GZIP a su XML (UTF-8) original."""
    return gzip.decompress(data).decode("utf-8")
