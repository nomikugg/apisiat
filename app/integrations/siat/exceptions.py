class SiatError(Exception):
    """Error base para cualquier falla del adapter SIAT."""


class SiatConnectionError(SiatError):
    """El servicio SOAP del SIN no respondió o respondió con un error de transporte."""


class SiatValidationError(SiatError):
    """El SIN rechazó el documento (XML/datos inválidos según sus reglas)."""


class CodigoControlNoDisponibleError(SiatError):
    """
    El cálculo del Código de Control (CUF/CUFD) no puede completarse porque falta la
    especificación exacta del SIN (alfabeto Base64 propio, orden de ensamblaje de los
    6 pasos, casos de prueba de validación). Ver docs/04-adapter-siat.md.
    """
