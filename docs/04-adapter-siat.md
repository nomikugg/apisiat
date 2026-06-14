# Adapter SIAT (Fase 2) — estado y pendientes

## Estructura

```
app/integrations/siat/
  exceptions.py         # SiatError, SiatConnectionError, SiatValidationError
  schemas.py             # pydantic: CufdSolicitud/Resultado, FacturaSiatPayload, RecepcionResultado
  cuf/
    cuf_generator.py       # generar_cuf() — algoritmo vigente 2026 (portal SIN), implementado y testeado
    __init__.py            # re-exporta generar_cuf()
  soap_client.py          # SiatSoapClient (zeep) — wrapper genérico, requiere config de WSDL
  xml_builder.py           # build_factura_compra_venta_xml() — estructura basada en docs/01-02
  signing.py               # PKCS#12 + firma XML-DSig (signxml) + huella_digital() (placeholder)
```

Tests en `tests/integrations/siat/` (CUF generator, XML builder).

## Qué está implementado y validado

- **CUF (Código Único de Factura)**: `cuf/cuf_generator.py`, implementa el algoritmo vigente
  publicado por el SIN en `siatinfo.impuestos.gob.bo` (2026): concatenación de 53 dígitos
  (NIT, fecha/hora, sucursal, modalidad, tipo de emisión, tipo factura/documento ajuste,
  tipo documento sector, número de factura de 10 dígitos, punto de venta de 4 dígitos) +
  dígito autoverificador Módulo 11 (`suma % 11`, 10→1) + codificación Base 16 + sufijo
  "código de control" (`CufdResultado.codigo`). Tests verifican el ejemplo oficial del
  SIN, formato hexadecimal, round-trip de los 54 dígitos y determinismo. Reemplaza la
  versión anterior basada en el Anexo Técnico I de la RND 101800000026 (2018), que tenía
  un campo "Número de factura" de 8 dígitos y no incluía "Punto de venta" ni el sufijo de
  código de control.
- **CUFD/CUIS/CUAPE**: confirmado que NO se calculan localmente — se obtienen del SIN vía
  los servicios web "Solicitud de CUFD/CUIS/CUAPE" (`soap_client.obtener_cufd`). El campo
  `codigo` de la respuesta de CUFD se usa también como sufijo del CUF.
- **Generador XML "Factura Compra Venta"**: `xml_builder.py`, produce XML bien formado
  con los campos conocidos (cabecera + detalle).
- **PKCS#12 + firma XML-DSig**: `signing.py`, usa `cryptography` y `signxml` (librerías
  estándar, sin secretos del SIN).

## Pendientes — bloqueados por especificación oficial del SIN

1. **URLs WSDL de sandbox** — `settings.siat_wsdl_facturacion` / `settings.siat_wsdl_codigos`
   están vacías. Obtenerlas del portal `siatinfo.impuestos.gob.bo` (su certificado TLS no
   es validado por WebFetch/navegador; se descargó con `curl -k` para lectura, pero para
   uso en producción conviene revisar/instalar la cadena de certificados correcta) una vez
   se tenga el Token Delegado / registro en ambiente PILOTO. El método "Solicitud de CUFD"
   requiere además credenciales (`usuario`/`password`) del Token Delegado.

2. **"Huella digital" (modalidad Computarizada)** — el primitivo (SHA-256 sobre bytes ->
   hex en minúsculas) está confirmado en siatinfo.impuestos.gob.bo ("Algoritmos
   Utilizados > Generación de SHA-256, MD5 y CRC32") y coincide con
   `hashlib.sha256(...).hexdigest()`. Falta confirmar qué bytes exactos se hashean por
   factura (¿el XML completo?, ¿una concatenación puntual de campos?); `signing.
   huella_digital()` aplica SHA-256 sobre el XML completo como placeholder. No aplica a
   la modalidad Electrónica, que usa certificado digital completo.

3. **Validación XSD** — `xml_builder.build_factura_compra_venta_xml()` no está validado
   contra el XSD oficial de "Factura Compra Venta", publicado en
   `siatinfo.impuestos.gob.bo` (sección "Archivos XML / XSD de Facturas Electrónicas").

## Próximos pasos sugeridos

- Iniciar el registro como proveedor / ambiente PILOTO en el portal SIAT para obtener
  URLs WSDL de sandbox y un Token Delegado de prueba (usuario/password para
  "Solicitud de CUFD/CUIS").
- Una vez disponible el WSDL, implementar el flujo completo: CUIS -> CUFD -> generar CUF
  (usando `CufdResultado.codigo` como `codigo_cufd`) -> construir XML -> firmar ->
  `recepcion_factura`.
- Descargar el XSD oficial de "Factura Compra Venta" desde
  `siatinfo.impuestos.gob.bo` (sección "Archivos XML / XSD de Facturas Electrónicas") y
  validar `xml_builder.build_factura_compra_venta_xml()` contra él.
