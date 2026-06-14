"""
CUF (Código Único de Factura) — ver `cuf_generator.py` para el algoritmo.

El CUFD (Código Único de Facturación Diaria), el CUIS (Código Único de
Identificación del Sistema) y el CUAPE (modalidad Prevalorado) NO se calculan
localmente: se obtienen del SIN mediante los servicios web "Solicitud de
CUFD" / "Solicitud de CUIS" / "Solicitud de CUAPE" (ver
`app.integrations.siat.soap_client.SiatSoapClient.obtener_cufd`).

`generar_cuf()` además requiere el campo `codigo` de ese resultado
(`CufdResultado.codigo`) como parámetro `codigo_cufd`: el CUF final es la
concatenación de la parte calculada localmente con ese código.
"""

from app.integrations.siat.cuf.cuf_generator import generar_cuf

__all__ = ["generar_cuf"]
