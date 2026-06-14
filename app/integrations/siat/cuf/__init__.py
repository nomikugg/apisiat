"""
Generación de CUF (Código Único de Factura) y CUFD (Código Único de Facturación Diaria).

Ambos códigos se construyen formateando el "Código de Control" (ver `codigo_control.py`)
en pares de caracteres separados por guiones (ej. "6A-DC-53-05-14"), según
docs/01-marco-regulatorio-sin.md. La función `calcular_codigo_control` levanta
`CodigoControlNoDisponibleError` mientras falte la especificación oficial del SIN
(pasos 2-6); estas funciones propagan ese error.
"""

from datetime import datetime
from decimal import Decimal

from app.integrations.siat.cuf.codigo_control import calcular_codigo_control


def _formatear_en_pares(codigo: str) -> str:
    """Formatea un código alfanumérico en pares separados por guion (ej. '6ADC53' -> '6A-DC-53')."""
    return "-".join(codigo[i : i + 2] for i in range(0, len(codigo), 2))


def generar_cuf(
    *,
    nit: int,
    numero_factura: int,
    fecha: datetime,
    monto_total: Decimal,
    clave_dosificacion: str,
) -> str:
    """Genera el CUF para una factura (hasta 10 caracteres alfanuméricos en pares)."""
    codigo = calcular_codigo_control(
        nit=nit,
        numero_factura=numero_factura,
        fecha=fecha,
        monto_total=monto_total,
        clave_dosificacion=clave_dosificacion,
    )
    return _formatear_en_pares(codigo)


def generar_cufd(
    *,
    nit: int,
    fecha: datetime,
    clave_dosificacion: str,
) -> str:
    """Genera el CUFD (vigencia 24h) para un punto de venta."""
    codigo = calcular_codigo_control(
        nit=nit,
        numero_factura=0,
        fecha=fecha,
        monto_total=Decimal(0),
        clave_dosificacion=clave_dosificacion,
    )
    return _formatear_en_pares(codigo)
