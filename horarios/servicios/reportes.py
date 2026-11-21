"""Caso de uso: generación de reportes."""

from __future__ import annotations

from typing import Any, Mapping

from horarios.dominio.modelos import Reporte
from horarios.dominio.puertos import LectorProcedimientos, Resultado


class ServicioReportes:
    def __init__(self, lector: LectorProcedimientos):
        self._lector = lector

    def generar(self, reporte: Reporte, valores: Mapping[str, Any]) -> Resultado:
        parametros = tuple(valores.get(campo.nombre) for campo in reporte.campos)
        return self._lector.consultar(reporte.procedimiento, parametros)
