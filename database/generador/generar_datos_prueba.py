"""Genera database/init/04_datos_prueba.sql con datos realistas y coherentes.

Simula un colegio completo (Inicial, Primaria y Secundaria) con horario semanal
para todas las secciones de Primaria y Secundaria, respetando las mismas reglas
que validan los triggers de la base de datos:
  * un espacio no puede tener dos actividades que se crucen (mismo día/periodo);
  * un docente no puede tener dos actividades que se crucen.
Además, la cantidad de bloques de cada asignatura coincide con las horas del
plan de estudios (Grado_Materia), de modo que el reporte 9 cuadra.

Uso:  python database/generador/generar_datos_prueba.py
El resultado es determinista (semilla fija).
"""

from __future__ import annotations

import random
from collections import defaultdict
from pathlib import Path

SALIDA = Path(__file__).resolve().parent.parent / "init" / "04_datos_prueba.sql"
SEMILLA = 2026
DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes"]

# --- Bloques horarios (45 min) ------------------------------------------------
BLOQUES = {
    "Primaria": [("08:00", "08:45"), ("08:45", "09:30"), ("09:45", "10:30"),
                 ("10:30", "11:15"), ("11:15", "12:00"), ("12:00", "12:45")],
    "Secundaria": [("08:00", "08:45"), ("08:45", "09:30"), ("09:30", "10:15"), ("10:30", "11:15"),
                   ("11:15", "12:00"), ("12:00", "12:45"), ("12:45", "13:30")],
}
RECESO = {"Primaria": ("09:30", "09:45", "Patio Central"),
          "Secundaria": ("10:15", "10:30", "Patio Secundaria")}

# --- Catálogos ------------------------------------------------------------------
GRADOS = [(1, "1°", "Primaria"), (2, "2°", "Primaria"), (3, "3°", "Primaria"), (4, "4°", "Primaria"),
          (5, "5°", "Primaria"), (6, "6°", "Primaria"), (7, "1°", "Secundaria"), (8, "2°", "Secundaria"),
          (9, "3°", "Secundaria"), (10, "4°", "Secundaria"), (11, "5°", "Secundaria"),
          (12, "3 años", "Inicial"), (13, "4 años", "Inicial"), (14, "5 años", "Inicial")]

ASIGNATURAS = [("Matemática", "Alta"), ("Comunicación", "Alta"), ("Ciencia y Tecnología", "Alta"),
               ("Ciencias Sociales", "Media"), ("Desarrollo Personal y Ciudadanía", "Media"),
               ("Inglés", "Media"), ("Educación Física", "Baja"), ("Arte y Cultura", "Baja"),
               ("Educación Religiosa", "Media"), ("Computación", "Media"),
               ("Educación para el Trabajo", "Media"), ("Tutoría", "Baja"), ("Danza", "Baja")]

PLAN = {  # bloques semanales por asignatura = Horas_Exigidas
    "Primaria": {"Matemática": 6, "Comunicación": 6, "Ciencia y Tecnología": 4, "Ciencias Sociales": 3,
                 "Inglés": 2, "Educación Física": 3, "Arte y Cultura": 2, "Educación Religiosa": 2,
                 "Computación": 1, "Tutoría": 1},
    "Secundaria": {"Matemática": 6, "Comunicación": 5, "Ciencia y Tecnología": 5, "Ciencias Sociales": 3,
                   "Desarrollo Personal y Ciudadanía": 2, "Inglés": 3, "Educación Física": 2,
                   "Arte y Cultura": 2, "Educación Religiosa": 2, "Computación": 2,
                   "Educación para el Trabajo": 2, "Tutoría": 1},
}
# En primaria, la tutora de aula dicta estas áreas en su propia sección.
AREAS_TUTORA = {"Matemática", "Comunicación", "Ciencia y Tecnología", "Ciencias Sociales", "Arte y Cultura", "Tutoría"}

