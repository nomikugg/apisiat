"""
Codec Base64 con alfabeto personalizado de 64 caracteres.

Referencia: docs/01-marco-regulatorio-sin.md — el paso 5 del Código de Control convierte
un valor a "Base64" usando un diccionario propio del SIN de 64 caracteres (sin O/l/0/1)
en vez del alfabeto estándar RFC 4648.

`ALFABETO_SIN_PLACEHOLDER` es un EJEMPLO que cumple la restricción (64 caracteres únicos,
sin O/l/0/1) pero NO es el alfabeto real del SIN — ese dato forma parte del anexo técnico
oficial (ver docs/04-adapter-siat.md). El codec en sí (encode/decode) es genérico y
funciona con cualquier alfabeto de 64 caracteres únicos que se le pase.
"""

import base64
import string

_STANDARD_ALPHABET = string.ascii_uppercase + string.ascii_lowercase + string.digits + "+/"
_PADDING_CHAR = "="

# Placeholder de ejemplo (NO es el alfabeto oficial del SIN): A-Z sin O, a-z sin l, 2-9, y 6 símbolos extra.
ALFABETO_SIN_PLACEHOLDER = (
    "ABCDEFGHIJKLMNPQRSTUVWXYZ"  # sin O
    "abcdefghijkmnopqrstuvwxyz"  # sin l
    "23456789"  # sin 0 y 1
    "+/-_.~"
)


def _validar_alfabeto(alfabeto: str) -> None:
    if len(alfabeto) != 64:
        raise ValueError(f"el alfabeto debe tener 64 caracteres, tiene {len(alfabeto)}")
    if len(set(alfabeto)) != 64:
        raise ValueError("el alfabeto debe tener 64 caracteres únicos")
    if _PADDING_CHAR in alfabeto:
        raise ValueError(f"el alfabeto no debe incluir el carácter de padding {_PADDING_CHAR!r}")


def encode(data: bytes, alfabeto: str) -> str:
    """Codifica `data` en Base64 usando `alfabeto` (64 caracteres únicos) en vez del estándar."""
    _validar_alfabeto(alfabeto)
    estandar = base64.b64encode(data).decode("ascii")
    tabla = str.maketrans(_STANDARD_ALPHABET, alfabeto)
    return estandar.translate(tabla)


def decode(texto: str, alfabeto: str) -> bytes:
    """Decodifica un string producido por `encode` con el mismo `alfabeto`."""
    _validar_alfabeto(alfabeto)
    tabla = str.maketrans(alfabeto, _STANDARD_ALPHABET)
    estandar = texto.translate(tabla)
    return base64.b64decode(estandar)
