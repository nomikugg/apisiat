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
  xml_builder.py           # build_factura_compra_venta_xml() + validar_contra_xsd()
  signing.py               # PKCS#12 + firma XML-DSig (signxml) + huella_digital() (placeholder)
  redondeo.py              # redondear_monto() — HALF-UP a 2 decimales (algoritmo SIN)
  paquetes.py              # comprimir_gzip()/descomprimir_gzip() — "Recepción Paquete Factura"
  xsd/
    SignatureSchema.xsd      # copia de xmldsig-core-schema.xsd (W3C, vía signxml) para
                              # resolver el <xs:import> de los XSD de factura
    facturas/
      facturaElectronicaCompraVenta.xsd/.xml   # XSD + ejemplo oficial del SIN
      facturaComputarizadaCompraVenta.xsd/.xml # idem, modalidad Computarizada
```

Tests en `tests/integrations/siat/` (CUF generator, XML builder, redondeo, paquetes, signing).

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
- **Generador XML "Factura Compra Venta"** (modalidades Electrónica/Computarizada):
  `xml_builder.py` + `schemas.py`. Reescrito en esta revisión a partir del XSD oficial
  descargado del portal SIN (`facturaElectronicaCompraVenta.xsd` /
  `facturaComputarizadaCompraVenta.xsd`, guardados en `app/integrations/siat/xsd/`):
  - `FacturaSiatPayload`/`FacturaSiatItem` ahora tienen los ~30 campos de `<cabecera>` y
    los 11 de `<detalle>` con los nombres y restricciones exactos del XSD (antes era un
    subconjunto simplificado con nombres distintos, ej. `cliente_nombre_razon_social`
    en vez de `nombreRazonSocial`/`numeroDocumento`/`codigoCliente` separados,
    `moneda: str = "BOB"` en vez de `codigoMoneda: int` codificado, etc.).
  - `<detalle>` se genera como elementos hermanos repetidos bajo la raíz (1 a 500, según
    el XSD), no como `<detalle><item>...</item></detalle>` (estructura anterior,
    incorrecta).
  - Campos `nillable` (`telefono`, `codigoPuntoVenta`, `nombreRazonSocial`,
    `complemento`, `numeroTarjeta`, `montoGiftCard`, `descuentoAdicional`,
    `codigoExcepcion`, `cafc`, `montoDescuento`, `numeroSerie`, `numeroImei`) se
    serializan como `<campo xsi:nil="true"/>` cuando son `None`.
  - `validar_contra_xsd(xml, modalidad=...)` valida contra el XSD oficial con
    `lxml.etree.XMLSchema`. Tests: la salida en modalidad "computarizada" valida
    directamente; en "electronica", tras firmarla con `signing.firmar_xml()` (el XSD
    exige `<Signature>` como último elemento).
  - **Pendiente** (no bloqueante para esta revisión): los catálogos de códigos
    (`codigoMoneda`, `codigoMetodoPago`, `unidadMedida`, `codigoTipoDocumentoIdentidad`,
    `actividadEconomica`, `codigoProductoSin`) son tablas de referencia del SIN
    ("Sincronización de Códigos y Catálogos", servicio web no implementado aún) — por
    ahora `FacturaSiatPayload`/`FacturaSiatItem` solo validan el *rango* numérico
    (ej. `codigoMoneda` 1-154), no que el código sea válido/exista en el catálogo.
- **PKCS#12 + firma XML-DSig**: `signing.py`, usa `cryptography` y `signxml` (librerías
  estándar, sin secretos del SIN). El proceso de 11 pasos descrito en
  siatinfo.impuestos.gob.bo ("Facturación en Línea > Firma Digital > Firma Digital") —
  canonicalizar, SHA-256, Base64, armar `<Signature>`, firmar con RSA-SHA256, etc. — es el
  procedimiento estándar de XML-DSig "enveloped" que `signxml.XMLSigner` ya implementa.
  `firmar_xml()` ahora pasa `cert=[certificate]` (no `certificate` suelto: `signxml`
  espera una `cert_chain`, lista/cadena — pasar un objeto `Certificate` suelto rompía con
  `TypeError: object of type 'Certificate' has no len()`, bug detectado y corregido en
  esta revisión, antes sin cobertura de tests) y `c14n_algorithm=CANONICAL_XML_1_0`, para
  que `<SignedInfo>/<CanonicalizationMethod>` coincida exactamente con el valor por
  defecto de Apache Santuario usado en el ejemplo Java oficial del SIN (C14N 1.0 sin
  comentarios; antes `signxml` usaba C14N 1.1 por defecto). Cubierto por
  `tests/integrations/siat/test_signing.py`.

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

3. **Algoritmo de canonicalización en `firmar_xml()` (parcialmente resuelto)** — el
   ejemplo Java oficial ("Facturación en Línea > Firma Digital > Firmado de XML")
   construye la firma con `<SignedInfo>/<CanonicalizationMethod>` = C14N 1.0 sin
   comentarios (`http://www.w3.org/TR/2001/REC-xml-c14n-20010315`, el valor por defecto de
   Apache Santuario) y `<Reference>/<Transforms>` =
   `[ENVELOPED_SIGNATURE, C14N 1.0 CON comentarios]`
   (`http://www.w3.org/TR/2001/REC-xml-c14n-20010315#WithComments`). `signxml` usaba por
   defecto `c14n_algorithm=CANONICAL_XML_1_1` (C14N **1.1**, sin comentarios) para AMBOS —
   no coincidía con el ejemplo del SIN en ninguno de los dos. Se corrigió pasando
   `c14n_algorithm=CANONICAL_XML_1_0` en `firmar_xml()`, lo que alinea
   `<SignedInfo>/<CanonicalizationMethod>` exactamente con el ejemplo del SIN (1.0 vs 1.1
   era la diferencia de algoritmo más concreta).

   Queda una diferencia menor sin resolver: el `<Reference>/<Transforms>` de
   `firmar_xml()` queda en C14N 1.0 **sin** comentarios (heredado de `c14n_algorithm`),
   mientras que el ejemplo del SIN usa la variante **con comentarios**
   (`#WithComments`). Como `xml_builder.py` no genera comentarios XML, el *digest*
   resultante es idéntico en ambos casos (con/sin comentarios solo difiere si el
   documento contiene comentarios) — solo cambia el string del `Algorithm` declarado en
   el `<Transform>`, que es a su vez parte de lo firmado (consistencia interna OK). Se
   intentó forzar `#WithComments` en el `Reference` vía
   `SignatureReference(URI=..., c14n_method=...)`, pero requiere agregar un atributo
   `Id` al elemento raíz y referenciarlo con `URI="#id"` (la `URI=""` de "documento
   completo" no es soportada por `signxml` junto con un `c14n_method` por-`Reference`
   distinto) — agregar un atributo `Id` no documentado al elemento raíz es un riesgo de
   romper la validación contra el XSD oficial, así que se descartó. La página "Firma
   Inválida" del mismo portal advierte que el algoritmo de hash/canonicalización
   incorrecto es la causa más común de "firma inválida", por lo que sigue siendo
   importante validar esto con un certificado de prueba real (ambiente PILOTO) en cuanto
   esté disponible.