ESPACIOS = ([(f"Aula {100 + i}", "Aula", 1) for i in range(1, 13)]           # primaria: sección i -> Aula 10i
            + [(f"Aula {200 + i}", "Aula", 1) for i in range(1, 11)]          # secundaria
            + [("Aula Inicial 1", "Aula", 1), ("Aula Inicial 2", "Aula", 1), ("Aula Inicial 3", "Aula", 1),
               ("Sala de Usos Múltiples", "Aula", 1),
               ("Cancha Principal", "Cancha", 2), ("Cancha Secundaria", "Cancha", 1), ("Losa Deportiva", "Cancha", 1),
               ("Patio Central", "Patio", 3), ("Patio Secundaria", "Patio", 2),
               ("Ambiente de Música", "Ambiente de música", 1),
               ("Centro de Cómputo", "Centro de cómputo", 1), ("Sala de Innovación", "Centro de cómputo", 1),
               ("Laboratorio de Ciencias", "Laboratorio", 1)])

# Espacios compartidos por asignatura (en el resto se usa el aula de la sección).
ESPACIO_ESPECIAL = {
    ("Primaria", "Educación Física"): ["Cancha Principal", "Losa Deportiva", "Cancha Secundaria"],
    ("Secundaria", "Educación Física"): ["Cancha Secundaria", "Cancha Principal", "Losa Deportiva"],
    ("Primaria", "Computación"): ["Sala de Innovación"],
    ("Secundaria", "Computación"): ["Centro de Cómputo"],
}
BLOQUES_EN_LABORATORIO = {("Secundaria", "Ciencia y Tecnología"): (1, ["Laboratorio de Ciencias"]),
                          ("Secundaria", "Arte y Cultura"): (1, ["Ambiente de Música"])}

