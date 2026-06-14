# Adapter SIAT (Fase 2) — estado y pendientes

## Estructura

```
app/integrations/siat/
  exceptions.py         # SiatError, SiatConnectionError, SiatValidationError
  schemas.py             # pydantic: CufdSolicitud/Resultado, FacturaSiatPayload, RecepcionResultado
  cuf/
    cuf_generator.py       # generar_cuf() — algoritmo oficial RND 101800000026, implementado y testeado
    __init__.py            # re-exporta generar_cuf()
  soap_client.py          # SiatSoapClient (zeep) — wrapper genérico, requiere config de WSDL
  xml_builder.py           # build_factura_compra_venta_xml() — estructura basada en docs/01-02
  signing.py               # PKCS#12 + firma XML-DSig (signxml) + huella_digital() (placeholder)
```

Tests en `tests/integrations/siat/` (CUF generator, XML builder).

## Qué está implementado y validado

- **CUF (Código Único de Factura)**: `cuf/cuf_generator.py`, implementa el algoritmo oficial
  del Anexo Técnico I (RND N° 101800000026): concatenación de 47 dígitos (NIT, fecha/hora,
  sucursal, modalidad, tipo de emisión, código documento fiscal, tipo documento sector,
  número de factura) + dígito autoverificador "Base 11" (Módulo 11 estándar) + codificación
  Base 16. Tests verifican formato hexadecimal, round-trip de los 48 dígitos y determinismo.
  **Pendiente**: validar el dígito "Base 11" contra casos de prueba oficiales del SIN — el
  anexo no detalla ese algoritmo más allá del nombre.
- **CUFD/CUIS/CUAPE**: confirmado que NO se calculan localmente — se obtienen del SIN vía
  los servicios web "Solicitud de CUFD/CUIS/CUAPE" (`soap_client.obtener_cufd`).
- **Generador XML "Factura Compra Venta"**: `xml_builder.py`, produce XML bien formado
  con los campos conocidos (cabecera + detalle).
- **PKCS#12 + firma XML-DSig**: `signing.py`, usa `cryptography` y `signxml` (librerías
  estándar, sin secretos del SIN).

## Pendientes — bloqueados por especificación oficial del SIN

1. **Dígito "Base 11" del CUF** — `cuf/cuf_generator.py` implementa el Módulo 11 estándar
   usado en Bolivia, pero el anexo no lo especifica en detalle. Falta validar contra los
   casos de prueba oficiales del SIN (si se publican).

2. **URLs WSDL de sandbox** — `settings.siat_wsdl_facturacion` / `settings.siat_wsdl_codigos`
   están vacías. Obtenerlas del portal `siatinfo.impuestos.gob.bo` (su certificado TLS no
   es validado por WebFetch; revisar manualmente desde navegador) una vez se tenga el
   Token Delegado / registro en ambiente PILOTO. El método "Solicitud de CUFD" requiere
   además credenciales (`usuario`/`password`) del Token Delegado.

3. **"Huella digital" (modalidad Computarizada)** — `signing.huella_digital()` aplica
   SHA-256 sobre el XML completo como placeholder. El anexo solo menciona huellas
   MD5/CRC32/SHA256 para certificación de componentes del sistema (no para facturas
   individuales); falta confirmar si "huella digital" por factura aplica a la modalidad
   que vayamos a usar (Electrónica) o es exclusivo de Computarizada/SFV legado.

4. **Validación XSD** — `xml_builder.build_factura_compra_venta_xml()` no está validado
   contra el XSD oficial de "Factura Compra Venta"; el anexo menciona que los XSD se
   publican en la página web de la Administración Tributaria pero no estaban incluidos
   en el PDF descargado.

## Próximos pasos sugeridos

- Iniciar el registro como proveedor / ambiente PILOTO en el portal SIAT para obtener
  URLs WSDL de sandbox y un Token Delegado de prueba (usuario/password para
  "Solicitud de CUFD/CUIS").
- Una vez disponible el WSDL, implementar el flujo completo: CUIS -> CUFD -> generar CUF
  -> construir XML -> firmar -> `recepcion_factura`.
- Si el SIN publica casos de prueba del dígito "Base 11" del CUF, agregarlos como tests
  parametrizados en `tests/integrations/siat/test_cuf_generator.py`.
