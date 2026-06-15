import gzip

from app.integrations.siat.paquetes import comprimir_gzip, descomprimir_gzip


def test_comprimir_gzip_produce_formato_gzip_valido():
    xml = "<?xml version='1.0' encoding='UTF-8'?><facturaElectronicaCompraVenta/>"
    comprimido = comprimir_gzip(xml)
    assert gzip.decompress(comprimido).decode("utf-8") == xml


def test_descomprimir_gzip_es_inverso_de_comprimir():
    xml = "<root>contenido de prueba</root>"
    assert descomprimir_gzip(comprimir_gzip(xml)) == xml
