"""Catálogo de las 11 tablas del sistema.

Para agregar una tabla nueva basta con añadir una `Entidad` a ENTIDADES:
el menú principal y el CRUD se generan solos (principio Abierto/Cerrado).
Los parámetros de cada Operacion están en el MISMO orden que en
database/init/02_procedimientos.sql.
"""

from horarios.catalogo import valores as v
from horarios.dominio.campos import CampoEntero, CampoHora, CampoOpcion, CampoTexto
from horarios.dominio.modelos import Entidad, Operacion

# --- Campos reutilizables ---------------------------------------------------

def _dni(etiqueta: str = "DNI del docente") -> CampoTexto:
    return CampoTexto("dni", etiqueta, patron=r"\d{8}", mensaje_patron="El DNI debe tener 8 dígitos.")


def _asignatura(etiqueta: str = "Nombre de la asignatura") -> CampoTexto:
    return CampoTexto("asignatura", etiqueta)


def _es_clase(valores) -> bool:
    return valores.get("naturaleza") == "Clase"


# --- Entidades --------------------------------------------------------------

GRADO_ESCOLAR = Entidad(
    titulo="Grados escolares",
    tabla="Grado_Escolar",
    orden="ORDER BY ID_Grado",
    insertar=Operacion("sp_insertar_grado_escolar", (
        CampoEntero("id_grado", "ID de grado", minimo=1),
        CampoTexto("nombre", "Nombre (ej. 3°)"),
        CampoOpcion("nivel", "Nivel", opciones=v.NIVELES),
    ), "Grado insertado."),
    modificar=Operacion("sp_modificar_grado_escolar", (
        CampoEntero("id_grado", "ID de grado a modificar", minimo=1),
        CampoTexto("nombre", "Nuevo nombre"),
        CampoOpcion("nivel", "Nuevo nivel", opciones=v.NIVELES),
    ), "Grado modificado."),
    eliminar=Operacion("sp_eliminar_grado_escolar", (
        CampoEntero("id_grado", "ID de grado a eliminar", minimo=1),
    ), "Grado eliminado."),
)

DOCENTE = Entidad(
    titulo="Docentes",
    tabla="Docente",
    orden="ORDER BY Nombre",
    insertar=Operacion("sp_insertar_docente", (
        _dni("DNI (8 dígitos)"),
        CampoTexto("nombre", "Nombre completo"),
        CampoOpcion("modalidad", "Modalidad", opciones=v.MODALIDADES),
        CampoOpcion("condicion", "Condición especial", opciones=v.CONDICIONES),
    ), "Docente insertado."),
    modificar=Operacion("sp_modificar_docente", (
        _dni("DNI del docente a modificar"),
        CampoTexto("nombre", "Nuevo nombre"),
        CampoOpcion("modalidad", "Nueva modalidad", opciones=v.MODALIDADES),
        CampoOpcion("condicion", "Nueva condición especial", opciones=v.CONDICIONES),
    ), "Docente modificado."),
    eliminar=Operacion("sp_eliminar_docente", (
        _dni("DNI del docente a eliminar"),
    ), "Docente eliminado."),
)

ASIGNATURA = Entidad(
    titulo="Asignaturas",
    tabla="Asignatura",
    orden="ORDER BY Nombre_Materia",
    insertar=Operacion("sp_insertar_asignatura", (
        _asignatura("Nombre de la materia"),
        CampoOpcion("exigencia", "Nivel de exigencia", opciones=v.EXIGENCIAS),
    ), "Asignatura insertada."),
    modificar=Operacion("sp_modificar_asignatura", (
        _asignatura("Nombre de la materia a modificar"),
        CampoOpcion("exigencia", "Nuevo nivel de exigencia", opciones=v.EXIGENCIAS),
    ), "Asignatura modificada."),
    eliminar=Operacion("sp_eliminar_asignatura", (
        _asignatura("Nombre de la materia a eliminar"),
    ), "Asignatura eliminada."),
)

