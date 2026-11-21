"""Definiciones declarativas de entidades, operaciones y reportes.

Describen QUÉ se puede hacer con cada tabla; no saben CÓMO se pide el dato
(eso es la UI) ni CÓMO se ejecuta (eso es la infraestructura).
"""

from __future__ import annotations

from dataclasses import dataclass

from horarios.dominio.campos import Campo


@dataclass(frozen=True)
class Operacion:
    """Una llamada a un procedimiento almacenado con sus parámetros en orden."""

    procedimiento: str
    campos: tuple[Campo, ...]
    mensaje_exito: str


@dataclass(frozen=True)
class Entidad:
    titulo: str
    tabla: str
    orden: str = ""
    insertar: Operacion | None = None
    modificar: Operacion | None = None
    eliminar: Operacion | None = None
    nota: str = ""


@dataclass(frozen=True)
class Reporte:
    titulo: str
    procedimiento: str
    campos: tuple[Campo, ...] = ()
