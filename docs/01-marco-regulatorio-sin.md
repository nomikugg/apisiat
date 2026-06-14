# Marco técnico-regulatorio: Sistema de Facturación Virtual (SFV) del SIN — Bolivia

## Las 3 modalidades (asignadas por el SIN, no elegibles)

| Modalidad | Perfil | Requisitos técnicos |
|---|---|---|
| **1. Electrónica en Línea** | Alto volumen (grandes empresas) | Certificado digital (PKCS#12 vía ADSIB/DigiCert), firma digital, SOAP + XML, transmisión en tiempo real |
| **2. Computarizada en Línea** | Volumen medio (comercios, restaurantes, servicios) | "Huella digital" (hash del XML) en vez de certificado completo, token (propio o delegado), SOAP + XML simplificado |
| **3. Portal Web** | Bajo volumen / independientes | Solo NIT + contraseña, formulario manual en el portal del SIN, sin software |

**Cambio clave 2026:** desde el 1 de enero, modalidades 1 y 2 deben transmitir **cada documento al
momento de la emisión** (ya no por lotes al final del día). Esto refuerza el valor de un servicio API
en tiempo real resiliente.

## CUFD y CUF — núcleo técnico

> **Actualización (2026-06-14):** la descripción original de esta sección (algoritmo de 6
> pasos con Verhoeff/RC4/Base64 propio) era una hipótesis sin confirmar. Una primera
> revisión usó el PDF "Anexos Técnicos SFE" (RND N° 101800000026, 21/11/2018), pero ese
> documento quedó desactualizado: el SIN publica el algoritmo vigente directamente en el
> portal `siatinfo.impuestos.gob.bo` (sección "Facturación en Línea > Algoritmos
> Utilizados > Generación CUF" / "> Algoritmo Módulo 11", con pie de página "2026" y un
> link "Versionamiento_2026"). Respecto al anexo de 2018 cambió: el campo "Número de
> Factura" pasó de 8 a 10 dígitos, se agregó el campo "Punto de Venta" (4 dígitos), y el
> CUF final incluye como sufijo el "código de control" devuelto por el servicio
> `solicitudCufd`. El esquema de 6 pasos del hallazgo original probablemente
> correspondía al "Código de Control" de 17 caracteres del **Anexo Técnico II** (Sistema
> de Facturación Virtual/SFV legado), no al CUF del SFE actual. Por eso se removieron
> `verhoeff.py`, `rc4.py` y `base64_sin.py` del adapter.

- **CUFD (Código Único de Facturación Diaria), CUIS (Código Único de Identificación del
  Sistema) y CUAPE (modalidad Prevalorado):** NO se calculan localmente. Se obtienen del
  SIN mediante los servicios web "Solicitud de CUFD" / "Solicitud de CUIS" / "Solicitud de
  CUAPE" (autenticados con usuario/password del Token Delegado), con vigencia limitada
  (CUFD: 24h). Ver `app/integrations/siat/soap_client.py`. El campo `codigo` de la
  respuesta de CUFD (`CufdResultado.codigo`) se usa además como sufijo del CUF (ver abajo).

- **CUF (Código Único de Factura) — algoritmo (portal SIN, "Generación CUF" / "Algoritmo
  Módulo 11", vigente 2026):**
  1. Concatenar los siguientes campos, cada uno con ceros a la izquierda hasta su longitud
     (total 53 dígitos):

     | Campo                            | Longitud | Detalle                          |
     |----------------------------------|----------|----------------------------------|
     | NIT del emisor                   | 13       |                                  |
     | Fecha/hora de emisión            | 17       | `yyyyMMddHHmmssSSS`              |
     | Sucursal                         | 4        | 0=Casa Matriz, 1=Sucursal 1, ... |
     | Modalidad                        | 1        | 1=Electrónica, 2=Computarizada, 3=Portal Web |
     | Tipo de emisión                  | 1        | 1=Online, 2=Offline, 3=Masiva    |
     | Tipo factura / documento ajuste  | 1        | 1=Factura con derecho a crédito fiscal, 2=sin derecho, 3=Documento de Ajuste |
     | Tipo documento sector            | 2        | 1=Factura Estándar ... 24=Nota Crédito-Débito |
     | Número de factura                | 10       |                                  |
     | Punto de venta (POS)             | 4        | 0=No corresponde, 1,2,3...n      |

  2. Calcular un dígito autoverificador Módulo 11 sobre la cadena de 53 dígitos y
     agregarlo al final (cadena de 54 dígitos). Fórmula (pesos 2-9 cíclicos de derecha a
     izquierda): `digito = suma % 11`; si `digito == 10`, el dígito final es `1`.
     Verificado contra el ejemplo oficial del portal del SIN.
  3. Codificar la cadena de 54 dígitos en Base 16 (hexadecimal).
  4. Concatenar el resultado del paso 3 con el "código de control" del servicio
     `solicitudCufd` (`CufdResultado.codigo`) -> CUF.

  Implementado y validado contra el ejemplo oficial en
  `app/integrations/siat/cuf/cuf_generator.py`.

> **Revisión de versionamiento (2026-06-14):** se revisó el historial completo de
> "Versionamiento" del portal SIN (`siatinfo.impuestos.gob.bo/index.php/versionamiento/`),
> versiones 1.0.0 (RND 102100000011, ago-2021) a 1.0.58 (jun-2026). Ninguna entrada
> menciona cambios a las páginas "Algoritmo Módulo 11", "Generación de SHA-256",
> "Algoritmo Base 16" o "Generación CUF": los cambios registrados son sobre nuevos
> documentos sector, ajustes de XML/XSD, fórmulas de cálculo de montos/ICE, y procesos de
> autorización/login. Esto sugiere que el algoritmo CUF de 53+1 dígitos (con Punto de
> Venta y sufijo `codigo_cufd`) está vigente desde la v1.0.0 y no requiere más ajustes por
> este lado.

## Otros algoritmos confirmados del portal SIN (pendientes de implementar)

- **Redondeo** (portal SIN, "Algoritmos Utilizados > Algoritmo de Redondeo"): los montos
  de facturas electrónicas en línea usan redondeo **HALF-UP** ("tradicional") a 2
  decimales (ej.: `3.14159` -> `3.14`, `3.14559` -> `3.15`). **Ojo:** `Decimal` de Python
  redondea por defecto con `ROUND_HALF_EVEN` ("banker's rounding"), no `ROUND_HALF_UP` —
  al calcular subtotales/totales en `xml_builder.py` hay que usar explícitamente
  `Decimal(...).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)`.
- **Compresión GZIP** (portal SIN, "Algoritmos Utilizados > Comprimir GZIP"): para
  "Recepción Paquete Factura" (envío por contingencia o masivo) cada archivo XML se
  comprime con GZIP (el ejemplo Java usa `GZIPOutputStream` y nombra el resultado con
  sufijo `.zip`, aunque el formato es gzip real, no zip). En Python equivale al módulo
  estándar `gzip` (`gzip.compress(...)`). Pendiente de implementar en `soap_client.py`
  cuando se aborden los métodos de paquete/masivo.

## Cómo un proveedor (tercero) opera a nombre de un contribuyente

1. El contribuyente genera un **Token Delegado** desde el portal SIAT y se lo entrega al proveedor.
2. El proveedor registra al contribuyente en el **ambiente PILOTO**.
3. El contribuyente hace **pruebas piloto** desde el portal SIAT y confirma/rechaza la
   **"Asociación de Sistemas"**.
4. Confirmar la asociación equivale a una **declaración jurada** de transición a producción.
5. Computarizada → token (propio/delegado) + huella del XML. Electrónica → token + certificado digital
   completo (PKCS#12).

## Volverse proveedor autorizado

- Requisitos base: domicilio fiscal en Bolivia, Régimen General, RNC actualizado, sin marcas de control
  activas en el Registro de Riesgo Tributario.
- Proceso de autorización incluye **Plan de Pruebas** con fases (Fase II/III = "Pruebas Piloto"):
  generación/emisión de documentos en ambiente de prueba, validación de campos, sincronización de
  catálogos, manejo de eventos significativos (contingencia).
- **Certificado digital ADSIB: Bs 70** (persona natural o jurídica), con versión gratuita para pruebas.
  El costo del certificado NO es el cuello de botella — lo es el proceso de homologación/pruebas piloto.

## Fuentes clave para revisar durante el desarrollo

- Portal SIAT: `siatinfo.impuestos.gob.bo` (modalidades, algoritmos, proceso de autorización,
  asociación de sistemas, solicitud de token delegado) — **nota:** el certificado TLS de este dominio
  no es validado por WebFetch; revisar manualmente desde navegador.
- Anexos técnicos SFE: PDF publicado en `impuestos.gob.bo/wp-content/uploads/.../ANEXOS-TECNICOS-SFE.pdf`
  (7.5MB, requiere extracción de texto con herramienta PDF adecuada — pdftoppm/poppler no disponible
  en este entorno).
- RND base: 102100000011 (ago 2021) y actualizaciones posteriores (ej. RND 102600000004, feb 2026,
  homologación de actividades económicas).
