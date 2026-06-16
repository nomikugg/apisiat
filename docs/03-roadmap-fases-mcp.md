# Roadmap por fases + plan de MCPs

| Fase | Qué se hace | MCP recomendado | Estado |
|---|---|---|---|
| **0. Investigación/diseño** | Regulación SIN, análisis de competidores, arquitectura | Ninguno extra (WebSearch/WebFetch) | ✅ Completado (ver docs/00, 01, 02) |
| **1. Setup del proyecto** | Repo git, scaffolding FastAPI, esquema inicial PostgreSQL, docker-compose | **GitHub MCP** (repo/issues/PRs) + **Postgres MCP** (iterar esquema) | ✅ Completado: scaffolding y esquema (commit `9aa7c19`), DB local `apisiat` en Postgres 17, MCPs de Postgres y GitHub configurados en `.mcp.json` (gitignored), repo subido a `github.com/nomikugg/apisiat` (branch `master`). |
| **2. Integración SIAT (sandbox)** | Adapter SOAP, algoritmo CUF/CUFD, contingencia | Sin MCP oficial del SIN. Opcional: MCP de CUCU como "oráculo" de referencia para comparar XML/CUF | 🟡 Algoritmo de CUF implementado y validado contra el ejemplo oficial del portal SIN 2026 (`app/integrations/siat/cuf/cuf_generator.py`); confirmado que CUFD/CUIS/CUAPE se obtienen del SIN vía SOAP (no se calculan), y que el CUF incluye como sufijo el `codigo` de CUFD. Generador XML reescrito según el XSD oficial del SIN (campos exactos de `<cabecera>`/`<detalle>`, valida con `validar_contra_xsd()`), con redondeo HALF-UP (`redondeo.py`), compresión GZIP para "Recepción Paquete Factura" (`paquetes.py`) y firma PKCS#12/XML-DSig (C14N 1.0) implementados y testeados. Pendiente: URLs WSDL de sandbox, Token Delegado, catálogos de códigos SIN — ver `docs/04-adapter-siat.md`. |
| **3. Homologación/Piloto con SIN** | Trámite ante el SIN, pruebas piloto, asociación de sistemas | Proceso manual vía portal SIAT — sin MCP aplicable | 🟡 Guía completa en `docs/05-fase3-piloto-sin.md`. Decisión 2026-06-15: arrancar registrando Apisiat como Sistema **Propio** bajo el NIT de un primer cliente piloto, mientras se tramita el NIT de Apisiat como Proveedor para el modelo multi-tenant. Para "Sistema Propio" no hay Token Delegado del portal: el adapter se autentica con NIT+login+password de Oficina Virtual del cliente piloto vía `SiatAuthClient.autenticar()` (`ServicioAutenticacionSoap` → JWT → header `Authorization: Token <jwt>`), ya implementado en `soap_client.py` junto con `solicitud_cuis`/`solicitud_cufd`/`RecepcionFactura`/`verificacionEstadoFactura`. Flujo completo validado contra un **mock local** (`app/integrations/siat/mock/`, `tests/integrations/siat/test_mock_e2e.py`). Bloqueado en: confirmar quién tiene acceso a SIAT en Línea del NIT del cliente piloto para iniciar el Paso 1 (trámite manual, no delegable). |
| **4. Producción / cobros / monitoreo** | Facturación a clientes (suscripción + por factura), alertas | Stripe MCP (cobros) + Slack MCP (alertas de contingencia) | ⏳ Pendiente |

## Notas para retomar contexto

- Todo el contexto de investigación regulatoria está en `docs/01-marco-regulatorio-sin.md`.
- La arquitectura completa (diagrama, módulos, modelo de datos, stack) está en `docs/02-arquitectura.md`.
- El análisis de competidores (CUCU, EERPBO, otros) está en `docs/00-investigacion-mercado.md`.
- Entorno de desarrollo: Python 3.13 nativo de Windows (`.venv` creado con `py -3.13`, **no** usar el
  Python de MSYS2/Git Bash porque no hay wheels de `psycopg-binary` para esa build), PostgreSQL 17
  local (DB `apisiat`), Redis vía Docker (`docker-compose.yml`).
- Esquema aplicado con Alembic (revisión `5c193cc7c26f`): tenants, sucursales, puntos de venta,
  actividades económicas, dosificaciones, CUFD cache, clientes, facturas/items, notas crédito-débito,
  contingencia, plans/subscriptions/usage_records, webhooks, audit_logs.
- Adapter SIAT (Fase 2): esqueleto en `app/integrations/siat/` con tests en
  `tests/integrations/siat/`. El PDF "Anexos Técnicos SFE" de 2018 (RND 101800000026)
  resultó estar desactualizado; el algoritmo de CUF vigente (53 dígitos + dígito Módulo 11
  + Base16 + sufijo `codigo` de CUFD) se tomó del portal `siatinfo.impuestos.gob.bo`
  (2026) y está implementado y validado contra su ejemplo oficial. CUFD/CUIS/CUAPE se
  obtienen del SIN vía SOAP (no se calculan). El generador XML "Factura Compra Venta" se
  reescribió a partir del XSD oficial del SIN (`app/integrations/siat/xsd/facturas/`),
  con campos exactos de `<cabecera>`/`<detalle>`, manejo de `xsi:nil` para campos
  opcionales y `validar_contra_xsd()`. Se agregaron además `redondeo.py` (HALF-UP,
  algoritmo SIN) y `paquetes.py` (GZIP para "Recepción Paquete Factura"), y se corrigió
  la canonicalización de `signing.firmar_xml()` a C14N 1.0 sin comentarios para alinear
  con el ejemplo Java oficial. Detalle de qué falta en `docs/04-adapter-siat.md`. Próximo
  paso: registro en ambiente PILOTO para obtener Token Delegado + URLs WSDL de sandbox.
