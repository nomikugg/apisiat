# apisiat

Plataforma de facturación electrónica para Bolivia (integración SIN/SIAT), estilo CUCU/EERPBO:
API REST + cobro por suscripción + tarifa marginal por factura emitida.

## Documentación

- [`docs/00-investigacion-mercado.md`](docs/00-investigacion-mercado.md) — análisis de competidores
  (CUCU, EERPBO, otros) y modelos de precio.
- [`docs/01-marco-regulatorio-sin.md`](docs/01-marco-regulatorio-sin.md) — modalidades SFV, algoritmo
  CUF/CUFD, proceso de homologación ante el SIN.
- [`docs/02-arquitectura.md`](docs/02-arquitectura.md) — arquitectura, módulos, modelo de datos, stack.
- [`docs/03-roadmap-fases-mcp.md`](docs/03-roadmap-fases-mcp.md) — roadmap por fases y plan de MCPs.

## Setup local (Windows)

Requisitos: Python 3.12+ (build nativo de Windows, no MSYS2 — usar `py -3.13`), PostgreSQL local,
Docker (para Redis).

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"

# Copiar .env.example a .env y ajustar DATABASE_URL con tus credenciales locales de Postgres
copy .env.example .env

# Crear la base de datos (una vez)
# psql -U postgres -c "CREATE DATABASE apisiat;"

# Aplicar migraciones
.\.venv\Scripts\python.exe -m alembic upgrade head

# Redis (opcional en esta fase, vía Docker)
docker compose up -d

# Levantar la API
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

Verificar: `GET http://localhost:8000/api/v1/health` → `{"status": "ok"}`.

## Estructura

```
app/
├── main.py            # FastAPI app
├── core/              # config y conexión a DB
├── models/            # SQLAlchemy: tenants, facturación, billing, auditoría
└── api/v1/            # routers REST
alembic/               # migraciones de esquema
docs/                  # investigación y arquitectura
```
