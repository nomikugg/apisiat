from decimal import Decimal

from app.integrations.siat.redondeo import redondear_monto


def test_redondear_monto_ejemplos_oficiales_del_sin():
    assert redondear_monto(Decimal("3.14159")) == Decimal("3.14")
    assert redondear_monto(Decimal("3.14559")) == Decimal("3.15")


def test_redondear_monto_usa_half_up_no_half_even():
    # 2.345 redondeado a 2 decimales: HALF_EVEN (default de Decimal) da 2.34,
    # HALF_UP (el algoritmo del SIN) da 2.35.
    assert redondear_monto(Decimal("2.345")) == Decimal("2.35")


def test_redondear_monto_completa_decimales_faltantes():
    assert redondear_monto(Decimal("10")) == Decimal("10.00")
    assert redondear_monto(Decimal("10.1")) == Decimal("10.10")