# --- Docentes -----------------------------------------------------------------------
# (DNI, nombre, modalidad, condición, especialidades). Los 10 primeros vienen de la
# versión anterior de los datos y se conservan.
DOCENTES = [
    ("45231678", "Chambilla Quispe, Maria del Carmen", "Jornada completa", "Miembro del Consejo Directivo", ["Educación Religiosa", "Ciencias Sociales"]),
    ("41023456", "Apaza Mamani, Rosa Elvira", "Jornada completa", "Docente", ["Matemática", "Ciencia y Tecnología"]),
    ("42876543", "Quispe Huanca, Jose Luis", "Jornada completa", "Tutor", ["Comunicación", "Tutoría"]),
    ("43109876", "Flores Condori, Ana Maria", "Por horas", "Docente", ["Inglés"]),
    ("44567890", "Mamani Choque, Pedro Pablo", "Jornada completa", "Docente", ["Educación Física", "Danza"]),
    ("46234561", "Ticona Rivera, Lucia Fernanda", "Jornada completa", "Hermana de la Congregación", ["Educación Religiosa"]),
    ("47345672", "Paredes Suni, Carlos Alberto", "Por horas", "Docente", ["Arte y Cultura", "Danza"]),
    ("48456783", "Vilca Zevallos, Maria Elena", "Jornada completa", "Tutor", ["Matemática", "Computación", "Tutoría"]),
    ("49567894", "Huanca Salazar, Jorge Luis", "Jornada completa", "Docente", ["Ciencias Sociales", "Desarrollo Personal y Ciudadanía"]),
    ("40678905", "Cutipa Mendoza, Sofia Isabel", "Por horas", "Docente", ["Computación", "Comunicación"]),
    # Tutoras de aula de primaria (una por sección, polivalentes)
    ("70123401", "Benavente Lazo, Carmen Rosa", "Jornada completa", "Tutor", ["Matemática", "Comunicación", "Ciencia y Tecnología", "Ciencias Sociales", "Arte y Cultura", "Tutoría"]),
    ("70123402", "Cáceres Medina, Gladys Noemí", "Jornada completa", "Tutor", ["Matemática", "Comunicación", "Ciencia y Tecnología", "Ciencias Sociales", "Arte y Cultura", "Tutoría"]),
    ("70123403", "Linares Torres, Patricia Elena", "Jornada completa", "Tutor", ["Matemática", "Comunicación", "Ciencia y Tecnología", "Ciencias Sociales", "Arte y Cultura", "Tutoría"]),
    ("70123404", "Zúñiga Ramos, Milagros del Pilar", "Jornada completa", "Tutor", ["Matemática", "Comunicación", "Ciencia y Tecnología", "Ciencias Sociales", "Arte y Cultura", "Tutoría"]),
    ("70123405", "Delgado Pinto, Rocío Beatriz", "Jornada completa", "Tutor", ["Matemática", "Comunicación", "Ciencia y Tecnología", "Ciencias Sociales", "Arte y Cultura", "Tutoría"]),
    ("70123406", "Salas Cornejo, Verónica Isabel", "Jornada completa", "Tutor", ["Matemática", "Comunicación", "Ciencia y Tecnología", "Ciencias Sociales", "Arte y Cultura", "Tutoría"]),
    ("70123407", "Núñez Valdivia, Elizabeth Karina", "Jornada completa", "Tutor", ["Matemática", "Comunicación", "Ciencia y Tecnología", "Ciencias Sociales", "Arte y Cultura", "Tutoría"]),
    ("70123408", "Rivera Gutiérrez, Juana Teresa", "Jornada completa", "Tutor", ["Matemática", "Comunicación", "Ciencia y Tecnología", "Ciencias Sociales", "Arte y Cultura", "Tutoría"]),
    ("70123409", "Llerena Huamán, Sonia Marlene", "Jornada completa", "Tutor", ["Matemática", "Comunicación", "Ciencia y Tecnología", "Ciencias Sociales", "Arte y Cultura", "Tutoría"]),
    ("70123410", "Vargas Pacheco, Liliana Esther", "Jornada completa", "Tutor", ["Matemática", "Comunicación", "Ciencia y Tecnología", "Ciencias Sociales", "Arte y Cultura", "Tutoría"]),
    ("70123411", "Mendoza Arce, Fiorella Andrea", "Jornada completa", "Tutor", ["Matemática", "Comunicación", "Ciencia y Tecnología", "Ciencias Sociales", "Arte y Cultura", "Tutoría"]),
    ("70123412", "Polanco Begazo, Ruth Milagros", "Jornada completa", "Tutor", ["Matemática", "Comunicación", "Ciencia y Tecnología", "Ciencias Sociales", "Arte y Cultura", "Tutoría"]),
    # Especialistas
    ("71234501", "Condori Apaza, Luis Fernando", "Jornada completa", "Docente", ["Matemática", "Tutoría"]),
    ("71234502", "Ccama Yupanqui, Raúl Ernesto", "Jornada completa", "Tutor", ["Matemática", "Tutoría"]),
    ("71234503", "Pari Ticona, Edwin Rolando", "Por horas", "Docente", ["Matemática"]),
    ("71234504", "Gamarra Ortiz, Diana Carolina", "Jornada completa", "Tutor", ["Comunicación", "Tutoría"]),
    ("71234505", "Neyra Bustamante, Kelly Roxana", "Por horas", "Docente", ["Comunicación"]),
    ("71234506", "Aguilar Chávez, Martín Alonso", "Jornada completa", "Tutor", ["Ciencia y Tecnología", "Tutoría"]),
    ("71234507", "Rodríguez Lupaca, Yesenia Paola", "Jornada completa", "Docente", ["Ciencia y Tecnología"]),
    ("71234508", "Calla Machaca, Hugo Wilber", "Por horas", "Docente", ["Ciencia y Tecnología"]),
    ("71234509", "Málaga Rendón, Cecilia Ivonne", "Jornada completa", "Tutor", ["Ciencias Sociales", "Desarrollo Personal y Ciudadanía", "Tutoría"]),
    ("71234510", "Soto Carpio, Kevin Arturo", "Jornada completa", "Docente", ["Inglés"]),
    ("71234511", "Bedoya Franco, Jessica Mabel", "Por horas", "Docente", ["Inglés"]),
    ("71234512", "Torres Llanos, Wilfredo César", "Jornada completa", "Docente", ["Educación Física", "Danza"]),
    ("71234513", "Huarca Mollo, Silvia Marisol", "Jornada completa", "Docente", ["Educación Física"]),
    ("71234514", "Esquivel Paz, Giancarlo Iván", "Por horas", "Docente", ["Educación para el Trabajo", "Computación"]),
    ("71234515", "Castro Meza, Lourdes Amparo", "Jornada completa", "Hermana de la Congregación", ["Educación Religiosa", "Desarrollo Personal y Ciudadanía"]),
    ("71234516", "Ramos Vizcarra, Nancy Gloria", "Jornada completa", "Miembro del Consejo Directivo", ["Comunicación", "Tutoría"]),
    ("71234517", "Puma Quispe, Rubén Darío", "Jornada completa", "Miembro del Consejo Directivo", ["Matemática", "Tutoría"]),
    ("71234518", "Laura Ccori, Maribel Susana", "Por horas", "Docente", ["Arte y Cultura", "Danza"]),
    ("71234519", "Zegarra Olivares, Franco Javier", "Jornada completa", "Docente", ["Educación para el Trabajo", "Computación"]),
    ("71234520", "Chura Mamani, Elsa Victoria", "Por horas", "Docente", ["Inglés", "Desarrollo Personal y Ciudadanía"]),
]
CAPACIDAD = {"Jornada completa": 30, "Por horas": 20}  # bloques semanales máximos


