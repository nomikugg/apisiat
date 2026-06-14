"""
Generación del CUF (Código Único de Factura).

Fuente: RND N° 101800000026 (21/11/2018), Anexo Técnico I, sección
"PROCESO DE GENERACIÓN CUF". El algoritmo es:

  1. Concatenar los siguientes campos, cada uno completado con ceros a la
     izquierda hasta la longitud indicada (total 47 dígitos):

     | Campo                   | Longitud | Detalle                                |
     |-------------------------|----------|----------------------------------------|
     | NIT del emisor          | 13       |                                          |
     | Fecha/hora de emisión   | 17       | `yyyymmddhhmmssmmm`                     |
     | Sucursal                | 4        | 0=Casa Matriz, 1=Sucursal 1, ...        |
     | Modalidad               | 1        | 1=Electrónica, 2=Computarizada,         |
     |                         |          | 3=Portal Web, 4=Prevalorado Electrónico |
     | Tipo de emisión         | 1        | 0=Online, 1=Offline                     |
     | Código documento fiscal | 1        | 1=Factura, 2=Nota Débito/Crédito,       |
     |                         |          | 3=Nota Fiscal, 4=Documento Equivalente  |
     | Tipo documento sector   | 2        | 1=Factura Estándar ... 22=Boleto Aéreo  |
     | Número de factura       | 8        |                                          |

  2. Calcular un dígito autoverificador "Base 11" sobre la cadena de 47
     dígitos y agregarlo al final (cadena de 48 dígitos).
  3. Codificar la cadena de 48 dígitos en Base 16 (hexadecimal) -> CUF.

El anexo no detalla el algoritmo del dígito "Base 11" más allá de su nombre.
Aquí se usa el algoritmo de Módulo 11 estándar para dígitos verificadores en
Bolivia (pesos 2-9 cíclicos de derecha a izquierda, con 10->1 y 11->0), que es
de conocimiento público y produce siempre un único dígito (0-9). Pendiente de
validar contra los casos de prueba oficiales del SIN (ver docs/04-adapter-siat.md).
"""

from datetime import datetime

_LONGITUD_NIT = 13
_LONGITUD_FECHA_HORA = 17
_LONGITUD_SUCURSAL = 4
_LONGITUD_MODALIDAD = 1
_LONGITUD_TIPO_EMISION = 1
_LONGITUD_CODIGO_DOCUMENTO_FISCAL = 1
_LONGITUD_TIPO_DOCUMENTO_SECTOR = 2
_LONGITUD_NUMERO_FACTURA = 8
_LONGITUD_CAMPOS = (
    _LONGITUD_NIT
    + _LONGITUD_FECHA_HORA
    + _LONGITUD_SUCURSAL
    + _LONGITUD_MODALIDAD
    + _LONGITUD_TIPO_EMISION
    + _LONGITUD_CODIGO_DOCUMENTO_FISCAL
    + _LONGITUD_TIPO_DOCUMENTO_SECTOR
    + _LONGITUD_NUMERO_FACTURA
)


def _digito_verificador_base11(digitos: str) -> int:
    """Dígito verificador Módulo 11 (pesos 2-9 cíclicos, de derecha a izquierda)."""
    factor = 2
    suma = 0
    for caracter in reversed(digitos):
        suma += int(caracter) * factor
        factor = 2 if factor == 9 else factor + 1
    resto = 11 - (suma % 11)
    if resto == 10:
        return 1
    if resto == 11:
        return 0
    return resto


def generar_cuf(
    *,
    nit: int,
    fecha_hora_emision: datetime,
    sucursal: int,
    modalidad: int,
    tipo_emision: int,
    codigo_documento_fiscal: int,
    tipo_documento_sector: int,
    numero_factura: int,
) -> str:
    """Calcula el CUF (Código Único de Factura) para una factura."""
    milisegundos = fecha_hora_emision.microsecond // 1000
    campos = (
        f"{nit:0{_LONGITUD_NIT}d}"
        f"{fecha_hora_emision:%Y%m%d%H%M%S}{milisegundos:03d}"
        f"{sucursal:0{_LONGITUD_SUCURSAL}d}"
        f"{modalidad:0{_LONGITUD_MODALIDAD}d}"
        f"{tipo_emision:0{_LONGITUD_TIPO_EMISION}d}"
        f"{codigo_documento_fiscal:0{_LONGITUD_CODIGO_DOCUMENTO_FISCAL}d}"
        f"{tipo_documento_sector:0{_LONGITUD_TIPO_DOCUMENTO_SECTOR}d}"
        f"{numero_factura:0{_LONGITUD_NUMERO_FACTURA}d}"
    )
    if len(campos) != _LONGITUD_CAMPOS:
        raise ValueError(
            f"La concatenación de campos debe tener {_LONGITUD_CAMPOS} dígitos, "
            f"tiene {len(campos)}: {campos!r}"
        )
    digito = _digito_verificador_base11(campos)
    cadena_48 = f"{campos}{digito}"
    return format(int(cadena_48), "X")
