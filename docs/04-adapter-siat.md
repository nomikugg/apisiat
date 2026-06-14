# Adapter SIAT (Fase 2) — estado y pendientes

## Estructura

```
app/integrations/siat/
  exceptions.py         # SiatError, SiatConnectionError, SiatValidationError, CodigoControlNoDisponibleError
  schemas.py             # pydantic: CufdSolicitud/Resultado, FacturaSiatPayload, RecepcionResultado
  cuf/
    verhoeff.py           # Algoritmo Verhoeff (ISO/IEC 7064) — implementado y testeado
    rc4.py                # Cifrado RC4 genérico — implementado y testeado
    base64_sin.py          # Codec Base64 con alfabeto de 64 chars parametrizable — implementado y testeado
    codigo_control.py      # Ensamblaje del Código de Control (6 pasos) — paso 1 implementado, 2-6 pendientes
    __init__.py            # generar_cuf() / generar_cufd()
  soap_client.py          # SiatSoapClient (zeep) — wrapper genérico, requiere config de WSDL
  xml_builder.py           # build_factura_compra_venta_xml() — estructura basada en docs/01-02
  signing.py               # PKCS#12 + firma XML-DSig (signxml) + huella_digital() (placeholder)
```

Tests en `tests/integrations/siat/` (Verhoeff, RC4, Base64-SIN, XML builder).

## Qué está implementado y validado

- **Verhoeff (ISO/IEC 7064)**: `cuf/verhoeff.py`, validado contra el vector de referencia
  público "236" → dígito de control "3" (2363).
- **RC4 genérico**: `cuf/rc4.py`, validado contra el vector estándar `key="Key"`,
  `plaintext="Plaintext"` → `BBF316E8D940AF0AD3`.
- **Codec Base64 con alfabeto parametrizable**: `cuf/base64_sin.py`, round-trip testeado.
  `ALFABETO_SIN_PLACEHOLDER` es solo un ejemplo con la forma correcta (64 chars únicos,
  sin O/l/0/1) — **no** es el alfabeto real del SIN.
- **Generador XML "Factura Compra Venta"**: `xml_builder.py`, produce XML bien formado
  con los campos conocidos (cabecera + detalle).
- **PKCS#12 + firma XML-DSig**: `signing.py`, usa `cryptography` y `signxml` (librerías
  estándar, sin secretos del SIN).

## Pendientes — bloqueados por especificación oficial del SIN

1. **Código de Control (CUF/CUFD), pasos 2-6** — `cuf/codigo_control.py` levanta
   `CodigoControlNoDisponibleError`. Falta:
   - El algoritmo exacto de extracción de subcadenas de la "clave de dosificación"
     (posiciones/longitudes).
   - El alfabeto Base64 real de 64 caracteres del SIN.
   - Los ~5000 casos de prueba publicados por el SIN para validar el resultado.
   - Fuente: PDF "Anexos Técnicos SFE" (`impuestos.gob.bo/wp-content/uploads/.../ANEXOS-TECNICOS-SFE.pdf`,
     7.5MB — no se pudo extraer texto en este entorno; requiere herramienta PDF adicional
     o descarga manual).

2. **URLs WSDL de sandbox** — `settings.siat_wsdl_facturacion` / `settings.siat_wsdl_codigos`
   están vacías. Obtenerlas del portal `siatinfo.impuestos.gob.bo` (su certificado TLS no
   es validado por WebFetch; revisar manualmente desde navegador) una vez se tenga el
   Token Delegado / registro en ambiente PILOTO.

3. **"Huella digital" (modalidad Computarizada)** — `signing.huella_digital()` aplica
   SHA-256 sobre el XML completo como placeholder. Falta la especificación exacta de qué
   campos concatenar y en qué orden/formato antes del hash.

4. **Validación XSD** — `xml_builder.build_factura_compra_venta_xml()` no está validado
   contra el XSD oficial de "Factura Compra Venta"; revisar cuando se obtenga del anexo
   técnico.

## Próximos pasos sugeridos

- Conseguir el PDF de Anexos Técnicos SFE (manualmente, o con una herramienta de
  extracción PDF disponible) para completar `codigo_control.py` y validar contra los
  casos de prueba oficiales.
- Iniciar el registro como proveedor / ambiente PILOTO en el portal SIAT para obtener
  URLs WSDL de sandbox y un Token Delegado de prueba.
- Una vez disponibles los pasos 2-6, escribir tests parametrizados con los ~5000 casos
  de prueba del SIN.