def minutos(hora: str) -> int:
    h, m = hora.split(":")
    return int(h) * 60 + int(m)


class Ocupacion:
    """Registro de franjas ocupadas por clave (docente, espacio, sección)."""

    def __init__(self):
        self._ocupado: dict[tuple, list[tuple[int, int]]] = defaultdict(list)

    def libre(self, clave, periodo, dia, inicio, fin) -> bool:
        a, b = minutos(inicio), minutos(fin)
        return all(not (a < y and b > x) for x, y in self._ocupado[(clave, periodo, dia)])

    def ocupar(self, clave, periodo, dia, inicio, fin) -> None:
        self._ocupado[(clave, periodo, dia)].append((minutos(inicio), minutos(fin)))


def generar(semilla: int):
    rnd = random.Random(semilla)
    docentes = {d[0]: d for d in DOCENTES}
    carga = defaultdict(int)
    ocup = Ocupacion()
    actividades, participa, asignaciones = [], [], []
    nivel_de = {g[0]: g[2] for g in GRADOS}

    # Secciones: 2 por grado de primaria/secundaria (IDs 1..22) y 1 por grado de inicial.
    secciones = []
    for id_grado in range(1, 12):
        secciones += [(2 * id_grado - 1, "A", id_grado), (2 * id_grado, "B", id_grado)]
    secciones += [(23, "A", 12), (24, "A", 13), (25, "A", 14)]
    aula = {s: f"Aula {100 + s}" if s <= 12 else f"Aula {200 + s - 12}" for s in range(1, 23)}

    tutoras = [d[0] for d in DOCENTES if d[0].startswith("701234")]
    tutora_de = {s: tutoras[s - 1] for s in range(1, 13)}

    def elegir_docente(asignatura, bloques, excluir=()):
        candidatos = [d for d in DOCENTES if asignatura in d[4] and not d[0].startswith("701234")
                      and d[0] not in excluir and carga[d[0]] + bloques <= CAPACIDAD[d[2]]]
        if not candidatos:
            raise RuntimeError(f"Sin docente para {asignatura}")
        menor = min(carga[d[0]] for d in candidatos)
        return rnd.choice([d for d in candidatos if carga[d[0]] - menor <= 2])[0]

    def nueva_actividad(inicio, fin, dia, naturaleza, materia, periodo, espacio):
        actividades.append((len(actividades) + 1, inicio, fin, dia, naturaleza, materia, periodo, espacio))
        ocup.ocupar(("esp", espacio), periodo, dia, inicio, fin)
        return len(actividades)

    # --- Clases 2026 ------------------------------------------------------------
    for id_sec, _, id_grado in secciones[:22]:
        nivel = nivel_de[id_grado]
        franjas = [(d, i, f) for d in DIAS for (i, f) in BLOQUES[nivel]]
        plan = PLAN[nivel]
        # Docente por asignatura para esta sección
        docente_de = {}
        for asignatura, bloques in plan.items():
            if nivel == "Primaria" and asignatura in AREAS_TUTORA:
                docente_de[asignatura] = tutora_de[id_sec]
            elif asignatura == "Tutoría":
                docente_de[asignatura] = docente_de.get("Matemática") or elegir_docente("Tutoría", 1)
            else:
                docente_de[asignatura] = elegir_docente(asignatura, bloques)
            carga[docente_de[asignatura]] += bloques
        # Ordenar: primero lo más restringido (espacios compartidos, especialistas)
        orden = sorted(plan, key=lambda a: (
            (nivel, a) not in ESPACIO_ESPECIAL, docente_de[a] in tutoras, -carga[docente_de[a]], -plan[a]))
        por_dia = defaultdict(int)
        for asignatura in orden:
            dni = docente_de[asignatura]
            en_lab, lab = BLOQUES_EN_LABORATORIO.get((nivel, asignatura), (0, []))
            for n in range(plan[asignatura]):
                opciones_esp = ESPACIO_ESPECIAL.get((nivel, asignatura)) or (lab if n < en_lab else [aula[id_sec]])
                rnd.shuffle(franjas)
                franjas.sort(key=lambda f: por_dia[(asignatura, f[0])])
                colocado = False
                for dia, ini, fin in franjas:
                    if por_dia[(asignatura, dia)] >= 2:
                        continue
                    if not ocup.libre(("sec", id_sec), 2026, dia, ini, fin) or not ocup.libre(("doc", dni), 2026, dia, ini, fin):
                        continue
                    espacio = next((e for e in opciones_esp if ocup.libre(("esp", e), 2026, dia, ini, fin)), None)
                    if espacio is None:
                        continue
                    id_act = nueva_actividad(ini, fin, dia, "Clase", asignatura, 2026, espacio)
                    ocup.ocupar(("sec", id_sec), 2026, dia, ini, fin)
                    ocup.ocupar(("doc", dni), 2026, dia, ini, fin)
                    participa.append((id_act, id_sec))
                    asignaciones.append((dni, id_act, "Dicta clase"))
                    por_dia[(asignatura, dia)] += 1
                    franjas.remove((dia, ini, fin))
                    colocado = True
                    break
                if not colocado:
                    raise RuntimeError(f"No se pudo ubicar {asignatura} de la sección {id_sec}")

    # --- Recesos, consejos y pastoral 2026 ----------------------------------------
    def de_turno(dia, ini, fin, cantidad, preferidos):
        libres = [d for d in preferidos if ocup.libre(("doc", d), 2026, dia, ini, fin)]
        rnd.shuffle(libres)
        return libres[:cantidad]

    for nivel, (ini, fin, patio) in RECESO.items():
        sec_nivel = [s for s, _, g in secciones[:22] if nivel_de[g] == nivel]
        for dia in DIAS:
            id_act = nueva_actividad(ini, fin, dia, "Receso", None, 2026, patio)
            participa.extend((id_act, s) for s in sec_nivel)
            preferidos = tutoras if nivel == "Primaria" else [d[0] for d in DOCENTES if not d[0].startswith("701234")]
            elegidos = de_turno(dia, ini, fin, 3, preferidos)
            for k, dni in enumerate(elegidos):
                asignaciones.append((dni, id_act, "Refrigera con estudiantes" if k == 2 else "Cuida receso"))
                ocup.ocupar(("doc", dni), 2026, dia, ini, fin)

    consejo = [d[0] for d in DOCENTES if d[3] == "Miembro del Consejo Directivo"]
    hermanas = [d[0] for d in DOCENTES if d[3] == "Hermana de la Congregación"]
    for dia, ini, fin in (("Lunes", "07:00", "08:00"), ("Jueves", "07:00", "08:00")):
        id_act = nueva_actividad(ini, fin, dia, "Consejo", None, 2026, "Sala de Usos Múltiples")
        asignaciones.extend((dni, id_act, "Reunión") for dni in consejo)
    for dia, ini, fin, nivel in (("Miércoles", "13:00", "13:45", "Primaria"), ("Viernes", "14:00", "15:00", "Secundaria")):
        id_act = nueva_actividad(ini, fin, dia, "Pastoral", None, 2026, "Ambiente de Música")
        participa.extend((id_act, s) for s, _, g in secciones[:22] if nivel_de[g] == nivel)
        asignaciones.extend((dni, id_act, "Reunión") for dni in hermanas)

    # --- Histórico 2025: mismo horario de las secciones 5 y 15 -------------------------
    for id_sec in (5, 15):
        for id_act, sec in [p for p in participa if p[1] == id_sec]:
            a = actividades[id_act - 1]
            if a[4] != "Clase":
                continue
            nuevo = nueva_actividad(a[1], a[2], a[3], "Clase", a[5], 2025, a[7])
            participa.append((nuevo, id_sec))
            dni = next(d for d, act, _ in asignaciones if act == id_act)
            asignaciones.append((dni, nuevo, "Dicta clase"))

    especialidades = sorted({(a, d[0]) for d in DOCENTES for a in d[4]})
    plan_estudios = [(a, g, h) for g, _, nivel in GRADOS if nivel in PLAN for a, h in PLAN[nivel].items()]
    return secciones, actividades, participa, asignaciones, especialidades, plan_estudios, carga


