"""
Ensamblaje del "Código de Control" del CUF/CUFD.

Referencia: docs/01-marco-regulatorio-sin.md, sección "CUFD y CUF — núcleo técnico",
algoritmo de 6 pasos:

  1. Agregar 2 dígitos Verhoeff a factura/NIT/fecha/monto; sumar valores; agregar 5
     dígitos Verhoeff más.
  2. Extraer los últimos 5 dígitos Verhoeff; usarlos para extraer subcadenas de la
     "clave de dosificación".
  3. Concatenar subcadenas extraídas con los campos originales; cifrar con RC4 usando
     la clave de dosificación + los 5 dígitos Verhoeff.
  4. Convertir el string cifrado a valores ASCII; distribuir en 5 sumas parciales.
  5. Calcular producto (total × sumas parciales ÷ posiciones de subcadena); convertir a
     Base64 (alfabeto propio del SIN, sin O/l/0/1).
  6. Aplicar RC4 al resultado Base64 usando la clave combinada.

  Formato final: alfanumérico hasta 10 caracteres, en pares separados por guiones
  (ej. "6A-DC-53-05-14").

Estado de esta implementación
------------------------------
- Paso 1 está implementado (es el único paso cuya especificación es independiente de
  secretos del SIN: usa `verhoeff.verhoeff_digit` repetidamente).
- Pasos 2-6 requieren información que NO está disponible en este entorno:
    * El algoritmo exacto de extracción de subcadenas de la "clave de dosificación"
      (posiciones, longitudes).
    * El alfabeto Base64 real del SIN (`base64_sin.ALFABETO_SIN_PLACEHOLDER` es solo
      un ejemplo con la forma correcta, no el real).
    * Los ~5000 casos de prueba publicados por el SIN para validar el resultado final.
  Estos datos están en el PDF de Anexos Técnicos SFE (ver docs/04-adapter-siat.md).
  Por eso esta función levanta `CodigoControlNoDisponibleError` antes de producir un
  resultado que NO podríamos validar y que sería fiscalmente incorrecto.
"""

from datetime import datetime
from decimal import Decimal

from app.integrations.siat.cuf.verhoeff import verhoeff_digit
from app.integrations.siat.exceptions import CodigoControlNoDisponibleError


def _encadenar_verhoeff(semilla: str, cantidad: int) -> str:
    """Calcula `cantidad` dígitos Verhoeff encadenados, cada uno sobre la cadena acumulada."""
    resultado = semilla
    digitos = []
    for _ in range(cantidad):
        digito = verhoeff_digit(resultado)
        digitos.append(digito)
        resultado += digito
    return "".join(digitos)


def calcular_codigo_control(
    *,
    nit: int,
    numero_factura: int,
    fecha: datetime,
    monto_total: Decimal,
    clave_dosificacion: str,
) -> str:
    """
    Calcula el "Código de Control" (CUF/CUFD) según los 6 pasos de docs/01.

    Levanta `CodigoControlNoDisponibleError` porque los pasos 2-6 dependen de
    especificación oficial del SIN no disponible en este entorno (ver docstring
    del módulo y docs/04-adapter-siat.md).
    """
    monto_centavos = int((monto_total * 100).to_integral_value())
    campos = f"{numero_factura}{nit}{fecha:%Y%m%d}{monto_centavos}"

    # Paso 1: 2 dígitos Verhoeff sobre los campos, sumar valores, 5 dígitos Verhoeff más.
    dos_digitos = _encadenar_verhoeff(campos, 2)
    suma = sum(int(c) for c in campos + dos_digitos)
    cinco_digitos = _encadenar_verhoeff(str(suma), 5)

    # Pasos 2-6: requieren especificación oficial del SIN (clave de dosificación,
    # alfabeto Base64 propio, casos de prueba de validación).
    raise CodigoControlNoDisponibleError(
        "Pasos 2-6 del Código de Control pendientes: falta la especificación oficial "
        "del SIN (extracción de subcadenas de la clave de dosificación, alfabeto "
        "Base64 propio y casos de prueba). Ver docs/04-adapter-siat.md. "
        f"(paso 1 completado: cinco_digitos={cinco_digitos!r}, "
        f"clave_dosificacion_presente={bool(clave_dosificacion)})"
    )
