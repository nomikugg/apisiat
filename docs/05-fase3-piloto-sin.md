# Fase 3: Trámite ante el SIN — Autorización de Sistema, Asociación y Piloto

Esta fase es, por normativa, un **trámite manual en el portal SIAT** que solo puede
realizar el titular del NIT con sus propias credenciales de "SIAT en Línea" (Oficina
Virtual) — no es delegable a un agente automatizado ni accesible vía API/MCP. Este
documento es la guía/checklist completa del proceso, reconstruida de
`siatinfo.impuestos.gob.bo` (secciones "Autorización de Sistemas", "Asociación de
Sistemas", "Solicitud Token Delegado", "Inicio Operaciones").

## Decisión (2026-06-15): arrancar como "Sistema Propio" con el NIT de un primer cliente piloto

Mientras se tramita el NIT de Apisiat como "Proveedor" (Régimen General + SIAT en
Línea propio, ver "Camino futuro" más abajo), el plan inmediato es registrar Apisiat
como **Sistema Informático de Facturación tipo "Propio"** bajo el NIT de un primer
cliente piloto. Esto evita el trámite de "Asociación de Sistemas" (solo aplica cuando
un NIT usa el sistema autorizado de OTRO NIT — "Proveedor") y permite iterar el
adapter contra el ambiente PILOTO real lo antes posible.

Diferencia clave vs. el camino "Proveedor": con "Sistema Propio" el Paso 1
(Autorización) y el Paso 2 (Registro de funcionalidades) se hacen directamente con el
NIT del cliente piloto, sin pasar por "Asociación de Sistemas" / "Confirmación de
Asociación" — esos dos trámites son exclusivos del modelo "Proveedor" multi-tenant.

## Requisitos previos (NIT del cliente piloto)

- NIT activo, Régimen General, con obligación tributaria IVA.
- Sin marcas de control ni contravenciones tributarias activas (Registro de Riesgo
  Tributario).
- Credenciales de "SIAT en Línea" (Oficina Virtual) de ese NIT — **quien las tenga
  (el cliente piloto, o quien tenga acceso delegado a su Oficina Virtual) es quien
  ejecuta los pasos del portal**.
- Si la modalidad asignada al cliente es **Electrónica en Línea**: solicitar un
  certificado/firma digital de prueba:
  1. Generar un CSR según los campos definidos por AGETIC.
  2. Enviarlo por correo a `siat.facturacion@impuestos.gob.bo`.
  3. El SIN devuelve el certificado firmado por SIN + AGETIC (público y privado) para
     firmar las facturas electrónicas de prueba.

## Paso 1 — Autorización de Sistema Informático de Facturación (Tipo: Propio)

1. Ingresar a PRODUCCIÓN: `https://siat.impuestos.gob.bo/launcher/` (v1) o
   `https://siat.impuestos.gob.bo/v2/launcher/` (v2), con las credenciales SIAT en
   Línea del NIT del cliente piloto.
2. v1: buscar "Gestión de Autorización de Sistemas (PILOTO)".
   v2: "Sistema de Facturación" → "Gestión de Autorización de Sistemas (PILOTO)".
3. "Autorización de Sistemas Informáticos de Facturación" → "Seguimiento de Sistemas" →
   "Nuevo Sistema".
4. Completar:
   - **Nombre Comercial**: `Apisiat`.
   - **Tipo**: `Propio` (uso del NIT del cliente piloto, no "Proveedor" — eso queda para
     el Camino futuro).
   - **Versión**: ej. `1.0.0`.
   - **Marca de Proceso Masivo**: marcar **sí** — ya está implementado
     `paquetes.py` (GZIP) para "Recepción Paquete Factura" (contingencia/masivo).
   - **Modalidad de Facturación**: la que el SIN ya tenga asignada a ese NIT
     (Electrónica o Computarizada en Línea — confirmarla con el cliente piloto).
   - **Tipo Documento Sector**: empezar con "Factura Compra Venta" (código 1, ya
     implementado en `xml_builder.py`); ampliar más adelante si el cliente emite otros
     tipos.
   - **Datos de contacto**: nombre completo, tipo/número de documento de identidad,
     complemento, correo electrónico, celular.
5. Al finalizar se genera un **reporte** con:
   - el **código de sistema** asignado,
   - parámetros constantes para el consumo de servicios,
   - las **URLs de los servicios** (WSDL) para el ambiente PILOTO.

   → Estas URLs completan `settings.siat_wsdl_facturacion` /
   `settings.siat_wsdl_codigos` (hoy vacías, ver `app/core/config.py`).

## Etapas del proceso de autorización (Fases 1–3)

- **Fase 1**: pruebas mínimas de emisión/envío de facturas al SIN, usando el código de
  sistema y las URLs de PILOTO entregadas en el Paso 1.
- **Fase 2**: "Pruebas de Funcionalidad e Inspección" — el SIN verifica las
  funcionalidades mínimas requeridas. Se coordina con la Administración Tributaria
  (puede ser presencial o virtual).
- **Fase 3**: "Pruebas Funcionales y de Carga" — responsabilidad de Apisiat/cliente, no
  controladas por el SIN, pero necesarias para garantizar la implementación antes de
  producción.

La autorización resultante es válida por **3 años**; antes de vencer hay que solicitar
"Nueva Autorización" (mismo flujo, "Seguimiento de Sistemas Informáticos").

## Paso 2 — Registro de funcionalidades del sistema (SISTEMA PROPIO)

- Portal SIAT → "Sistema de Facturación" → "Gestión de Autorización de Sistemas
  (PILOTO)" → "Seguimiento de Sistemas Informáticos" → se habilita un botón para
  registrar las características/funcionalidades del sistema, en 6 secciones:
  1. **Tipo de sector**: tipos de factura a habilitar (ej. "Factura Compra Venta").
  2. **Características**: ej. creación de puntos de venta, tipos de descuento.
  3. **Formas de pago**.
  4. **Unidades de medida** aplicables a los productos/servicios del cliente.
  5. **Tipos de moneda** (típicamente Bolivianos + Dólar).
  6. **Tipos de documento de identidad** (recomendado marcar todos).

  (Sin pasar por "Confirmación de Asociación de Sistemas" — eso es solo para
  "CONTRIBUYENTES ASOCIADOS" en el modelo Proveedor.)

## Paso 3 — Solicitud de Token Piloto

1. Portal SIAT (v2: "Sistema de Facturación") → "Gestión de Autorización de Sistemas
   Informáticos de Facturación (Piloto)" → "Token Delegado Piloto".
2. "Generar Nuevo Ticket" → elegir el NIT del cliente piloto y la duración (máx. 1 año)
   → "Solicitar".
3. Guardar este token como `Credential` del tenant piloto (ver `docs/02`).
4. **Renovación**: cuando caduca o está por caducar, inactivar el token vigente (botón
   "X") y generar uno nuevo con el mismo flujo.

**Uso del token**: va en el header HTTP `apikey: TokenApi <token>` de cada llamada SOAP
al SIN. **Ya implementado** en `app/integrations/siat/soap_client.py`
(`SiatSoapClient(wsdl_url=..., token_delegado=...)` → `_build_transport()` configura el
header en la sesión `requests` usada por `zeep`).

## Paso 4 — Inicio de Operaciones (Piloto → Producción)

1. Una vez aprobadas las pruebas piloto: menú "Inicio y Cierre de Operaciones" → "Inicio
   de Operaciones".
2. Formulario: fecha de inicio de operaciones, tipo de servicio de Internet y proveedor.
3. Al aceptar: se habilita el sistema en producción y se entregan las **URLs
   productivas** de los servicios (distintas de las de PILOTO).
4. En producción:
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
  ambiente PILOTO en cuanto haya WSDL + Token.

## Camino futuro: Apisiat como "Proveedor" multi-tenant

Cuando la entidad que opera Apisiat tenga su **propio NIT en Régimen General +
obligación IVA + acceso a SIAT en Línea**, se repite el Paso 1 con **Tipo = Proveedor**
(nueva autorización, nuevo código de sistema). A partir de ahí, **cada tenant nuevo**
de Apisiat requiere dos trámites adicionales que NO aplicaron en el camino "Propio":

- **Asociación de Sistemas** (la hace Apisiat, menú "Asociación de Sistemas
  (RND-102100000011)"): NIT del tenant, login de Apisiat, nombre/modalidad del sistema,
  **tipo de servicio = "Prestación de servicio"** (Web Service SOAP/REST — el tenant
  envía los datos y Apisiat genera/emite la factura), sectores autorizados del tenant,
  correo del tenant para confirmación. Implica que el tenant cede su firma digital
  (modalidad Electrónica) y un usuario de oficina virtual.
- **Confirmación de Asociación + Pruebas Piloto** (la hace el tenant): Portal SIAT →
  "Sistema de Facturación Versión 2" → "Confirmación de la Asociación" → "Pruebas
  Piloto" → completar el formulario de 6 secciones (igual al Paso 2 de arriba) →
  aceptar la asociación (declaración jurada de transición a producción).
- Cada tenant obtiene su **propio Token Delegado Piloto** (Paso 3 de arriba, repetido
  por tenant) y lo cede a Apisiat.

Importante: como "Proveedor", Apisiat debe implementar **todas** las funcionalidades
mínimas exigidas (no un subconjunto), y los sistemas Web/API se autorizan por separado.

## Siguiente acción

Confirmar quién tiene acceso a las credenciales de "SIAT en Línea" del NIT del primer
cliente piloto (¿el cliente directamente, o se gestiona un acceso delegado para hacer
el Paso 1?). Ese acceso es el requisito para iniciar el Paso 1 — sin él no se puede
avanzar, ya que es un trámite manual en el portal.