## Próximos pasos sugeridos

- Iniciar el registro como proveedor / ambiente PILOTO en el portal SIAT para obtener
  URLs WSDL de sandbox y un Token Delegado de prueba (usuario/password para
  "Solicitud de CUFD/CUIS").
- Una vez disponible el WSDL, implementar el flujo completo: CUIS -> CUFD -> generar CUF
  (usando `CufdResultado.codigo` como `codigo_cufd`) -> construir XML -> firmar ->
  `recepcion_factura`.
- Descargar los XSD de los demás "tipos de documento sector" (notas de crédito/débito,
  exportación, hidrocarburos, etc., ver lista completa en
  `siatinfo.impuestos.gob.bo/index.php/facturacion-en-linea/archivos-xml-xsd-de-facturas-electronicas`)
  a medida que se necesiten, siguiendo el mismo patrón de
  `app/integrations/siat/xsd/facturas/`.
- Implementar el servicio "Sincronización de Códigos y Catálogos" para validar/resolver
  `codigoMoneda`, `codigoMetodoPago`, `unidadMedida`, `codigoTipoDocumentoIdentidad`,
  `actividadEconomica` y `codigoProductoSin` contra las tablas reales del SIN (hoy solo
  se valida el rango numérico, ver "Generador XML" arriba).
- Con un certificado de prueba del ambiente PILOTO, firmar un XML de ejemplo con
  `signing.firmar_xml()` y comparar el `<Signature>` resultante contra el del ejemplo Java
  oficial (algoritmos de `CanonicalizationMethod`/`Transforms`, ver pendiente #3) hasta
  obtener "firma válida" del SIN.
