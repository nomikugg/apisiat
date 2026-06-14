from app.integrations.siat.cuf.verhoeff import verhoeff_digit, verhoeff_validate


def test_verhoeff_digit_known_vector():
    # Ejemplo de referencia (Wikipedia, "Verhoeff algorithm"): 236 -> dígito 3 -> 2363
    assert verhoeff_digit("236") == "3"


def test_verhoeff_validate_known_vector():
    assert verhoeff_validate("2363") is True


def test_verhoeff_validate_detects_error():
    assert verhoeff_validate("2364") is False
