"""Dobles de prueba: implementaciones en memoria de los puertos.

Gracias a la inversión de dependencias, los servicios y pantallas se prueban
sin MySQL.
"""

from __future__ import annotations

from horarios.dominio.errores import OperacionRechazada
from horarios.dominio.puertos import Resultado


class GatewayFalso:
    def __init__(self, rechazar_con: str | None = None, resultado: Resultado | None = None,
                 tablas: dict[str, Resultado] | None = None,
                 procedimientos: dict[str, Resultado] | None = None):
        self.llamadas: list[tuple[str, tuple]] = []
        self.listados: list[tuple[str, str]] = []
        self._rechazar_con = rechazar_con
        self._resultado = resultado or Resultado(["col"], [("valor",)])
        self._tablas = tablas or {}
        self._procedimientos = procedimientos or {}

    def ejecutar(self, procedimiento, parametros):
        self.llamadas.append((procedimiento, tuple(parametros)))
        if self._rechazar_con:
            raise OperacionRechazada(self._rechazar_con)

    def consultar(self, procedimiento, parametros):
        self.llamadas.append((procedimiento, tuple(parametros)))
        return self._procedimientos.get(procedimiento, self._resultado)

    def listar(self, tabla, orden=""):
        self.listados.append((tabla, orden))
        return self._tablas.get(tabla, self._resultado)


class ConsolaFalsa:
    def __init__(self, entradas: list[str]):
        self._entradas = list(entradas)
        self.salida: list[str] = []

    def leer(self, mensaje):
        self.salida.append(mensaje)
        return self._entradas.pop(0)

    def mostrar(self, texto=""):
        self.salida.append(texto)

    @property
    def texto(self) -> str:
        return "\n".join(self.salida)
