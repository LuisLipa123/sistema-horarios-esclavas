"""Controladores web: reciben una Peticion, usan un servicio y devuelven HTML.

Cada controlador tiene una sola responsabilidad (S) y depende de servicios
que a su vez dependen de abstracciones (D).
"""

from __future__ import annotations

from typing import Sequence

from horarios.dominio.campos import ValorInvalido, procesar_campos
from horarios.dominio.errores import ErrorBaseDatos
from horarios.dominio.modelos import Entidad, Reporte
from horarios.servicios.crud import ServicioCrud
from horarios.servicios.horarios import ServicioHorarios
from horarios.servicios.reportes import ServicioReportes
from horarios.web import vistas as v
from horarios.web.peticiones import Peticion, Respuesta

ACCIONES = {"insertar": "Insertar", "modificar": "Modificar", "eliminar": "Eliminar"}


def slug(entidad: Entidad) -> str:
    return entidad.tabla.lower()


class ControladorInicio:
    def __init__(self, entidades: Sequence[Entidad], reportes: Sequence[Reporte]):
        self._entidades = entidades
        self._reportes = reportes

    def inicio(self, peticion: Peticion) -> Respuesta:
        tarjetas = (
            v.tarjeta_enlace("/horarios", "Horarios semanales",
                             "Mira la semana de una sección, un docente o un ambiente.", "calendario")
            + v.tarjeta_enlace("/tablas", "Tablas",
                               f"Registra, edita o elimina datos de las {len(self._entidades)} tablas.", "tabla")
            + v.tarjeta_enlace("/reportes", "Reportes",
                               f"{len(self._reportes)} consultas listas: cargas, ocupación, bitácora…", "reporte")
        )
        return Respuesta(v.pagina("Bienvenido", f'<div class="tarjetas">{tarjetas}</div>', activo="/",
                                  subtitulo="Colegio Particular Esclavas del Sagrado Corazón de Jesús · "
                                            "¿Qué quieres revisar hoy?"))

    def no_encontrado(self, peticion: Peticion) -> Respuesta:
        cuerpo = '<a class="volver" href="/">← Volver al inicio</a>'
        return Respuesta(v.pagina("Página no encontrada", cuerpo, subtitulo="Esa dirección no existe."), 404)


class ControladorEntidades:
    def __init__(self, entidades: Sequence[Entidad], servicio: ServicioCrud):
        self._entidades = {slug(e): e for e in entidades}
        self._servicio = servicio

    def indice(self, peticion: Peticion) -> Respuesta:
        tarjetas = "".join(
            v.tarjeta_enlace(f"/tablas/{s}", e.titulo,
                             " · ".join(n for a, n in ACCIONES.items() if getattr(e, a)) + " · Listar")
            for s, e in self._entidades.items())
        return Respuesta(v.pagina("Tablas", f'<div class="tarjetas">{tarjetas}</div>', activo="/tablas",
                                  subtitulo="Elige una tabla para ver sus registros o hacer cambios."))

    def ver(self, peticion: Peticion, tabla: str) -> Respuesta:
        entidad = self._entidades.get(tabla)
        if entidad is None:
            return Respuesta(v.pagina("Tabla no encontrada", "", activo="/tablas"), 404)
        return self._pagina(entidad, ok=peticion.consulta.get("ok"), error=peticion.consulta.get("error"))

    def ejecutar(self, peticion: Peticion, tabla: str, accion: str) -> Respuesta:
        entidad = self._entidades.get(tabla)
        operacion = getattr(entidad, accion, None) if entidad and accion in ACCIONES else None
        if operacion is None:
            return Respuesta(v.pagina("Operación no disponible", "", activo="/tablas"), 404)
        try:
            valores = procesar_campos(operacion.campos, peticion.formulario)
            self._servicio.ejecutar(operacion, valores)
        except ValorInvalido as err:
            return self._pagina(entidad, error=str(err), activa=accion, enviados=peticion.formulario, estado=400)
        except ErrorBaseDatos as err:
            return self._pagina(entidad, error=f"La base de datos rechazó la operación: {err.mensaje}",
                                activa=accion, enviados=peticion.formulario, estado=400)
        return Respuesta.redirigir(f"/tablas/{tabla}", ok=operacion.mensaje_exito)

    def _pagina(self, entidad: Entidad, ok=None, error=None, activa=None, enviados=None, estado=200) -> Respuesta:
        formularios = []
        for accion, nombre in ACCIONES.items():
            operacion = getattr(entidad, accion)
            if operacion is None:
                continue
            formularios.append(v.formulario(
                nombre, operacion.campos, f"/tablas/{slug(entidad)}/{accion}", nombre,
                valores=enviados if accion == activa else None,
                confirmar="¿Seguro que deseas eliminar este registro?" if accion == "eliminar" else None,
                plegable=True,
                abierto=accion == activa or (activa is None and accion == "insertar"),
            ))
        nota = f'<div class="nota">{v.e(entidad.nota)}</div>' if entidad.nota else ""
        try:
            listado = v.tabla(self._servicio.listar(entidad), titulo="Registros")
        except ErrorBaseDatos as err:
            listado = f'<div class="aviso error">No se pudo listar: {v.e(err.mensaje)}</div>'
        cuerpo = (f'{nota}<div class="acciones">{"".join(formularios)}</div>{listado}'
                  '<a class="volver" href="/tablas">← Todas las tablas</a>')
        return Respuesta(v.pagina(entidad.titulo, cuerpo, ok=ok, error=error, activo="/tablas",
                                  subtitulo=f"Tabla {entidad.tabla}"), estado)


