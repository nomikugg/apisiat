# Investigación de mercado — Facturación electrónica como servicio en Bolivia

> Objetivo del proyecto: construir una plataforma tipo **CUCU** que actúe como intermediario entre
> sistemas de terceros (ERPs, e-commerce, POS) y el SIN/SIAT de Bolivia, cobrando por factura emitida
> (suscripción + tarifa marginal por documento).

## Competidores identificados

### CUCU (cucu.bo)
- **Modelo:** suscripción mensual + cobro por factura.
- Planes API: Junior (Bs 280/mes, Bs 0.88/factura), Semi-Senior (Bs 350/mes, Bs 0.47/factura),
  Senior (Bs 420/mes, Bs 0.32/factura). Pago inicial Bs 2,800 en todos los planes.
- También venden Odoo SaaS (cuota de facturas incluida + excedente a Bs 0.25/factura) y módulos self-hosted.
- Features: API REST + servidor **MCP** (14 herramientas para agentes IA), multi-empresa/sucursal/POS
  con una sola API key, modo contingencia automático, generación de PDF (A4 + ticket 80mm) + XML,
  firma digital (ADSIB/DigiCert), 14 tipos de documento (salud, educación, telecom, exportación, etc.).
- Doc API: `https://docs.cucu.bo` — endpoint principal `POST /api/v1/invoices`, respuesta estandarizada
  `{success, message, data, error, timestamp}`. Sandbox: `sandbox.cucu.bo`, Prod: `api.cucu.bo`.

### EERPBO / Enterprise Bolivia (enterprise.eerpbo.com)
- **Modelo:** suscripción mensual por banda de volumen (sin tarifa marginal explícita por factura).
- Planes Engine2 API: Bs 50 (1-500 fact/mes) → Bs 100 (501-1,000) → Bs 200 (1,001-5,000) →
  Bs 400 (5,001-9,999) → Corporativo a cotizar (10,000+).
- Incluye sucursales/POS ilimitados, respaldo XML, facturación offline.
- También ofrecen hosting Odoo (VPS desde Bs 350/mes) con módulo de facturación preconfigurado,
  y app "FactuFacil" para independientes. Productos propios: GUARDIUM®, PACKAGER®, SINCRONIZADOR®,
  VALIDATOR®, REPORTER®.

### Otros jugadores
- **Sintic Bolivia** (sinticbolivia.net) — API REST + librería PHP (`sinticbolivia/mono-invoices-api`)
  para SIAT v2, sin precios públicos (a cotización).
- **Gosocket** — proveedor internacional certificado por SIN, presencia en varios países LatAm.
- **EDICOM** — multinacional española, enfocada en empresas grandes/multinacionales.
- **GuruSoft (eDoc)** — autorizado bajo RND 1020-00000017 (jul 2020).
- **SisCruz** — oferta local/regional (Santa Cruz).
- **facturacion.firmadigital.bo** — portal de ADSIB para certificados/firma digital (no es competidor
  directo, es infraestructura oficial).

## Lectura del mercado / oportunidades

- El dolor real (SOAP + firma digital + CUF/CUFD + contingencia + XML normado) es lo que todos estos
  players monetizan.
- Diferenciadores ya ocupados: precio bajo por volumen (EERPBO), AI/MCP (CUCU), enterprise (Gosocket/EDICOM).
- Posibles huecos: verticales específicos (salud, exportación, ONGs), integraciones pre-hechas con
  plataformas populares en Bolivia (WooCommerce, Shopify, POS locales), modelo pay-as-you-go sin pago
  inicial alto (CUCU pide Bs 2,800 de entrada).
