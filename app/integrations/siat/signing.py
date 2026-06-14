"""
Firma digital de documentos XML.

- Modalidad Electrónica: certificado PKCS#12 (ADSIB/DigiCert) + firma XML-DSig "enveloped".
- Modalidad Computarizada: "huella digital" (hash del XML) en vez de firma completa.

La carga de PKCS#12 y la firma XML-DSig usan librerías estándar (`cryptography`,
`signxml`) y no dependen de secretos del SIN. La función `huella_digital` es un
placeholder: el SIN especifica una concatenación de campos puntual para el hash que no
está disponible en este entorno (ver docs/04-adapter-siat.md).
"""

import hashlib

from cryptography.hazmat.primitives.asymmetric.types import PrivateKeyTypes
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509 import Certificate
from lxml import etree
from signxml import XMLSigner


def cargar_pkcs12(pfx_bytes: bytes, password: str) -> tuple[PrivateKeyTypes, Certificate]:
    """Carga la clave privada y el certificado desde un archivo PKCS#12 (.p12/.pfx)."""
    private_key, certificate, _ = pkcs12.load_key_and_certificates(pfx_bytes, password.encode("utf-8"))
    if private_key is None or certificate is None:
        raise ValueError("el PKCS#12 no contiene clave privada y/o certificado")
    return private_key, certificate


def firmar_xml(xml: str, private_key: PrivateKeyTypes, certificate: Certificate) -> str:
    """Firma `xml` con XML-DSig (enveloped) usando la clave y certificado dados."""
    root = etree.fromstring(xml.encode("utf-8"))
    signed_root = XMLSigner().sign(root, key=private_key, cert=certificate)
    return etree.tostring(signed_root, xml_declaration=True, encoding="UTF-8").decode("utf-8")


def huella_digital(xml: str) -> str:
    """
    Calcula la "huella digital" (modalidad Computarizada) de un XML.

    El primitivo (SHA-256 sobre bytes -> hex en minúsculas, vía
    `DatatypeConverter.printHexBinary(...).toLowerCase()`) está confirmado en
    siatinfo.impuestos.gob.bo ("Algoritmos Utilizados > Generación de SHA-256, MD5 y
    CRC32") y coincide con `hashlib.sha256(...).hexdigest()`.

    TODO: falta confirmar qué bytes exactos se hashean para la "huella digital" por
    factura (¿el XML completo?, ¿una concatenación puntual de campos?). Esta
    implementación aplica SHA-256 sobre el XML completo como placeholder
    (ver docs/04-adapter-siat.md).
    """
    return hashlib.sha256(xml.encode("utf-8")).hexdigest()
