class SiatError(Exception):
    """Error base para cualquier falla del adapter SIAT."""


class SiatConnectionError(SiatError):
    """El servicio SOAP del SIN no respondió o respondió con un error de transporte."""


class SiatValidationError(SiatError):
    """El SIN rechazó el documento (XML/datos inválidos según sus reglas)."""
