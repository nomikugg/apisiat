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

> **Actualización:** la descripción original de esta sección (algoritmo de 6 pasos con
> Verhoeff/RC4/Base64 propio) era una hipótesis sin confirmar. Se obtuvo el PDF oficial
> "Anexos Técnicos SFE" (RND N° 101800000026, 21/11/2018) y el algoritmo real es mucho
> más simple — ver abajo. El esquema de 6 pasos probablemente correspondía al "Código de
> Control" de 17 caracteres del **Anexo Técnico II** (Sistema de Facturación Virtual /SFV
> legado, modalidades Computarizada/Electrónica Web/Por Ciclos en proceso de
> discontinuación), no al CUF del SFE actual. Por eso se removieron `verhoeff.py`,
> `rc4.py` y `base64_sin.py` del adapter.

- **CUFD (Código Único de Facturación Diaria), CUIS (Código Único de Identificación del
  Sistema) y CUAPE (modalidad Prevalorado):** NO se calculan localmente. Se obtienen del
  SIN mediante los servicios web "Solicitud de CUFD" / "Solicitud de CUIS" / "Solicitud de
  CUAPE" (autenticados con usuario/password del Token Delegado), con vigencia limitada
  (CUFD: 24h). Ver `app/integrations/siat/soap_client.py`.

- **CUF (Código Único de Factura) — algoritmo (Anexo Técnico I, "PROCESO DE GENERACIÓN
  CUF"):**
  1. Concatenar los siguientes campos, cada uno con ceros a la izquierda hasta su longitud
     (total 47 dígitos):

     | Campo                   | Longitud | Detalle                                  |
     |-------------------------|----------|------------------------------------------|
     | NIT del emisor          | 13       |                                            |
     | Fecha/hora de emisión   | 17       | `yyyymmddhhmmssmmm`                       |
     | Sucursal                | 4        | 0=Casa Matriz, 1=Sucursal 1, ...           |
     | Modalidad               | 1        | 1=Electrónica, 2=Computarizada, 3=Portal Web, 4=Prevalorado Electrónico |
     | Tipo de emisión         | 1        | 0=Online, 1=Offline                       |
     | Código documento fiscal | 1        | 1=Factura, 2=Nota Débito/Crédito, 3=Nota Fiscal, 4=Documento Equivalente |
     | Tipo documento sector   | 2        | 1=Factura Estándar ... 22=Boleto Aéreo     |
     | Número de factura       | 8        |                                            |

  2. Calcular un dígito autoverificador "Base 11" sobre la cadena de 47 dígitos y agregarlo
     al final (cadena de 48 dígitos). El anexo no detalla el algoritmo más allá del nombre;
     se implementó el Módulo 11 estándar (pesos 2-9 cíclicos), pendiente de validar contra
     casos de prueba oficiales.
  3. Codificar la cadena de 48 dígitos en Base 16 (hexadecimal) -> CUF.

  Implementado en `app/integrations/siat/cuf/cuf_generator.py`.

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
