from datetime import datetime

import pytest

from app.integrations.siat.cuf.cuf_generator import (
    _digito_verificador_modulo11,
    generar_cuf,
)


def test_digito_verificador_modulo11_es_un_solo_digito():
    for n in range(0, 100):
        digitos = str(n).zfill(53)
        digito = _digito_verificador_modulo11(digitos)
        assert 0 <= digito <= 9


def test_generar_cuf_coincide_con_ejemplo_oficial_del_sin():
    # Ejemplo oficial de siatinfo.impuestos.gob.bo
    # ("Facturación en Línea > Algoritmos Utilizados > Generación CUF").
    cuf = generar_cuf(
        nit=123456789,
        fecha_hora_emision=datetime(2019, 1, 13, 16, 37, 21, 231_000),
        sucursal=0,
        modalidad=1,
        tipo_emision=1,
        tipo_factura_documento_ajuste=1,
        tipo_documento_sector=1,
        numero_factura=1,
        punto_venta=0,
        codigo_cufd="A19E23EF34124CD",
    )

    assert cuf == "8727F63A15F8976591FDDE5B387C5D015A29E06A1A19E23EF34124CD"


def test_generar_cuf_es_hexadecimal_y_decodifica_a_54_digitos():
    cuf = generar_cuf(
        nit=123456789,
        fecha_hora_emision=datetime(2026, 1, 15, 10, 30, 0, 123_000),
        sucursal=0,
        modalidad=1,
        tipo_emision=1,
        tipo_factura_documento_ajuste=1,
        tipo_documento_sector=1,
        numero_factura=1,
        punto_venta=0,
        codigo_cufd="ABCDEF0123456789",
    )

    hex_parte, codigo_cufd = cuf[:-16], cuf[-16:]
    assert codigo_cufd == "ABCDEF0123456789"
    assert all(c in "0123456789ABCDEF" for c in hex_parte)

    cadena_54 = str(int(hex_parte, 16)).zfill(54)
    campos, digito = cadena_54[:53], cadena_54[53]
    campos_esperado = (
        "0000123456789"  # NIT (13)
        "20260115103000123"  # fecha/hora yyyyMMddHHmmssSSS (17)
        "0000"  # sucursal (4)
        "1"  # modalidad (1)
        "1"  # tipo de emisión (1)
        "1"  # tipo factura / documento ajuste (1)
        "01"  # tipo documento sector (2)
        "0000000001"  # número de factura (10)
        "0000"  # punto de venta (4)
    )
    assert campos == campos_esperado
    assert int(digito) == _digito_verificador_modulo11(campos)


def test_generar_cuf_es_deterministico():
    kwargs = dict(
        nit=987654321,
        fecha_hora_emision=datetime(2026, 6, 14, 23, 59, 59, 999_000),
        sucursal=2,
        modalidad=2,
        tipo_emision=2,
        tipo_factura_documento_ajuste=1,
        tipo_documento_sector=24,
        numero_factura=42,
        punto_venta=1,
        codigo_cufd="A19E23EF34124CD",
    )
    assert generar_cuf(**kwargs) == generar_cuf(**kwargs)


def test_generar_cuf_rechaza_nit_demasiado_largo():
    with pytest.raises(ValueError):
        generar_cuf(
            nit=10**14,  # 15 dígitos, desborda el campo de 13
            fecha_hora_emision=datetime(2026, 1, 1),
            sucursal=0,
            modalidad=1,
            tipo_emision=1,
            tipo_factura_documento_ajuste=1,
            tipo_documento_sector=1,
            numero_factura=1,
            punto_venta=0,
            codigo_cufd="A19E23EF34124CD",
        )
