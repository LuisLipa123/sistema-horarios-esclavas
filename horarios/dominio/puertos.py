"""Abstracciones (puertos) de las que dependen los servicios.

I (Segregación de interfaces): cada consumidor depende solo de la interfaz
que usa — el servicio CRUD no conoce los reportes y viceversa.
D (Inversión de dependencias): los servicios dependen de estos protocolos,
no de MySQL; la implementación concreta se inyecta en bootstrap.py.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, Sequence


@dataclass(frozen=True)
class Resultado:
    columnas: list[str] = field(default_factory=list)
    filas: list[tuple[Any, ...]] = field(default_factory=list)

    @property
    def vacio(self) -> bool:
        return not self.filas


class EjecutorProcedimientos(Protocol):
    """Ejecuta procedimientos que modifican datos (insertar/modificar/eliminar)."""

    def ejecutar(self, procedimiento: str, parametros: Sequence[Any]) -> None: ...


class LectorProcedimientos(Protocol):
    """Ejecuta procedimientos que devuelven filas (reportes)."""

    def consultar(self, procedimiento: str, parametros: Sequence[Any]) -> Resultado: ...


class LectorTablas(Protocol):
    """Lee el contenido completo de una tabla (listados)."""

    def listar(self, tabla: str, orden: str = "") -> Resultado: ...
