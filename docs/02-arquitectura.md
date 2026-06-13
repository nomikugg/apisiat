# Arquitectura propuesta — Plataforma de facturación electrónica (Bolivia)

## Diagrama de alto nivel

```
┌─────────────────────────────────────────────────────────────────────┐
│                     CLIENTES (ERPs, e-commerce, POS)                  │
│         → REST API / SDKs / Webhooks / MCP (estilo CUCU)              │
└───────────────────────────────┬───────────────────────────────────────┘
                                  │
                    ┌─────────────▼─────────────┐
                    │   API Gateway / Auth       │  ← API Keys por tenant,
                    │   (rate limit, tenant id)  │    rate limiting, logging
                    └─────────────┬─────────────┘
                                  │
        ┌─────────────┬──────────┼──────────┬───────────────┐
        ▼             ▼          ▼          ▼               ▼
  ┌──────────┐  ┌───────────┐ ┌────────┐ ┌─────────┐  ┌─────────────┐
  │ Invoice  │  │ Documentos │ │ CUFD/  │ │ Billing/│  │ Webhooks &  │
  │ Service  │  │ (PDF/XML)  │ │ CUF    │ │ Metering│  │ Notif.      │
  │ (core)   │  │ Renderer   │ │ Engine │ │ (uso)   │  │ (email/SMS) │
  └────┬─────┘  └────────────┘ └───┬────┘ └─────────┘  └─────────────┘
        │                            │
        ▼                            ▼
  ┌──────────────────────────────────────────┐
  │   SIAT Adapter Layer (por modalidad)       │
  │   - SOAP client + XML builder              │
  │   - Firma digital (PKCS#12) / Huella XML   │
  │   - Manejo de Token (propio/delegado)      │
  │   - Cola de Contingencia (retry + sync)    │
  └────────────────┬───────────────────────────┘
                     │
                     ▼
            ┌──────────────────┐
            │   SIN / SIAT      │
            │ (Piloto / Prod)   │
            └──────────────────┘

  Persistencia:
  - PostgreSQL (multi-tenant, datos fiscales)
  - Redis (cache CUFD diario, colas)
  - Object Storage S3/MinIO (XML/PDF firmados)
  - Vault/KMS (certificados PKCS#12, claves de dosificación)
```

## Módulos principales

1. **Tenant/Account Management** — multi-empresa, multi-sucursal, multi-punto de venta, NIT, actividad
   económica (CAEB), modalidad asignada por el SIN, credenciales (token delegado, certificado).
2. **SIAT Adapter Layer** — pieza más sensible. Un adapter por modalidad (Electrónica/Computarizada):
   - Cliente SOAP/WSDL
   - Generador de XML por tipo de documento (14 tipos: ventas, exportación, salud, educación, etc.)
   - Motor CUF/CUFD (Verhoeff + RC4 + Base64-SIN)
   - Firma PKCS#12 o huella digital del XML
3. **Cola de Contingencia** — si SIAT no responde, la factura se emite localmente (CUF generado offline
   con CUFD vigente), se encola, y se sincroniza al SIN cuando vuelve el servicio.
4. **Document Renderer** — XML normado + PDF A4 + ticket 80mm (plantillas, Puppeteer/wkhtmltopdf).
5. **Billing/Metering** — registra cada factura emitida por tenant, aplica el plan (suscripción +
   tarifa marginal por factura, modelo estilo CUCU: Bs 0.32–0.88/factura según plan).
6. **Webhooks/Notificaciones** — eventos (factura emitida, anulada, contingencia activada).
7. **Catálogos** — sincronización periódica de catálogos SIN (unidades de medida, actividades, tipos de
   documento, monedas, formas de pago).
8. **Auditoría** — log inmutable de cada interacción con el SIN.

## Modelo de datos (entidades clave)

- `Tenant` (empresa cliente) → `Sucursal` → `PuntoVenta`
- `ActividadEconomica` (CAEB, ligada al Padrón del tenant)
- `Dosificacion` (rango de números autorizados + clave de dosificación — **secreto crítico**)
- `CUFDCache` (código diario por punto de venta, TTL 24h)
- `Factura` / `FacturaItem`, `NotaCreditoDebito`
- `Credential` (token delegado, certificado PKCS#12 cifrado — referencia a Vault, no el archivo en DB)
- `Plan`, `Subscription`, `UsageRecord` (para el cobro por factura)
- `ContingencyEvent`, `WebhookEndpoint`, `AuditLog`

## Stack recomendado

| Capa | Recomendación | Por qué |
|---|---|---|
| Core API + adapter SIAT | **Python + FastAPI** | `zeep` (SOAP/WSDL) maduro para SIN; `cryptography`/`pyOpenSSL` para PKCS#12 |
| Workers (cola/contingencia) | **Celery o RQ + Redis** | Reintentos, sincronización diferida, generación de CUFD |
| Base de datos | **PostgreSQL** (RLS por tenant) | Multi-tenant estándar, transaccional para datos fiscales |
| Storage XML/PDF | **S3-compatible (MinIO si self-hosted)** | Retención legal de documentos |
| Secrets (certificados, claves de dosificación) | **Vault / KMS** | Activo más sensible del sistema — nunca en DB plana |
| Dashboard merchant/admin | **Next.js** | Configuración, reportes, plan de facturación |
| API pública | **REST + Webhooks**, MCP opcional luego | Igual que CUCU/EERPBO |

## Consideración de seguridad crítica

La **clave de dosificación** y los **certificados PKCS#12** de cada tenant permiten firmar facturas en
su nombre ante el SIN. Si se filtran, alguien podría emitir facturas fiscalmente válidas a nombre de
los clientes. Deben:
- Cifrarse en reposo con KMS/Vault, nunca en variables de entorno ni columnas planas.
- Tener acceso auditado (quién/qué proceso lo usó y cuándo).
- Soportar rotación y revocación si un tenant se da de baja.
