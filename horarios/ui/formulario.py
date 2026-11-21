"""Pide al usuario los valores de una lista de campos."""

from __future__ import annotations

from typing import Any, Sequence

from horarios.dominio.campos import Campo, ValorInvalido
from horarios.ui.consola import Consola


class Formulario:
    """S: solo recolecta y valida datos; la validación de cada tipo vive en
    el propio Campo, así este código no cambia al agregar tipos nuevos."""

    def __init__(self, consola: Consola):
        self._consola = consola

    def completar(self, campos: Sequence[Campo]) -> dict[str, Any]:
        valores: dict[str, Any] = {}
        for campo in campos:
            valores[campo.nombre] = self._leer(campo) if campo.es_visible(valores) else None
        return valores

    def _leer(self, campo: Campo) -> Any:
        while True:
            texto = self._consola.leer(f"{campo.indicacion()}: ")
            try:
                return campo.procesar(texto)
            except ValorInvalido as err:
                self._consola.mostrar(f"  {err}")