class ControladorReportes:
    def __init__(self, reportes: Sequence[Reporte], servicio: ServicioReportes):
        self._reportes = reportes
        self._servicio = servicio

    def indice(self, peticion: Peticion) -> Respuesta:
        tarjetas = "".join(
            v.tarjeta_enlace(f"/reportes/{n}", r.titulo,
                             "Pide: " + ", ".join(c.etiqueta.lower() for c in r.campos) if r.campos
                             else "Sin parámetros", numero=f"REPORTE {n}")
            for n, r in enumerate(self._reportes, start=1))
        return Respuesta(v.pagina("Reportes", f'<div class="tarjetas">{tarjetas}</div>', activo="/reportes",
                                  subtitulo="Consultas sobre horarios, docentes y espacios."))

    def ver(self, peticion: Peticion, numero: str) -> Respuesta:
        indice = int(numero) - 1
        if not 0 <= indice < len(self._reportes):
            return Respuesta(v.pagina("Reporte no encontrado", "", activo="/reportes"), 404)
        reporte = self._reportes[indice]
        consulta = peticion.consulta
        resultado_html, error = "", None
        if "generar" in consulta:
            try:
                valores = procesar_campos(reporte.campos, consulta)
                resultado_html = v.tabla(self._servicio.generar(reporte, valores), titulo="Resultado")
            except ValorInvalido as err:
                error = str(err)
            except ErrorBaseDatos as err:
                error = f"Error al generar el reporte: {err.mensaje}"
        form = v.formulario("Parámetros" if reporte.campos else "", reporte.campos, f"/reportes/{numero}",
                            "Generar reporte", metodo="get", valores=consulta, ocultos={"generar": "1"})
        cuerpo = (f'<div class="acciones">{form}</div>{resultado_html}'
                  '<a class="volver" href="/reportes">← Todos los reportes</a>')
        return Respuesta(v.pagina(reporte.titulo, cuerpo, error=error, activo="/reportes",
                                  subtitulo=f"Reporte {numero} · {reporte.procedimiento}"))


class ControladorHorarios:
    def __init__(self, servicio: ServicioHorarios):
        self._servicio = servicio

    def ver(self, peticion: Peticion) -> Respuesta:
        c = peticion.consulta
        seccion, docente, espacio = c.get("seccion", ""), c.get("docente", ""), c.get("espacio", "")
        error, grilla_html = None, ""
        try:
            selectores = (
                v.selector("Por sección", "seccion", self._servicio.secciones(), seccion, "/horarios")
                + v.selector("Por docente", "docente", self._servicio.docentes(), docente, "/horarios")
                + v.selector("Por ambiente", "espacio", self._servicio.espacios(), espacio, "/horarios"))
            if seccion.isdigit():
                grilla_html = v.grilla(self._servicio.horario_seccion(int(seccion)))
            elif docente:
                grilla_html = v.grilla(self._servicio.horario_docente(docente))
            elif espacio:
                grilla_html = v.grilla(self._servicio.horario_espacio(espacio))
        except ErrorBaseDatos as err:
            selectores, error = "", f"No se pudo consultar la base de datos: {err.mensaje}"
        cuerpo = f'<div class="selectores">{selectores}</div>{grilla_html}'
        return Respuesta(v.pagina("Horarios semanales", cuerpo, error=error, activo="/horarios",
                                  subtitulo="Elige qué horario quieres ver."))
