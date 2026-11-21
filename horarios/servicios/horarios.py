"""Caso de uso: armar la grilla semanal (Lunes–Viernes × franjas horarias)
del horario de una sección, de un docente o de un espacio."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any, Callable, Iterable, Mapping

from horarios.catalogo.valores import DIAS
from horarios.dominio.puertos import LectorProcedimientos, LectorTablas, Resultado

Franja = tuple[str, str]
Fila = Mapping[str, Any]


@dataclass(frozen=True)
class Bloque:
    titulo: str
    detalle: str = ""
    es_clase: bool = True


@dataclass
class Grilla:
    titulo: str
    dias: tuple[str, ...] = DIAS
    franjas: list[Franja] = field(default_factory=list)
    celdas: dict[tuple[Franja, str], list[Bloque]] = field(default_factory=dict)

    @property
    def vacia(self) -> bool:
        return not self.franjas

    def bloques(self, franja: Franja, dia: str) -> list[Bloque]:
        return self.celdas.get((franja, dia), [])


def hhmm(valor: Any) -> str:
    """MySQL devuelve TIME como timedelta; lo normaliza a 'HH:MM'."""
    if isinstance(valor, timedelta):
        segundos = int(valor.total_seconds())
        return f"{segundos // 3600:02d}:{segundos % 3600 // 60:02d}"
    return str(valor)[:5]


def armar_grilla(titulo: str, filas: Iterable[Fila], a_bloque: Callable[[Fila], Bloque]) -> Grilla:
    grilla = Grilla(titulo)
    franjas: set[Franja] = set()
    for fila in filas:
        franja = (hhmm(fila["Hora_Inicio"]), hhmm(fila["Hora_Fin"]))
        franjas.add(franja)
        grilla.celdas.setdefault((franja, fila["Dia"]), []).append(a_bloque(fila))
    grilla.franjas = sorted(franjas)
    return grilla


def registros(resultado: Resultado) -> list[dict[str, Any]]:
    return [dict(zip(resultado.columnas, fila)) for fila in resultado.filas]


class ServicioHorarios:
    def __init__(self, procedimientos: LectorProcedimientos, tablas: LectorTablas):
        self._procedimientos = procedimientos
        self._tablas = tablas

    # --- Opciones para los selectores --------------------------------------
    def secciones(self) -> list[tuple[str, str]]:
        grados = {g["ID_Grado"]: g for g in registros(self._tablas.listar("Grado_Escolar"))}
        opciones = []
        for s in registros(self._tablas.listar("Seccion", "ORDER BY ID_Grado, Letra_Identificadora")):
            g = grados.get(s["ID_Grado"], {})
            etiqueta = f"{g.get('Nombre', '?')} {g.get('Nivel', '')} - {s['Letra_Identificadora']} (ID {s['ID_Seccion']})"
            opciones.append((str(s["ID_Seccion"]), etiqueta))
        return opciones

    def docentes(self) -> list[tuple[str, str]]:
        return [(d["DNI"], f"{d['Nombre']} ({d['DNI']})")
                for d in registros(self._tablas.listar("Docente", "ORDER BY Nombre"))]

    def espacios(self) -> list[tuple[str, str]]:
        return [(e["Denominacion"], e["Denominacion"])
                for e in registros(self._tablas.listar("Espacio", "ORDER BY Denominacion"))]

    # --- Grillas -----------------------------------------------------------
    def horario_seccion(self, id_seccion: int) -> Grilla:
        filas = registros(self._procedimientos.consultar("sp_reporte_01_horario_seccion", (id_seccion,)))
        titulo = f"Sección {id_seccion}"
        if filas:
            f = filas[0]
            titulo = f"{f['Grado']} {f['Nivel']} - Sección {f['Seccion']}"
        return armar_grilla(titulo, filas, lambda f: Bloque(
            titulo=f["Asignatura"] if f["Naturaleza"] == "Clase" else f["Naturaleza"],
            detalle=f["Espacio"],
            es_clase=f["Naturaleza"] == "Clase",
        ))

    def horario_docente(self, dni: str) -> Grilla:
        filas = registros(self._procedimientos.consultar("sp_reporte_02_carga_docente", (dni,)))
        titulo = f"Docente {filas[0]['Docente']}" if filas else f"Docente {dni}"
        def a_bloque(f: Fila) -> Bloque:
            tiene_materia = f["Asignatura"] != "—"
            return Bloque(
                titulo=f["Asignatura"] if tiene_materia else f["Rol_Asumido"],
                detalle=f"{f['Espacio']} · {f['Rol_Asumido']}" if tiene_materia else f["Espacio"],
                es_clase=f["Rol_Asumido"] == "Dicta clase",
            )
        return armar_grilla(titulo, filas, a_bloque)

    def horario_espacio(self, denominacion: str) -> Grilla:
        actividades = [a for a in registros(self._tablas.listar("Actividad", "ORDER BY Hora_Inicio"))
                       if a["Espacio"] == denominacion]
        return armar_grilla(f"Espacio {denominacion}", actividades, lambda a: Bloque(
            titulo=a["Materia_Asignatura"] or a["Naturaleza"],
            detalle=f"Periodo {a['Periodo']} · Actividad {a['ID_Actividad']}",
            es_clase=a["Naturaleza"] == "Clase",
        ))
