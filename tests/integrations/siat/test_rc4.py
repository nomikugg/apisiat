from app.integrations.siat.cuf.rc4 import rc4


def test_rc4_known_vector():
    # Vector de referencia estándar (Wikipedia, "RC4"): key="Key", plaintext="Plaintext"
    ciphertext = rc4(b"Key", b"Plaintext")
    assert ciphertext.hex().upper() == "BBF316E8D940AF0AD3"


def test_rc4_is_symmetric():
    key = b"clave-de-prueba"
    data = b"hola mundo"
    ciphertext = rc4(key, data)
    assert rc4(key, ciphertext) == data
