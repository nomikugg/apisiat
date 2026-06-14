# Roadmap por fases + plan de MCPs

| Fase | Qué se hace | MCP recomendado | Estado |
|---|---|---|---|
| **0. Investigación/diseño** | Regulación SIN, análisis de competidores, arquitectura | Ninguno extra (WebSearch/WebFetch) | ✅ Completado (ver docs/00, 01, 02) |
| **1. Setup del proyecto** | Repo git, scaffolding FastAPI, esquema inicial PostgreSQL, docker-compose | **GitHub MCP** (repo/issues/PRs) + **Postgres MCP** (iterar esquema) | ✅ Completado: scaffolding y esquema (commit `9aa7c19`), DB local `apisiat` en Postgres 17, MCPs de Postgres y GitHub configurados en `.mcp.json` (gitignored), repo subido a `github.com/nomikugg/apisiat` (branch `master`). |
| **2. Integración SIAT (sandbox)** | Adapter SOAP, algoritmo CUF/CUFD, contingencia | Sin MCP oficial del SIN. Opcional: MCP de CUCU como "oráculo" de referencia para comparar XML/CUF | ⏳ Pendiente |
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
- Próximo paso: definir el adapter SIAT (Fase 2) — cliente SOAP, generador XML, algoritmo CUF/CUFD,
  firma digital/huella.
- MCPs de Fase 1: configurados en `.mcp.json` (gitignored, contiene credenciales/tokens). Postgres MCP
  apunta a `apisiat` local y GitHub MCP tiene su Personal Access Token configurado. Remote `origin`
  configurado y con push hecho: `https://github.com/nomikugg/apisiat.git` (branch `master`).
