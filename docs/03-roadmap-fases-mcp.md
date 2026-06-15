# Roadmap por fases + plan de MCPs

| Fase | Qué se hace | MCP recomendado | Estado |
|---|---|---|---|
| **0. Investigación/diseño** | Regulación SIN, análisis de competidores, arquitectura | Ninguno extra (WebSearch/WebFetch) | ✅ Completado (ver docs/00, 01, 02) |
| **1. Setup del proyecto** | Repo git, scaffolding FastAPI, esquema inicial PostgreSQL, docker-compose | **GitHub MCP** (repo/issues/PRs) + **Postgres MCP** (iterar esquema) | ✅ Completado: scaffolding y esquema (commit `9aa7c19`), DB local `apisiat` en Postgres 17, MCPs de Postgres y GitHub configurados en `.mcp.json` (gitignored), repo subido a `github.com/nomikugg/apisiat` (branch `master`). |
| **2. Integración SIAT (sandbox)** | Adapter SOAP, algoritmo CUF/CUFD, contingencia | Sin MCP oficial del SIN. Opcional: MCP de CUCU como "oráculo" de referencia para comparar XML/CUF | 🟡 Algoritmo de CUF implementado y validado contra el ejemplo oficial del portal SIN 2026 (`app/integrations/siat/cuf/cuf_generator.py`); confirmado que CUFD/CUIS/CUAPE se obtienen del SIN vía SOAP (no se calculan), y que el CUF incluye como sufijo el `codigo` de CUFD. Generador XML reescrito según el XSD oficial del SIN (campos exactos de `<cabecera>`/`<detalle>`, valida con `validar_contra_xsd()`), con redondeo HALF-UP (`redondeo.py`), compresión GZIP para "Recepción Paquete Factura" (`paquetes.py`) y firma PKCS#12/XML-DSig (C14N 1.0) implementados y testeados. Pendiente: URLs WSDL de sandbox, Token Delegado, catálogos de códigos SIN — ver `docs/04-adapter-siat.md`. |
| **3. Homologación/Piloto con SIN** | Trámite ante el SIN, pruebas piloto, asociación de sistemas | Proceso manual vía portal SIAT — sin MCP aplicable | ⏳ Pendiente |
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
