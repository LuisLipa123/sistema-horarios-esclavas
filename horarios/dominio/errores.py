"""Errores del dominio. Las capas superiores no conocen mysql.connector."""


class ErrorBaseDatos(Exception):
    """Error genérico al hablar con la base de datos."""

    def __init__(self, mensaje: str, codigo: int | None = None):
        super().__init__(mensaje)
        self.mensaje = mensaje
        self.codigo = codigo


class ErrorConexion(ErrorBaseDatos):
    """No se pudo abrir la conexión (servidor caído, credenciales, etc.)."""

    ACCESO_DENEGADO = 1045
    SERVIDOR_NO_DISPONIBLE = 2003

    @property
    def es_acceso_denegado(self) -> bool:
        return self.codigo == self.ACCESO_DENEGADO

    @property
    def es_servidor_no_disponible(self) -> bool:
        return self.codigo == self.SERVIDOR_NO_DISPONIBLE


class OperacionRechazada(ErrorBaseDatos):
    """La BD rechazó la operación (CHECK, FK, trigger de cruces, etc.)."""
