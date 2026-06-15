# Fase 3: Trámite ante el SIN — Autorización de Sistema, Asociación y Piloto

Esta fase es, por normativa, un **trámite manual en el portal SIAT** que solo puede
realizar el titular del NIT con sus propias credenciales de "SIAT en Línea" (Oficina
Virtual) — no es delegable a un agente automatizado ni accesible vía API/MCP. Este
documento es la guía/checklist completa del proceso, reconstruida de
`siatinfo.impuestos.gob.bo` (secciones "Autorización de Sistemas", "Asociación de
Sistemas", "Solicitud Token Delegado", "Inicio Operaciones").

## Resumen: 3 trámites distintos

1. **Autorización de Sistema Informático de Facturación** (una sola vez, lo hace
   **Apisiat** como "Proveedor").
2. **Asociación de Sistemas** (una vez **por cada tenant/contribuyente** que use
   Apisiat — lo inicia Apisiat y lo confirma el cliente).
3. **Inicio de Operaciones** (transición Piloto → Producción, una vez por tenant tras
   las pruebas piloto).

## Requisitos previos (NIT de Apisiat como Proveedor)

- NIT activo, Régimen General, con obligación tributaria IVA.
- Sin marcas de control ni contravenciones tributarias activas (Registro de Riesgo
  Tributario).
- Credenciales de "SIAT en Línea" (Oficina Virtual) de ese NIT.
- Si se ofrecerá modalidad **Electrónica en Línea**: solicitar un certificado/firma
  digital de prueba:
  1. Generar un CSR según los campos definidos por AGETIC.
  2. Enviarlo por correo a `siat.facturacion@impuestos.gob.bo`.
  3. El SIN devuelve el certificado firmado por SIN + AGETIC (público y privado) para
     firmar las facturas electrónicas de prueba.

**Esto es lo que bloquea hoy el avance**: confirmar si la entidad que operará como
"Proveedor" (Apisiat) ya tiene NIT en Régimen General + acceso a SIAT en Línea, o si
ese trámite (ante Impuestos Nacionales, independiente del portal SIAT) es el primer
paso.

## Paso 1 — Autorización de Sistema Informático de Facturación (Apisiat = Proveedor)

1. Ingresar a PRODUCCIÓN: `https://siat.impuestos.gob.bo/launcher/` (v1) o
   `https://siat.impuestos.gob.bo/v2/launcher/` (v2), con credenciales SIAT en Línea.
2. v1: buscar "Gestión de Autorización de Sistemas (PILOTO)".
   v2: "Sistema de Facturación" → "Gestión de Autorización de Sistemas (PILOTO)".
3. "Autorización de Sistemas Informáticos de Facturación" → "Seguimiento de Sistemas" →
   "Nuevo Sistema".
4. Completar:
   - **Nombre Comercial**: `Apisiat`.
   - **Tipo**: `Proveedor` (no "uso propio" — Apisiat factura para múltiples NITs/tenants).
   - **Versión**: ej. `1.0.0`.
   - **Marca de Proceso Masivo**: marcar **sí** — ya está implementado
     `paquetes.py` (GZIP) para "Recepción Paquete Factura" (contingencia/masivo), y el
     SIN exige pruebas adicionales de envío por paquete para sistemas tipo Proveedor.
   - **Modalidad de Facturación**: Electrónica y/o Computarizada en Línea, según a qué
     tipo de cliente se ofrecerá el servicio primero (ver `docs/04`).
   - **Tipo Documento Sector**: empezar con "Factura Compra Venta" (código 1, ya
     implementado en `xml_builder.py`); se pueden agregar otros tipos de documento
     sector más adelante.
   - **Datos de contacto**: nombre completo, tipo/número de documento de identidad,
     complemento, correo electrónico, celular.
5. Al finalizar se genera un **reporte** con:
   - el **código de sistema** asignado,
   - parámetros constantes para el consumo de servicios,
   - las **URLs de los servicios** (WSDL) para el ambiente PILOTO.

   → Estas URLs son las que completan `settings.siat_wsdl_facturacion` /
   `settings.siat_wsdl_codigos` (hoy vacías, ver `app/core/config.py`).

> **Nota**: los sistemas tipo "Proveedor" deben implementar **todas** las
> funcionalidades mínimas exigidas (no un subconjunto). Sistemas Web y API se autorizan
> por separado — como Apisiat es solo API/backend, correspondería la autorización de
> tipo API.

## Etapas del proceso de autorización (Fases 1–3)

- **Fase 1**: pruebas mínimas de emisión/envío de facturas al SIN, usando el código de
  sistema y las URLs de PILOTO entregadas en el Paso 1.
- **Fase 2**: "Pruebas de Funcionalidad e Inspección" — el SIN verifica las
  funcionalidades mínimas requeridas. Se coordina con la Administración Tributaria
  (puede ser presencial o virtual).
- **Fase 3**: "Pruebas Funcionales y de Carga" — responsabilidad de Apisiat, no
  controladas por el SIN, pero necesarias para garantizar la implementación antes de
  producción.

La autorización resultante es válida por **3 años**; antes de vencer hay que solicitar
"Nueva Autorización" (mismo flujo, "Seguimiento de Sistemas Informáticos").

## Paso 2 — Registro de funcionalidades del sistema

- Portal SIAT → "Sistema de Facturación" → "Gestión de Autorización de Sistemas
  (PILOTO)" → "Seguimiento de Sistemas Informáticos" → botón para registrar las
  características/funcionalidades del sistema (sectores, formas de pago, unidades de
  medida, monedas, tipos de documento de identidad, etc. — ver el detalle del
  formulario de 6 secciones más abajo, en el Paso 4).

## Paso 3 — Asociación de Sistemas (por cada tenant/cliente de Apisiat)

Lo hace **Apisiat**, desde su sesión en PRODUCCIÓN, menú "Asociación de Sistemas
(RND-102100000011)":

- **NIT del contribuyente** (cliente de Apisiat) — debe estar activo.
- **Login del usuario** con el que Apisiat ingresa al sistema del SIN.
- **Nombre del sistema** que se está asociando (Apisiat).
- **Modalidad** a la que se asocia (Electrónica/Computarizada).
- **Tipo de servicio** — para Apisiat corresponde **"Prestación de servicio"** (Web
  Service SOAP/REST: el sistema del contribuyente solo envía los datos de facturación
  necesarios y Apisiat genera/emite la factura digital). Implicaciones:
  - El contribuyente debe **ceder su firma digital** (modalidad Electrónica) —
    almacenada como `Credential` (PKCS#12 cifrado en Vault, ver `docs/02`).
  - El contribuyente debe ceder un **usuario de oficina virtual**.
  - Se debe definir el **tiempo de prestación del servicio**.
- **Sectores** a asociar (solo los que el contribuyente ya tiene autorizados).
- **Correo electrónico del contribuyente** — recibe el aviso para confirmar la
  asociación.

## Paso 4 — Confirmación de Asociación + Pruebas Piloto (lo hace el tenant/cliente)

1. El contribuyente entra al Portal SIAT → "Sistema de Facturación Versión 2" →
   "Confirmación de la Asociación".
2. Ve la lista de sistemas (Apisiat) que asociaron su NIT; solo está habilitada la
   opción **"Pruebas Piloto"**.
3. Al seleccionarla se genera un documento con las especificaciones de las pruebas.
4. El contribuyente debe completar el formulario de configuración (6 secciones):
   1. **Tipo de sector**: tipos de factura a habilitar (ej. "Factura Compra Venta").
   2. **Características**: ej. creación de puntos de venta, tipos de descuento.
   3. **Formas de pago**.
   4. **Unidades de medida** aplicables a sus productos/servicios.
   5. **Tipos de moneda** (típicamente Bolivianos + Dólar).
   6. **Tipos de documento de identidad** (recomendado marcar todos).
5. "Continuar" → si está conforme, **confirma/acepta la asociación** → se emite la
   autorización de asociación. Aceptar equivale a una **declaración jurada** de
   transición a producción.

## Paso 5 — Solicitud de Token Delegado Piloto (lo hace el tenant/cliente)

1. Portal SIAT (v2: "Sistema de Facturación") → "Gestión de Autorización de Sistemas
   Informáticos de Facturación (Piloto)" → "Token Delegado Piloto".
2. "Generar Nuevo Ticket" → elegir el NIT correspondiente y la duración (máx. 1 año) →
   "Solicitar".
3. El contribuyente **cede este token a Apisiat** (guardarlo como `Credential` por
   tenant, ver `docs/02`).
4. **Renovación**: cuando caduca o está por caducar, inactivar el token vigente (botón
   "X") y generar uno nuevo con el mismo flujo.

**Uso del token**: va en el header HTTP `apikey: TokenApi <token>` de cada llamada SOAP
al SIN. **Ya implementado** en `app/integrations/siat/soap_client.py`
(`SiatSoapClient(wsdl_url=..., token_delegado=...)` → `_build_transport()` configura el
header en la sesión `requests` usada por `zeep`).

## Paso 6 — Inicio de Operaciones (Piloto → Producción, por tenant)

1. Una vez aprobadas las pruebas piloto: menú "Inicio y Cierre de Operaciones" → "Inicio
   de Operaciones".
2. Formulario: fecha de inicio de operaciones, tipo de servicio de Internet y proveedor.
3. Al aceptar: se habilita el sistema en producción y se entregan las **URLs
   productivas** de los servicios (distintas de las de PILOTO).
4. En producción, por cada tenant:
   - Obtener un **nuevo Token** (de producción, distinto al de Piloto).
   - Obtener el **CUIS** (Código Único de Inicio de Sistemas) — una sola vez, o cuando
     venza.
   - Obtener el **CUFD** diariamente (ya modelado: `CufdSolicitud`/`CufdResultado` en
     `schemas.py`, cache con TTL 24h en `docs/02`).
   - **Sincronizar catálogos** diariamente (actividades, sectores, productos, fecha/hora,
     documento sector) — pendiente implementar "Sincronización de Códigos y Catálogos"
     (ver `docs/04`, pendiente de `codigoMoneda`/`codigoMetodoPago`/etc.).
   - Realizar la **homologación de productos**.
   - Definir **puntos de venta** si corresponde.

## Qué queda listo en el código para cuando se complete el trámite

- `app/integrations/siat/soap_client.py`: `SiatSoapClient` ya acepta `token_delegado`
  y lo envía como header `apikey: TokenApi <token>` (requisito documentado del SIN).
  Tests en `tests/integrations/siat/test_soap_client.py`.
- `app/core/config.py`: `siat_wsdl_facturacion` / `siat_wsdl_codigos` — completar con
  las URLs entregadas en el **Paso 1** (reporte de "Nuevo Sistema").
- Generador XML (`xml_builder.py`), CUF (`cuf/cuf_generator.py`), redondeo, GZIP, firma
  XML-DSig: implementados y testeados (ver `docs/04`), listos para probarse contra el
  ambiente PILOTO en cuanto haya WSDL + Token Delegado.

## Bloqueante y siguiente paso

Todo lo anterior depende de que la entidad que operará como "Proveedor" (Apisiat) tenga
NIT activo en Régimen General + obligación IVA + acceso a "SIAT en Línea". Sin eso no se
puede iniciar el Paso 1. **Pendiente confirmar con el usuario** el estado de ese
registro (NIT propio, o usar el NIT de un primer cliente piloto como "sistema propio"
mientras se tramita el NIT de Apisiat como Proveedor).
