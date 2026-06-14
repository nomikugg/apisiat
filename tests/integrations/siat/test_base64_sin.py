import pytest

from app.integrations.siat.cuf.base64_sin import ALFABETO_SIN_PLACEHOLDER, decode, encode


def test_roundtrip_with_placeholder_alphabet():
    data = b"hola mundo CUF/CUFD"
    encoded = encode(data, ALFABETO_SIN_PLACEHOLDER)
    assert decode(encoded, ALFABETO_SIN_PLACEHOLDER) == data


def test_placeholder_alphabet_excludes_ambiguous_chars():
    for ch in "O0l1":
        assert ch not in ALFABETO_SIN_PLACEHOLDER


def test_invalid_alphabet_length_rejected():
    with pytest.raises(ValueError):
        encode(b"x", "ABC")