- MCPs de Fase 1: configurados en `.mcp.json` (gitignored, contiene credenciales/tokens). Postgres MCP
  apunta a `apisiat` local y GitHub MCP tiene su Personal Access Token configurado. Remote `origin`
  configurado y con push hecho: `https://github.com/nomikugg/apisiat.git` (branch `master`).
- API REST (`app/api/v1/`): CRUD de tenants/sucursales/puntos de venta/actividades
  económicas/dosificaciones/clientes/facturas, con asignación y avance de
  `numero_factura` desde la dosificación correspondiente (commit `b8ecf3f`).
- Orquestador Factura → SIAT (mock): `app/integrations/siat/orchestrator.py` ensambla
  el flujo completo (autenticación → CUIS → CUFD → CUF → XML → huella → RecepcionFactura
  → verificacionEstadoFactura, solo modalidad Computarizada) como función reutilizable;
  `app/services/emision.py` mapea `Factura`(BD) + datos extra del SIN a
  `FacturaSiatPayload` y expone `POST /api/v1/facturas/{id}/emitir`. Los campos del SIN
  sin catálogo propio (`municipio`, `codigoMetodoPago`, `codigoProductoSin`, etc., ver
  docs/04) y las credenciales de Oficina Virtual se reciben en el body
  (`EmisionFacturaRequest`) hasta que existan catálogos/`Credential`+Vault. Se ajustó
  `facturas.cuf`/`notas_credito_debito.cuf` a `VARCHAR(100)` (revisión Alembic
  `2d913fb54643`) porque el CUF real supera los 50 caracteres del esquema inicial.
- Notas de crédito/débito: modelo `NotaCreditoDebito` extendido con `numero_nota`,
  `codigo_documento_sector` y `cufd` (migración `d56e0b94c900`). Flujo en dos pasos:
  `POST /facturas/{id}/notas-credito-debito` (crea con estado PENDIENTE, asigna número
  desde la dosificación de la factura original) y `POST /notas/{id}/emitir` (emite al SIN
  reutilizando `emitir_factura_compra_venta()` con payload de un solo ítem representando
  el ajuste). Registra `AuditLog` con `accion="emision_nota"` e incluye el CUF de la
  factura original en el detalle. Solo facturas VALIDADAS pueden generar notas.
  Endpoints de consulta: `GET /facturas/{id}/notas-credito-debito`, `GET /notas/{id}`.
- Eventos de contingencia: modelo `ContingencyEvent` ya existente en el esquema.
  Se agregaron `contingency_event_id` (FK nullable) y `emision_sin_json` (JSONB, payload
  sin credenciales) a `Factura` (migración `037ee9941b5d`). Al ocurrir
  `SiatConnectionError`, se crea o reutiliza el evento abierto para ese tenant+punto_venta
  (`app/services/contingencia.py::obtener_o_crear_evento`), la factura queda vinculada y
  el payload del SIN se persiste para reintentar. Endpoints:
  `POST /tenants/{id}/contingency-events` (apertura manual),
  `GET /tenants/{id}/contingency-events`, `GET /contingency-events/{id}`,
  `POST /contingency-events/{id}/cerrar`,
  `POST /contingency-events/{id}/reintentar` (recibe solo credenciales, reconstruye el
  payload de cada factura desde `emision_sin_json` y reintenta emitir).
- Autenticación por API keys: modelo `ApiKey` (`app/models/integration.py`) con
  `clave_hash` SHA-256 (la clave en texto plano sólo se retorna en la creación),
  `prefijo` (primeros 12 chars para identificación) y `activa`. Módulo
  `app/core/security.py` con `generar_api_key()` y dependencia FastAPI
  `requerir_api_key()` (header `X-API-Key`). Endpoints: `POST /tenants/{id}/api-keys`
  (bootstrap, sin auth), `GET /tenants/{id}/api-keys`, `DELETE /api-keys/{id}`.
  Endpoints protegidos: todos los de `facturas.py` y el de `audit-logs`. El campo
  `actor` de los `AuditLog` ahora usa `api_key.nombre` en vez del valor hardcodeado.
  Migración Alembic `bee29705505a`. Tests en `tests/api/v1/test_api_keys.py`.
- Auditoría de interacciones SIN: `app/services/auditoria.py::registrar_auditoria()`
  agrega un `AuditLog` (tabla `audit_logs`, modelo ya existente) a la sesión sin hacer
  commit. `app/services/emision.py::emitir_factura()` lo invoca tras una emisión exitosa
  (`accion="emision_factura"`, `detalle` con `estado_anterior`/`estado_nuevo`, `cuf`,
  `cufd`, `codigo_recepcion`, `estado_factura_sin`, `transaccion_recepcion`,
  `observaciones`), y `emitir_factura_endpoint()` lo invoca también en el `except
  SiatConnectionError` (caso contingencia, `detalle` incluye `error`). Nuevo endpoint
  `GET /api/v1/tenants/{tenant_id}/audit-logs` (paginado, orden descendente por
  `created_at`) para consultar el historial. `actor` queda como constante
  `"orquestador-siat"` hasta que exista autenticación de la API.
