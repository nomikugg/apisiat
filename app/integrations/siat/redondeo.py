"""
Redondeo de montos monetarios.

El portal del SIN (siatinfo.impuestos.gob.bo, "Algoritmos Utilizados > Algoritmo de
Redondeo") especifica que los montos de facturas electrónicas en línea usan redondeo
HALF-UP ("tradicional") a 2 decimales (ej.: 3.14159 -> 3.14, 3.14559 -> 3.15).

`Decimal.quantize` redondea con ROUND_HALF_EVEN por defecto ("banker's rounding"), que
difiere de HALF-UP en los casos exactamente intermedios (ej.: 2.345 -> 2.34 con
HALF_EVEN, 2.35 con HALF_UP), por lo que hay que forzar ROUND_HALF_UP explícitamente.
"""

from decimal import ROUND_HALF_UP, Decimal

_DOS_DECIMALES = Decimal("0.01")


def redondear_monto(valor: Decimal) -> Decimal:
    """Redondea `valor` a 2 decimales usando HALF-UP, según el algoritmo del SIN."""
    return valor.quantize(_DOS_DECIMALES, rounding=ROUND_HALF_UP)
