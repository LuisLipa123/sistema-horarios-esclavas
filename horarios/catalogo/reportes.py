"""Catálogo de los 10 reportes de database/init/05_reportes.sql."""

from horarios.catalogo import valores as v
from horarios.dominio.campos import CampoEntero, CampoOpcion, CampoTexto
from horarios.dominio.modelos import Reporte

REPORTES: tuple[Reporte, ...] = (
    Reporte("Horario completo de una sección", "sp_reporte_01_horario_seccion",
            (CampoEntero("id_seccion", "ID de sección", minimo=1),)),
    Reporte("Carga horaria semanal de un docente", "sp_reporte_02_carga_docente",
            (CampoTexto("dni", "DNI del docente", patron=r"\d{8}",
                        mensaje_patron="El DNI debe tener 8 dígitos."),)),
    Reporte("Docentes especializados en una asignatura", "sp_reporte_03_docentes_por_asignatura",
            (CampoTexto("asignatura", "Nombre de la asignatura"),)),
    Reporte("Plan de estudios (horas exigidas) de un grado", "sp_reporte_04_plan_estudios_grado",
            (CampoEntero("id_grado", "ID de grado", minimo=1),)),
    Reporte("Ocupación de espacios en un día", "sp_reporte_05_ocupacion_espacios",
            (CampoOpcion("dia", "Día", opciones=v.DIAS),)),
    Reporte("Actividades por naturaleza y periodo", "sp_reporte_06_actividades_por_naturaleza",
            (CampoOpcion("naturaleza", "Naturaleza", opciones=v.NATURALEZAS),
             CampoEntero("anio", "Año lectivo"))),
    Reporte("Docentes con condición especial y su carga", "sp_reporte_07_docentes_condicion_especial"),
    Reporte("Secciones por nivel educativo", "sp_reporte_08_secciones_por_nivel",
            (CampoOpcion("nivel", "Nivel", opciones=v.NIVELES),)),
    Reporte("Horas exigidas vs. bloques programados por asignatura",
            "sp_reporte_09_horas_exigidas_vs_programadas",
            (CampoEntero("anio", "Año lectivo"),)),
    Reporte("Bitácora de los últimos cambios", "sp_reporte_10_bitacora_reciente",
            (CampoEntero("limite", "Cantidad de registros a mostrar", minimo=1),)),
)
