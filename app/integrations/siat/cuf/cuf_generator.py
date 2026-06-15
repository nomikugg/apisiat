"""
Generación del CUF (Código Único de Factura).

Fuente: portal del SIN (siatinfo.impuestos.gob.bo), "Facturación en Línea >
Algoritmos Utilizados > Generación CUF" y "> Algoritmo Módulo 11" (vigente
2026). Esta especificación reemplaza a la tabla de campos del Anexo Técnico I
de la RND N° 101800000026 (2018): el campo "Número de Factura" pasó de 8 a 10
dígitos y se agregó el campo "Punto de Venta" (4 dígitos).

El algoritmo es:

  1. Concatenar los siguientes campos, cada uno completado con ceros a la
     izquierda hasta la longitud indicada (total 53 dígitos):

     | Campo                          | Longitud | Detalle                       |
     |--------------------------------|----------|--------------------------------|
     | NIT del emisor                 | 13       |                                |
     | Fecha/hora de emisión          | 17       | `yyyyMMddHHmmssSSS`            |
     | Sucursal                       | 4        | 0=Casa Matriz, 1=Sucursal 1... |
     | Modalidad                      | 1        | 1=Electrónica, 2=Computarizada,|
     |                                |          | 3=Portal Web                   |
     | Tipo de emisión                | 1        | 1=Online, 2=Offline, 3=Masiva  |
     | Tipo factura / documento ajuste| 1        | 1=Factura con derecho a crédito|
     |                                |          | fiscal, 2=sin derecho a crédito|
     |                                |          | fiscal, 3=Documento de Ajuste  |
     | Tipo documento sector          | 2        | 1=Factura Estándar ... 24=Nota |
     |                                |          | Crédito-Débito                 |
     | Número de factura              | 10       |                                |
     | Punto de venta (POS)           | 4        | 0=No corresponde, 1,2,3...n    |

  2. Calcular el dígito autoverificador Módulo 11 sobre la cadena de 53
     dígitos y agregarlo al final (cadena de 54 dígitos). Fórmula (pesos
     2-9 cíclicos de derecha a izquierda): `digito = suma % 11`; si
     `digito == 10`, el dígito final es `1`.
  3. Codificar la cadena de 54 dígitos en Base 16 (hexadecimal).
  4. Concatenar el resultado del paso 3 con el "código de control" obtenido
     del Servicio Web "Solicitud de CUFD" (`CufdResultado.codigo_control`,
     campo `codigoControl` de la respuesta de `solicitudCufd` — distinto de
     `codigoCUFD`, que es el valor que va en `<cufd>` de la factura) -> CUF.

Validado contra el ejemplo oficial de la página "Generación CUF": con NIT
123456789, fecha/hora 2019-01-13 16:37:21.231, sucursal 0, modalidad 1, tipo
de emisión 1, tipo factura/documento ajuste 1, tipo documento sector 01,
número de factura 1, POS 0 y código de control "A19E23EF34124CD", el CUF
resultante es "8727F63A15F8976591FDDE5B387C5D015A29E06A1A19E23EF34124CD".

Nota sobre el paso 3 (Base 16): el SIN documenta ese paso con
`BigInteger.Parse(cadena).ToString("X")` (C#), que antepone un "0" cuando el
primer nibble es >= 8 (para que `Parse(..., HexNumber)` no lo interprete como
negativo en el round-trip). El ejemplo oficial ("8727F63A...", empieza con
"8") NO tiene ese "0" extra, y `format(int(cadena_54), "X")` en Python
(que tampoco lo agrega) coincide exactamente con ese ejemplo -> no agregar
ceros extra para "imitar" el comportamiento de BigInteger en C#.
"""

from datetime import datetime

_LONGITUD_NIT = 13
_LONGITUD_FECHA_HORA = 17
_LONGITUD_SUCURSAL = 4
_LONGITUD_MODALIDAD = 1
_LONGITUD_TIPO_EMISION = 1
_LONGITUD_TIPO_FACTURA_DOCUMENTO_AJUSTE = 1
_LONGITUD_TIPO_DOCUMENTO_SECTOR = 2
_LONGITUD_NUMERO_FACTURA = 10
_LONGITUD_PUNTO_VENTA = 4
_LONGITUD_CAMPOS = (
    _LONGITUD_NIT
    + _LONGITUD_FECHA_HORA
    + _LONGITUD_SUCURSAL
    + _LONGITUD_MODALIDAD
    + _LONGITUD_TIPO_EMISION
    + _LONGITUD_TIPO_FACTURA_DOCUMENTO_AJUSTE
    + _LONGITUD_TIPO_DOCUMENTO_SECTOR
    + _LONGITUD_NUMERO_FACTURA
    + _LONGITUD_PUNTO_VENTA
)


def _digito_verificador_modulo11(digitos: str) -> int:
    """Dígito autoverificador Módulo 11 (pesos 2-9 cíclicos, de derecha a izquierda)."""
    factor = 2
    suma = 0
    for caracter in reversed(digitos):
        suma += int(caracter) * factor
        factor = 2 if factor == 9 else factor + 1
    digito = suma % 11
    return 1 if digito == 10 else digito


def generar_cuf(
    *,
    nit: int,
    fecha_hora_emision: datetime,
    sucursal: int,
    modalidad: int,
    tipo_emision: int,
    tipo_factura_documento_ajuste: int,
    tipo_documento_sector: int,
    numero_factura: int,
    punto_venta: int,
    codigo_control: str,
) -> str:
    """Calcula el CUF (Código Único de Factura) para una factura."""
    milisegundos = fecha_hora_emision.microsecond // 1000
    campos = (
        f"{nit:0{_LONGITUD_NIT}d}"
        f"{fecha_hora_emision:%Y%m%d%H%M%S}{milisegundos:03d}"
        f"{sucursal:0{_LONGITUD_SUCURSAL}d}"
        f"{modalidad:0{_LONGITUD_MODALIDAD}d}"
        f"{tipo_emision:0{_LONGITUD_TIPO_EMISION}d}"
        f"{tipo_factura_documento_ajuste:0{_LONGITUD_TIPO_FACTURA_DOCUMENTO_AJUSTE}d}"
        f"{tipo_documento_sector:0{_LONGITUD_TIPO_DOCUMENTO_SECTOR}d}"
        f"{numero_factura:0{_LONGITUD_NUMERO_FACTURA}d}"
        f"{punto_venta:0{_LONGITUD_PUNTO_VENTA}d}"
    )
    if len(campos) != _LONGITUD_CAMPOS:
        raise ValueError(
            f"La concatenación de campos debe tener {_LONGITUD_CAMPOS} dígitos, "
            f"tiene {len(campos)}: {campos!r}"
        )
    digito = _digito_verificador_modulo11(campos)
    cadena_54 = f"{campos}{digito}"
    return format(int(cadena_54), "X") + codigo_control
