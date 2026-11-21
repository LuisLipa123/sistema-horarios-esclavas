"""Pantallas de la aplicación.

Todas las pantallas cumplen el mismo contrato (`titulo` + `abrir()`), así el
menú principal puede mostrar cualquiera sin conocer su tipo concreto
(Liskov) y se pueden añadir pantallas nuevas sin modificarlo (Abierto/Cerrado).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable, Sequence

from horarios.dominio.errores import ErrorBaseDatos
from horarios.dominio.modelos import Entidad, Operacion, Reporte
from horarios.servicios.crud import ServicioCrud
from horarios.servicios.reportes import ServicioReportes
from horarios.ui.consola import Consola
from horarios.ui.formulario import Formulario
from horarios.ui.tabla import formatear_tabla

Accion = Callable[[], None]


def elegir(consola: Consola, titulo: str, opciones: Sequence[tuple[str, Accion]],
           etiqueta_salida: str = "Volver") -> bool:
    """Muestra un menú numerado y ejecuta la acción elegida.
    Devuelve False cuando el usuario elige salir (0)."""
    consola.mostrar(f"\n--- {titulo} ---")
    for numero, (etiqueta, _) in enumerate(opciones, start=1):
        consola.mostrar(f"  {numero}. {etiqueta}")
    consola.mostrar(f"  0. {etiqueta_salida}")
    eleccion = consola.leer("Elige una opción: ").strip()
    if eleccion == "0":
        return False
    if eleccion.isdigit() and 1 <= int(eleccion) <= len(opciones):
        opciones[int(eleccion) - 1][1]()
    else:
        consola.mostrar("Opción no válida.")
    return True


class Pantalla(ABC):
    def __init__(self, consola: Consola):
        self._consola = consola

    @property
    @abstractmethod
    def titulo(self) -> str: ...

    @abstractmethod
    def opciones(self) -> list[tuple[str, Accion]]: ...

    def abrir(self) -> None:
        while elegir(self._consola, self.titulo, self.opciones()):
            pass

    def _informar_error(self, err: ErrorBaseDatos) -> None:
        self._consola.mostrar(f"✘ La base de datos rechazó la operación: {err.mensaje}")


class PantallaCrud(Pantalla):
    """Pantalla genérica de mantenimiento: sirve para las 11 tablas."""

    def __init__(self, consola: Consola, entidad: Entidad, servicio: ServicioCrud, formulario: Formulario):
        super().__init__(consola)
        self._entidad = entidad
        self._servicio = servicio
        self._formulario = formulario

    @property
    def titulo(self) -> str:
        return self._entidad.titulo

    def opciones(self) -> list[tuple[str, Accion]]:
        e = self._entidad
        posibles = [("Insertar", e.insertar), ("Modificar", e.modificar), ("Eliminar", e.eliminar)]
        opciones = [(nombre, self._accion(op)) for nombre, op in posibles if op is not None]
        opciones.append(("Listar", self._listar))
        return opciones

    def abrir(self) -> None:
        if self._entidad.nota:
            self._consola.mostrar(f"\n(i) {self._entidad.nota}")
        super().abrir()

    def _accion(self, operacion: Operacion) -> Accion:
        def ejecutar() -> None:
            valores = self._formulario.completar(operacion.campos)
            try:
                self._servicio.ejecutar(operacion, valores)
                self._consola.mostrar(f"✔ {operacion.mensaje_exito}")
            except ErrorBaseDatos as err:
                self._informar_error(err)
        return ejecutar

    def _listar(self) -> None:
        try:
            self._consola.mostrar(formatear_tabla(self._servicio.listar(self._entidad)))
        except ErrorBaseDatos as err:
            self._informar_error(err)


class PantallaReportes(Pantalla):
    def __init__(self, consola: Consola, reportes: Sequence[Reporte],
                 servicio: ServicioReportes, formulario: Formulario):
        super().__init__(consola)
        self._reportes = reportes
        self._servicio = servicio
        self._formulario = formulario

    @property
    def titulo(self) -> str:
        return "Reportes"

    def opciones(self) -> list[tuple[str, Accion]]:
        return [(r.titulo, self._accion(r)) for r in self._reportes]

    def _accion(self, reporte: Reporte) -> Accion:
        def generar() -> None:
            valores = self._formulario.completar(reporte.campos)
            try:
                resultado = self._servicio.generar(reporte, valores)
                self._consola.mostrar()
                self._consola.mostrar(formatear_tabla(resultado))
            except ErrorBaseDatos as err:
                self._consola.mostrar(f"✘ Error al generar el reporte: {err.mensaje}")
            self._consola.leer("\nPresiona Enter para continuar...")
        return generar


class MenuPrincipal:
    ENCABEZADO = (
        "==========================================================\n"
        " SISTEMA DE ASIGNACIÓN DE HORARIOS Y CARGA ACADÉMICA\n"
        " Colegio Particular Esclavas del Sagrado Corazón de Jesús\n"
        "=========================================================="
    )

    def __init__(self, consola: Consola, pantallas: Sequence[Pantalla]):
        self._consola = consola
        self._pantallas = pantallas

    def abrir(self) -> None:
        opciones = [(p.titulo, p.abrir) for p in self._pantallas]
        while True:
            self._consola.mostrar("\n" + self.ENCABEZADO)
            if not elegir(self._consola, "Menú principal", opciones, etiqueta_salida="Salir"):
                self._consola.mostrar("Hasta luego.")
                return
