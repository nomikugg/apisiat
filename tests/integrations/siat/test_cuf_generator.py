from datetime import datetime

import pytest

from app.integrations.siat.cuf.cuf_generator import (
    _digito_verificador_base11,
    generar_cuf,
)


def test_digito_verificador_base11_es_un_solo_digito():
    for n in range(0, 100):
        digitos = str(n).zfill(47)
        digito = _digito_verificador_base11(digitos)
        assert 0 <= digito <= 9


def test_generar_cuf_es_hexadecimal_y_decodifica_a_48_digitos():
    cuf = generar_cuf(
        nit=123456789,
        fecha_hora_emision=datetime(2026, 1, 15, 10, 30, 0, 123_000),
        sucursal=0,
        modalidad=1,
        tipo_emision=0,
        codigo_documento_fiscal=1,
        tipo_documento_sector=1,
        numero_factura=1,
    )

    # Solo caracteres hexadecimales (mayúsculas).
    assert all(c in "0123456789ABCDEF" for c in cuf)

    # Al decodificar, la cadena de 48 dígitos reconstruye los campos + dígito verificador.
    cadena_48 = str(int(cuf, 16)).zfill(48)
    campos, digito = cadena_48[:47], cadena_48[47]
    campos_esperado = (
        "0000123456789"  # NIT (13)
        "20260115103000123"  # fecha/hora yyyymmddhhmmssmmm (17)
        "0000"  # sucursal (4)
        "1"  # modalidad (1)
        "0"  # tipo de emisión (1)
        "1"  # código documento fiscal (1)
        "01"  # tipo documento sector (2)
        "00000001"  # número de factura (8)
    )
    assert campos == campos_esperado
    assert int(digito) == _digito_verificador_base11(campos)


def test_generar_cuf_es_deterministico():
    kwargs = dict(
        nit=987654321,
        fecha_hora_emision=datetime(2026, 6, 14, 23, 59, 59, 999_000),
        sucursal=2,
        modalidad=2,
        tipo_emision=1,
        codigo_documento_fiscal=1,
        tipo_documento_sector=22,
        numero_factura=42,
    )
    assert generar_cuf(**kwargs) == generar_cuf(**kwargs)


def test_generar_cuf_rechaza_nit_demasiado_largo():
    with pytest.raises(ValueError):
        generar_cuf(
            nit=10**14,  # 15 dígitos, desborda el campo de 13
            fecha_hora_emision=datetime(2026, 1, 1),
            sucursal=0,
            modalidad=1,
            tipo_emision=0,
            codigo_documento_fiscal=1,
            tipo_documento_sector=1,
            numero_factura=1,
        )
