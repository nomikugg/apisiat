# Roadmap por fases + plan de MCPs

| Fase | Qué se hace | MCP recomendado | Estado |
|---|---|---|---|
| **0. Investigación/diseño** | Regulación SIN, análisis de competidores, arquitectura | Ninguno extra (WebSearch/WebFetch) | ✅ Completado (ver docs/00, 01, 02) |
| **1. Setup del proyecto** | Repo git, scaffolding FastAPI, esquema inicial PostgreSQL, docker-compose | **GitHub MCP** (repo/issues/PRs) + **Postgres MCP** (iterar esquema) | 🔄 En curso |
| **2. Integración SIAT (sandbox)** | Adapter SOAP, algoritmo CUF/CUFD, contingencia | Sin MCP oficial del SIN. Opcional: MCP de CUCU como "oráculo" de referencia para comparar XML/CUF | ⏳ Pendiente |
| **3. Homologación/Piloto con SIN** | Trámite ante el SIN, pruebas piloto, asociación de sistemas | Proceso manual vía portal SIAT — sin MCP aplicable | ⏳ Pendiente |
| **4. Producción / cobros / monitoreo** | Facturación a clientes (suscripción + por factura), alertas | Stripe MCP (cobros) + Slack MCP (alertas de contingencia) | ⏳ Pendiente |

## Notas para retomar contexto

- Todo el contexto de investigación regulatoria está en `docs/01-marco-regulatorio-sin.md`.
- La arquitectura completa (diagrama, módulos, modelo de datos, stack) está en `docs/02-arquitectura.md`.
- El análisis de competidores (CUCU, EERPBO, otros) está en `docs/00-investigacion-mercado.md`.
- Próximo paso inmediato: scaffolding FastAPI + docker-compose (Postgres/Redis) + esquema inicial
  basado en las entidades de `docs/02-arquitectura.md`.
