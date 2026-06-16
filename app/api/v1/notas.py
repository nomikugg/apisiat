import uuid
from datetime import datetime, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import requerir_api_key
from app.integrations.siat.exceptions import SiatConnectionError, SiatValidationError
from app.integrations.siat.schemas import AutenticacionSolicitud, FacturaSiatItem, FacturaSiatPayload
from app.integrations.siat.orchestrator import emitir_factura_compra_venta
from app.models.facturacion import Cliente, Dosificacion, EstadoFactura, Factura, NotaCreditoDebito, TipoDocumentoFiscal
from app.models.integration import ApiKey
from app.models.tenant import PuntoVenta, Sucursal, Tenant
from app.schemas.nota import NotaCreate, NotaEmisionRequest, NotaEmisionResponse, NotaRead
from app.services.auditoria import registrar_auditoria

router = APIRouter(tags=["notas"])

_PLACEHOLDER = "PENDIENTE"


def _get_nota_or_404(db: Session, nota_id: uuid.UUID) -> NotaCreditoDebito:
    nota = db.get(NotaCreditoDebito, nota_id)
    if nota is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Nota no encontrada")
    return nota


def _construir_payload_nota(
    nota: NotaCreditoDebito,
    factura: Factura,
    tenant: Tenant,
    sucursal: Sucursal,
    punto_venta: PuntoVenta,
    cliente: Cliente,
    extra: NotaEmisionRequest,
) -> FacturaSiatPayload:
    return FacturaSiatPayload(
        nit_emisor=int(tenant.nit),
        razon_social_emisor=tenant.razon_social,
        municipio=extra.municipio,
        telefono=extra.telefono,
        numero_factura=nota.numero_nota,
        cuf=_PLACEHOLDER,
        cufd=_PLACEHOLDER,
        codigo_sucursal=sucursal.codigo_sucursal,
        direccion=_PLACEHOLDER,
        codigo_punto_venta=punto_venta.codigo_punto_venta,
        fecha_emision=datetime.now(timezone.utc),
        nombre_razon_social=cliente.nombre_razon_social,
        codigo_tipo_documento_identidad=1,
        numero_documento=cliente.numero_documento,
        complemento=cliente.complemento,
        codigo_cliente=cliente.numero_documento,
        codigo_metodo_pago=extra.codigo_metodo_pago,
        monto_total=nota.monto,
        monto_total_sujeto_iva=nota.monto,
        codigo_moneda=extra.codigo_moneda,
        tipo_cambio=extra.tipo_cambio,
        monto_total_moneda=nota.monto,
        leyenda=extra.leyenda,
        usuario=extra.usuario,
        codigo_documento_sector=nota.codigo_documento_sector,
        items=[
            FacturaSiatItem(
                actividad_economica=extra.actividad_economica,
                codigo_producto_sin=extra.codigo_producto_sin,
                codigo_producto=extra.codigo_producto,
                descripcion=nota.motivo,
                cantidad=Decimal("1"),
                unidad_medida=extra.unidad_medida,
                precio_unitario=nota.monto,
                monto_descuento=None,
                subtotal=nota.monto,
            )
        ],
    )


@router.post(
    "/facturas/{factura_id}/notas-credito-debito",
    response_model=NotaRead,
    status_code=status.HTTP_201_CREATED,
)
def crear_nota(
    factura_id: uuid.UUID,
    payload: NotaCreate,
    db: Session = Depends(get_db),
    _: ApiKey = Depends(requerir_api_key),
) -> NotaCreditoDebito:
    factura = db.get(Factura, factura_id)
    if factura is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Factura no encontrada")
    if factura.estado != EstadoFactura.VALIDADA:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Solo se pueden crear notas sobre facturas validadas",
        )
    if payload.tipo == TipoDocumentoFiscal.FACTURA:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="El tipo debe ser nota_credito o nota_debito",
        )

    dosificacion = db.get(Dosificacion, factura.dosificacion_id)
    if dosificacion.numero_actual > dosificacion.numero_final:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Dosificación agotada")
    numero_nota_sin = dosificacion.numero_actual
    dosificacion.numero_actual += 1

    nota = NotaCreditoDebito(
        factura_id=factura_id,
        tipo=payload.tipo,
        motivo=payload.motivo,
        monto=payload.monto,
        numero_nota=numero_nota_sin,
        codigo_documento_sector=payload.codigo_documento_sector,
    )
    db.add(nota)
    db.commit()
    db.refresh(nota)
    return nota