PERIODO_ACADEMICO = Entidad(
    titulo="Periodos académicos",
    tabla="Periodo_Academico",
    orden="ORDER BY Anio_Lectivo",
    insertar=Operacion("sp_insertar_periodo", (
        CampoEntero("anio", "Año lectivo"),
        CampoOpcion("estado", "Estado", opciones=v.ESTADOS_PERIODO),
    ), "Periodo insertado."),
    modificar=Operacion("sp_modificar_periodo", (
        CampoEntero("anio", "Año lectivo a modificar"),
        CampoOpcion("estado", "Nuevo estado", opciones=v.ESTADOS_PERIODO),
    ), "Periodo modificado."),
    eliminar=Operacion("sp_eliminar_periodo", (
        CampoEntero("anio", "Año lectivo a eliminar"),
    ), "Periodo eliminado."),
)

SECCION = Entidad(
    titulo="Secciones",
    tabla="Seccion",
    orden="ORDER BY ID_Grado, Letra_Identificadora",
    insertar=Operacion("sp_insertar_seccion", (
        CampoEntero("id_seccion", "ID de sección", minimo=1),
        CampoOpcion("letra", "Letra", opciones=v.LETRAS_SECCION),
        CampoEntero("id_grado", "ID de grado al que pertenece", minimo=1),
    ), "Sección insertada."),
    modificar=Operacion("sp_modificar_seccion", (
        CampoEntero("id_seccion", "ID de sección a modificar", minimo=1),
        CampoOpcion("letra", "Nueva letra", opciones=v.LETRAS_SECCION),
        CampoEntero("id_grado", "Nuevo ID de grado", minimo=1),
    ), "Sección modificada."),
    eliminar=Operacion("sp_eliminar_seccion", (
        CampoEntero("id_seccion", "ID de sección a eliminar", minimo=1),
    ), "Sección eliminada."),
)

ESPACIO = Entidad(
    titulo="Espacios / ambientes físicos",
    tabla="Espacio",
    orden="ORDER BY Denominacion",
    insertar=Operacion("sp_insertar_espacio", (
        CampoTexto("denominacion", "Denominación (ej. Aula 101)"),
        CampoOpcion("categoria", "Categoría", opciones=v.CATEGORIAS_ESPACIO),
        CampoEntero("limite", "Límite de grupos simultáneos", minimo=1),
    ), "Espacio insertado."),
    modificar=Operacion("sp_modificar_espacio", (
        CampoTexto("denominacion", "Denominación a modificar"),
        CampoOpcion("categoria", "Nueva categoría", opciones=v.CATEGORIAS_ESPACIO),
        CampoEntero("limite", "Nuevo límite de grupos", minimo=1),
    ), "Espacio modificado."),
    eliminar=Operacion("sp_eliminar_espacio", (
        CampoTexto("denominacion", "Denominación a eliminar"),
    ), "Espacio eliminado."),
)


def _campos_actividad(prefijo: str) -> tuple:
    nuevo = "Nuevo " if prefijo else ""
    nueva = "Nueva " if prefijo else ""
    return (
        CampoEntero("id_actividad", f"ID de actividad{prefijo}", minimo=1),
        CampoHora("hora_inicio", f"{nueva}Hora de inicio".capitalize()),
        CampoHora("hora_fin", f"{nueva}Hora de fin".capitalize()),
        CampoOpcion("dia", f"{nuevo}Día".capitalize(), opciones=v.DIAS),
        CampoOpcion("naturaleza", f"{nueva}Naturaleza".capitalize(), opciones=v.NATURALEZAS),
        CampoTexto("asignatura", f"{nueva}Asignatura".capitalize(), visible_si=_es_clase,
                   ayuda="Solo si la naturaleza es Clase"),
        CampoEntero("anio", f"{nuevo}Año lectivo (periodo)".capitalize()),
        CampoTexto("espacio", f"{nuevo}Espacio (denominación exacta)".capitalize()),
    )


