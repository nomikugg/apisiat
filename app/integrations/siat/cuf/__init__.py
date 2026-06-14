"""
CUF (Código Único de Factura) — ver `cuf_generator.py` para el algoritmo.

El CUFD (Código Único de Facturación Diaria), el CUIS (Código Único de
Identificación del Sistema) y el CUAPE (modalidad Prevalorado) NO se calculan
localmente: se obtienen del SIN mediante los servicios web "Solicitud de
CUFD" / "Solicitud de CUIS" / "Solicitud de CUAPE" (ver
`app.integrations.siat.soap_client.SiatSoapClient.obtener_cufd`).
"""

from app.integrations.siat.cuf.cuf_generator import generar_cuf

__all__ = ["generar_cuf"]
