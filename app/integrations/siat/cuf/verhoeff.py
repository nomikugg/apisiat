"""
Algoritmo de Verhoeff (ISO/IEC 7064, esquema "Verhoeff") para dígitos de control.

Referencia: docs/01-marco-regulatorio-sin.md — el Código de Control del CUF/CUFD usa
dígitos Verhoeff en sus pasos 1 y 2. Esta implementación sigue las tablas estándar
publicadas (multiplicación d, permutación p, inversa inv) y es independiente de
cualquier secreto del SIN.
"""

# Tabla de multiplicación (d8/5 - grupo diedro de orden 10)
_D = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
]

# Tabla de permutación (8 filas, una por posición módulo 8)
_P = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
]

# Tabla inversa
_INV = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]


def _checksum(numero: str, offset: int = 0) -> int:
    if not numero.isdigit():
        raise ValueError(f"numero debe contener solo dígitos: {numero!r}")
    c = 0
    for i, ch in enumerate(reversed(numero)):
        c = _D[c][_P[(i + offset) % 8][int(ch)]]
    return c


def verhoeff_digit(numero: str) -> str:
    """Calcula el dígito de control Verhoeff para `numero` (solo dígitos)."""
    # Generación: el dígito de control ocupará la posición 0, así que `numero`
    # se procesa con un desfase de 1 en la tabla de permutación.
    c = _checksum(numero, offset=1)
    return str(_INV[c])


def verhoeff_validate(numero: str) -> bool:
    """Valida que `numero` (incluyendo su último dígito como dígito de control) sea correcto."""
    return _checksum(numero, offset=0) == 0
