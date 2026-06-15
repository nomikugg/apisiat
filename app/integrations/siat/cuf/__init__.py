"""
CUF (Código Único de Factura) — ver `cuf_generator.py` para el algoritmo.

El CUFD (Código Único de Facturación Diaria), el CUIS (Código Único de
Identificación del Sistema) y el CUAPE (modalidad Prevalorado) NO se calculan
localmente: se obtienen del SIN mediante los servicios web "Solicitud de
CUFD" / "Solicitud de CUIS" / "Solicitud de CUAPE" (ver
`app.integrations.siat.soap_client.SiatSoapClient.solicitud_cufd`).

`generar_cuf()` además requiere el campo `codigoControl` de ese resultado
(`CufdResultado.codigo_control`) como parámetro `codigo_control`: el CUF final
es la concatenación de la parte calculada localmente con ese código. No
confundir con `CufdResultado.codigo_cufd` (campo `codigoCUFD`), que es el
valor que va en `<cufd>` de la factura y en `RecepcionFactura`.
"""

from app.integrations.siat.cuf.cuf_generator import generar_cuf

__all__ = ["generar_cuf"]
