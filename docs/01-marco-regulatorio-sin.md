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

- **CUFD (Código Único de Facturación Diaria):** se solicita al SIN una vez al día por punto de venta,
  vigencia 24h. Obligatorio en todas las modalidades online.
- **CUF (Código Único de Factura):** se genera por cada factura, combinando datos de la transacción
  (NIT cliente, fecha, monto, número de factura/autorización) + el **Código de Control**.
- **Código de Control — algoritmo de 6 pasos:**
  1. Agregar 2 dígitos Verhoeff a factura/NIT/fecha/monto; sumar valores; agregar 5 dígitos Verhoeff más.
  2. Extraer los últimos 5 dígitos Verhoeff; usarlos para extraer subcadenas de la "clave de dosificación".
  3. Concatenar subcadenas extraídas con los campos originales; cifrar con RC4 usando la clave de
     dosificación + los 5 dígitos Verhoeff.
  4. Convertir el string cifrado a valores ASCII; distribuir en 5 sumas parciales.
  5. Calcular producto (total × sumas parciales ÷ posiciones de subcadena); convertir a Base64 (SIN usa
     diccionario propio de 64 caracteres, sin O/l/0/1).
  6. Aplicar RC4 al resultado Base64 usando la clave combinada.
  - Formato final: alfanumérico hasta 10 caracteres, en pares separados por guiones
    (ej. `6A-DC-53-05-14`).
  - El SIN publica ~5,000 casos de prueba (Excel/TXT) para validar la implementación — entregable
    obligatorio antes de homologar.

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