def sql_valor(v) -> str:
    if v is None:
        return "NULL"
    if isinstance(v, int):
        return str(v)
    return "'" + str(v).replace("'", "''") + "'"


def insert(tabla: str, columnas: list[str], filas, comentario: str) -> str:
    cuerpo = ",\n".join("(" + ", ".join(sql_valor(v) for v in f) + ")" for f in filas)
    return f"-- {comentario} ({len(filas)} registros)\nINSERT INTO {tabla} ({', '.join(columnas)}) VALUES\n{cuerpo};\n"


def main() -> None:
    for intento in range(300):
        try:
            secciones, actividades, participa, asignaciones, especialidades, plan, carga = generar(SEMILLA + intento)
            break
        except RuntimeError:
            continue
    else:
        raise SystemExit("No se pudo generar un horario válido")

    partes = [
        "-- =========================================================================\n"
        "-- DATOS DE PRUEBA\n"
        "-- Proyecto: Asignación de Horarios y Carga Académica\n"
        "-- Generado por database/generador/generar_datos_prueba.py (no editar a mano).\n"
        "-- Colegio completo: Inicial, Primaria (6 grados x 2 secciones) y Secundaria\n"
        "-- (5 grados x 2 secciones), con horario semanal completo sin cruces de\n"
        "-- espacio ni de docente, recesos, consejos, pastoral e histórico 2025.\n"
        "-- =========================================================================\n"
        "USE bd_horarios_esclavas;\n",
        insert("Grado_Escolar", ["ID_Grado", "Nombre", "Nivel"], GRADOS, "Grados escolares"),
        insert("Seccion", ["ID_Seccion", "Letra_Identificadora", "ID_Grado"], secciones, "Secciones"),
        insert("Docente", ["DNI", "Nombre", "Modalidad", "Condicion_Especial"], [d[:4] for d in DOCENTES], "Docentes"),
        insert("Asignatura", ["Nombre_Materia", "Nivel_Exigencia"], ASIGNATURAS, "Asignaturas"),
        insert("Periodo_Academico", ["Anio_Lectivo", "Estado"], [(2025, "Cerrado"), (2026, "Activo")], "Periodos académicos"),
        insert("Espacio", ["Denominacion", "Categoria", "Limite_Grupos"], ESPACIOS, "Espacios / ambientes físicos"),
        insert("Especializado_En", ["Nombre_Asignatura", "DNI_Docente"], especialidades, "Especialidades docentes"),
        insert("Grado_Materia", ["Nombre_Asignatura", "ID_Grado", "Horas_Exigidas"], plan, "Plan de estudios (horas semanales)"),
        insert("Actividad", ["ID_Actividad", "Hora_Inicio", "Hora_Fin", "Dia", "Naturaleza", "Materia_Asignatura", "Periodo", "Espacio"],
               [(a[0], a[1] + ":00", a[2] + ":00", *a[3:]) for a in actividades], "Actividades (bloques de horario)"),
        insert("Seccion_Periodo", ["ID_Actividad", "ID_Seccion"], participa, "Participación de secciones en actividades"),
        insert("Docente_Actividad", ["DNI_Docente", "ID_Actividad", "Rol_Asumido"], asignaciones, "Carga docente por actividad"),
    ]
    SALIDA.write_text("\n".join(partes), encoding="utf-8", newline="\n")
    print(f"{SALIDA.name}: {len(DOCENTES)} docentes, {len(secciones)} secciones, {len(actividades)} actividades, "
          f"{len(participa)} participaciones, {len(asignaciones)} asignaciones docentes")
    print("Carga máxima:", max(carga.values()), "bloques")


if __name__ == "__main__":
    main()
