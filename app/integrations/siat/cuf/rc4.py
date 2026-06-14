"""
Cifrado de flujo RC4 genérico.

Referencia: docs/01-marco-regulatorio-sin.md — el paso 3 (y 6) del Código de Control
cifran con RC4 usando la clave de dosificación combinada con dígitos Verhoeff. Esta
es una implementación estándar de RC4 (KSA + PRGA), sin nada específico del SIN.
"""


def _ksa(key: bytes) -> list[int]:
    s = list(range(256))
    j = 0
    for i in range(256):
        j = (j + s[i] + key[i % len(key)]) % 256
        s[i], s[j] = s[j], s[i]
    return s


def _prga(s: list[int], length: int) -> bytes:
    i = j = 0
    out = bytearray(length)
    for n in range(length):
        i = (i + 1) % 256
        j = (j + s[i]) % 256
        s[i], s[j] = s[j], s[i]
        out[n] = s[(s[i] + s[j]) % 256]
    return bytes(out)


def rc4(key: bytes, data: bytes) -> bytes:
    """Cifra/descifra `data` con la clave `key` usando RC4 (operación simétrica)."""
    if not key:
        raise ValueError("key no puede estar vacía")
    s = _ksa(key)
    keystream = _prga(s, len(data))
    return bytes(a ^ b for a, b in zip(data, keystream))