ACTIVIDAD = Entidad(
    titulo="Actividades (bloques de horario)",
    tabla="Actividad",
    orden="ORDER BY Periodo, FIELD(Dia,'Lunes','Martes','Miércoles','Jueves','Viernes'), Hora_Inicio",
    insertar=Operacion("sp_insertar_actividad", _campos_actividad(""), "Actividad insertada."),
    modificar=Operacion("sp_modificar_actividad", _campos_actividad(" a modificar"), "Actividad modificada."),
    eliminar=Operacion("sp_eliminar_actividad", (
        CampoEntero("id_actividad", "ID de actividad a eliminar", minimo=1),
    ), "Actividad eliminada."),
    nota="La BD rechaza bloques que se crucen en el mismo espacio, día y periodo.",
)

GRADO_MATERIA = Entidad(
    titulo="Plan de estudios (Grado x Asignatura)",
    tabla="Grado_Materia",
    orden="ORDER BY ID_Grado, Nombre_Asignatura",
    insertar=Operacion("sp_insertar_grado_materia", (
        _asignatura(),
        CampoEntero("id_grado", "ID de grado", minimo=1),
        CampoEntero("horas", "Horas pedagógicas exigidas", minimo=1),
    ), "Registro insertado."),
    modificar=Operacion("sp_modificar_grado_materia", (
        _asignatura(),
        CampoEntero("id_grado", "ID de grado", minimo=1),
        CampoEntero("horas", "Nuevas horas exigidas", minimo=1),
    ), "Registro modificado."),
    eliminar=Operacion("sp_eliminar_grado_materia", (
        _asignatura(),
        CampoEntero("id_grado", "ID de grado", minimo=1),
    ), "Registro eliminado."),
)

ESPECIALIZADO_EN = Entidad(
    titulo="Especialidades docentes",
    tabla="Especializado_En",
    orden="ORDER BY Nombre_Asignatura",
    insertar=Operacion("sp_insertar_especializado_en", (_asignatura(), _dni()), "Especialidad registrada."),
    eliminar=Operacion("sp_eliminar_especializado_en", (_asignatura(), _dni()), "Especialidad eliminada."),
    nota="Sin 'modificar': se elimina y se vuelve a insertar.",
)

SECCION_PERIODO = Entidad(
    titulo="Participación de secciones en actividades",
    tabla="Seccion_Periodo",
    orden="ORDER BY ID_Actividad",
    insertar=Operacion("sp_insertar_seccion_periodo", (
        CampoEntero("id_actividad", "ID de actividad", minimo=1),
        CampoEntero("id_seccion", "ID de sección", minimo=1),
    ), "Participación registrada."),
    eliminar=Operacion("sp_eliminar_seccion_periodo", (
        CampoEntero("id_actividad", "ID de actividad", minimo=1),
        CampoEntero("id_seccion", "ID de sección", minimo=1),
    ), "Participación eliminada."),
    nota="Sin 'modificar': se elimina y se vuelve a insertar.",
)

DOCENTE_ACTIVIDAD = Entidad(
    titulo="Carga docente por actividad",
    tabla="Docente_Actividad",
    orden="ORDER BY DNI_Docente",
    insertar=Operacion("sp_insertar_docente_actividad", (
        _dni(),
        CampoEntero("id_actividad", "ID de actividad", minimo=1),
        CampoOpcion("rol", "Rol asumido", opciones=v.ROLES_DOCENTE),
    ), "Asignación registrada."),
    modificar=Operacion("sp_modificar_docente_actividad", (
        _dni(),
        CampoEntero("id_actividad", "ID de actividad", minimo=1),
        CampoOpcion("rol", "Nuevo rol", opciones=v.ROLES_DOCENTE),
    ), "Asignación modificada."),
    eliminar=Operacion("sp_eliminar_docente_actividad", (
        _dni(),
        CampoEntero("id_actividad", "ID de actividad", minimo=1),
    ), "Asignación eliminada."),
    nota="La BD rechaza asignar a un docente dos actividades que se crucen.",
)

ENTIDADES: tuple[Entidad, ...] = (
    GRADO_ESCOLAR,
    DOCENTE,
    ASIGNATURA,
    PERIODO_ACADEMICO,
    SECCION,
    ESPACIO,
    ACTIVIDAD,
    GRADO_MATERIA,
    ESPECIALIZADO_EN,
    SECCION_PERIODO,
    DOCENTE_ACTIVIDAD,
)