@router.get("/facturas/{factura_id}/notas-credito-debito", response_model=list[NotaRead])
def listar_notas(
    factura_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: ApiKey = Depends(requerir_api_key),
) -> list[NotaCreditoDebito]:
    factura = db.get(Factura, factura_id)
    if factura is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Factura no encontrada")
    return list(
        db.query(NotaCreditoDebito)
        .filter(NotaCreditoDebito.factura_id == factura_id)
        .order_by(NotaCreditoDebito.created_at)
        .all()
    )


@router.get("/notas/{nota_id}", response_model=NotaRead)
def obtener_nota(
    nota_id: uuid.UUID,
    db: Session = Depends(get_db),
    _: ApiKey = Depends(requerir_api_key),
) -> NotaCreditoDebito:
    return _get_nota_or_404(db, nota_id)


@router.post("/notas/{nota_id}/emitir", response_model=NotaEmisionResponse)
def emitir_nota_endpoint(
    nota_id: uuid.UUID,
    payload: NotaEmisionRequest,
    db: Session = Depends(get_db),
    api_key: ApiKey = Depends(requerir_api_key),
) -> NotaEmisionResponse:
    nota = _get_nota_or_404(db, nota_id)
    if nota.estado != EstadoFactura.PENDIENTE:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="La nota ya fue procesada")

    factura = db.get(Factura, nota.factura_id)
    tenant = db.get(Tenant, factura.tenant_id)
    sucursal = db.get(Sucursal, factura.sucursal_id)
    punto_venta = db.get(PuntoVenta, factura.punto_venta_id)
    cliente = db.get(Cliente, factura.cliente_id)

    nota_payload = _construir_payload_nota(nota, factura, tenant, sucursal, punto_venta, cliente, payload)

    try:
        resultado = emitir_factura_compra_venta(
            nota_payload,
            auth=AutenticacionSolicitud(nit=payload.nit, login=payload.login, password=payload.password),
            codigo_sistema=payload.codigo_sistema,
            codigo_ambiente=payload.codigo_ambiente,
            codigo_sucursal=sucursal.codigo_sucursal,
            codigo_punto_venta=punto_venta.codigo_punto_venta,
        )
    except SiatConnectionError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc
    except SiatValidationError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)) from exc

    estado_anterior = nota.estado.value
    nota.cuf = resultado.cuf
    nota.cufd = resultado.cufd
    if resultado.transaccion_recepcion and resultado.estado_factura == "VALIDA":
        nota.estado = EstadoFactura.VALIDADA
    else:
        nota.estado = EstadoFactura.RECHAZADA

    registrar_auditoria(
        db,
        tenant_id=factura.tenant_id,
        actor=api_key.nombre,
        accion="emision_nota",
        entidad="nota_credito_debito",
        entidad_id=nota.id,
        detalle={
            "estado_anterior": estado_anterior,
            "estado_nuevo": nota.estado.value,
            "tipo": nota.tipo.value,
            "cuf": resultado.cuf,
            "cufd": resultado.cufd,
            "codigo_recepcion": resultado.codigo_recepcion,
            "estado_factura_sin": resultado.estado_factura,
            "factura_id": str(factura.id),
            "cuf_factura_original": factura.cuf,
        },
    )
    db.commit()
    db.refresh(nota)

    return NotaEmisionResponse(
        nota=nota,
        transaccion_recepcion=resultado.transaccion_recepcion,
        codigo_recepcion=resultado.codigo_recepcion,
        estado_factura=resultado.estado_factura,
        observaciones=resultado.observaciones,
    )
