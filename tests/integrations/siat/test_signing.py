import datetime

from cryptography import x509
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from lxml import etree

from app.integrations.siat.signing import firmar_xml, huella_digital

NS = {"ds": "http://www.w3.org/2000/09/xmldsig#"}


def _generar_certificado_prueba():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    nombre = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "prueba")])
    ahora = datetime.datetime.now(datetime.timezone.utc)
    certificado = (
        x509.CertificateBuilder()
        .subject_name(nombre)
        .issuer_name(nombre)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(ahora)
        .not_valid_after(ahora + datetime.timedelta(days=1))
        .sign(key, hashes.SHA256())
    )
    return key, certificado


def test_firmar_xml_produce_signature_envuelta():
    key, certificado = _generar_certificado_prueba()
    xml = "<?xml version='1.0' encoding='UTF-8'?><facturaElectronicaCompraVenta><a>1</a></facturaElectronicaCompraVenta>"

    firmado = firmar_xml(xml, key, certificado)
    root = etree.fromstring(firmado.encode("utf-8"))

    assert root.tag == "facturaElectronicaCompraVenta"
    assert root.find("ds:Signature", NS) is not None


def test_firmar_xml_usa_canonicalizacion_c14n_1_0_sin_comentarios():
    # Replica el <CanonicalizationMethod> del ejemplo Java oficial del SIN
    # ("Firmado de XML"), que usa el default de Apache Santuario: C14N 1.0 sin comentarios.
    key, certificado = _generar_certificado_prueba()
    xml = "<?xml version='1.0' encoding='UTF-8'?><facturaElectronicaCompraVenta><a>1</a></facturaElectronicaCompraVenta>"

    firmado = firmar_xml(xml, key, certificado)
    root = etree.fromstring(firmado.encode("utf-8"))

    c14n_method = root.find("ds:Signature/ds:SignedInfo/ds:CanonicalizationMethod", NS)
    assert c14n_method.get("Algorithm") == "http://www.w3.org/TR/2001/REC-xml-c14n-20010315"


def test_huella_digital_es_sha256_hex():
    import hashlib

    xml = "<root/>"
    assert huella_digital(xml) == hashlib.sha256(xml.encode("utf-8")).hexdigest()
