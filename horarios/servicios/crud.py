"""Caso de uso: mantenimiento (insertar/modificar/eliminar/listar) de tablas."""

from __future__ import annotations

from typing import Any, Mapping

from horarios.dominio.modelos import Entidad, Operacion
from horarios.dominio.puertos import EjecutorProcedimientos, LectorTablas, Resultado


class ServicioCrud:
    """S: traduce una Operacion + valores en una llamada al procedimiento.
    D: depende de los puertos, no de MySQL."""

    def __init__(self, ejecutor: EjecutorProcedimientos, lector: LectorTablas):
        self._ejecutor = ejecutor
        self._lector = lector

    def ejecutar(self, operacion: Operacion, valores: Mapping[str, Any]) -> None:
        parametros = tuple(valores.get(campo.nombre) for campo in operacion.campos)
        self._ejecutor.ejecutar(operacion.procedimiento, parametros)

    def listar(self, entidad: Entidad) -> Resultado:
        return self._lector.listar(entidad.tabla, entidad.orden)
