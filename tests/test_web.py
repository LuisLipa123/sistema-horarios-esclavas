from datetime import timedelta

import pytest

from horarios.bootstrap import construir_web
from horarios.dominio.campos import ValorInvalido, procesar_campos
from horarios.catalogo.entidades import ACTIVIDAD
from horarios.dominio.puertos import Resultado
from horarios.servicios.horarios import ServicioHorarios, hhmm
from horarios.web.peticiones import Peticion
from tests.dobles import GatewayFalso

HORARIO_SECCION = Resultado(
    ["Grado", "Nivel", "Seccion", "Dia", "Hora_Inicio", "Hora_Fin", "Naturaleza", "Asignatura", "Espacio"],
    [("3°", "Primaria", "A", "Lunes", timedelta(hours=8), timedelta(hours=8, minutes=45), "Clase", "Matemática", "Aula 101"),
     ("3°", "Primaria", "A", "Martes", timedelta(hours=8), timedelta(hours=8, minutes=45), "Clase", "Comunicación", "Aula 101"),
     ("3°", "Primaria", "A", "Lunes", timedelta(hours=9, minutes=30), timedelta(hours=9, minutes=45), "Receso", "—", "Patio")],
)


def get(app, ruta, **consulta):
    return app.resolver(Peticion("GET", ruta, consulta))


def post(app, ruta, **formulario):
    return app.resolver(Peticion("POST", ruta, {}, formulario))


# --- Servicio de horarios ----------------------------------------------------

def test_hhmm_convierte_timedelta_y_texto():
    assert hhmm(timedelta(hours=7, minutes=5)) == "07:05"
    assert hhmm("13:30:00") == "13:30"


def test_grilla_de_seccion_agrupa_por_franja_y_dia():
    gateway = GatewayFalso(procedimientos={"sp_reporte_01_horario_seccion": HORARIO_SECCION})
    grilla = ServicioHorarios(gateway, gateway).horario_seccion(5)
    assert grilla.titulo == "3° Primaria - Sección A"
    assert grilla.franjas == [("08:00", "08:45"), ("09:30", "09:45")]
    assert grilla.bloques(("08:00", "08:45"), "Lunes")[0].titulo == "Matemática"
    receso = grilla.bloques(("09:30", "09:45"), "Lunes")[0]
    assert receso.titulo == "Receso" and not receso.es_clase
    assert grilla.bloques(("09:30", "09:45"), "Viernes") == []


def test_procesar_campos_omite_asignatura_si_no_es_clase():
    textos = {"id_actividad": "1", "hora_inicio": "10:00", "hora_fin": "10:30", "dia": "Lunes",
              "naturaleza": "Receso", "asignatura": "Ignorada", "anio": "2026", "espacio": "Patio"}
    assert procesar_campos(ACTIVIDAD.insertar.campos, textos)["asignatura"] is None
    with pytest.raises(ValorInvalido, match="Hora de fin"):
        procesar_campos(ACTIVIDAD.insertar.campos, {**textos, "hora_fin": "99:99"})


# --- Páginas -----------------------------------------------------------------

def test_inicio_y_404():
    app = construir_web(GatewayFalso())
    assert "Horarios semanales" in get(app, "/").cuerpo
    assert get(app, "/no-existe").estado == 404


def test_pagina_de_tabla_muestra_formularios_y_listado_escapado():
    gateway = GatewayFalso(resultado=Resultado(["Nombre"], [("<script>x</script>",)]))
    html = get(construir_web(gateway), "/tablas/grado_escolar").cuerpo
    assert 'action="/tablas/grado_escolar/insertar"' in html
    assert 'action="/tablas/grado_escolar/eliminar"' in html
    assert "&lt;script&gt;" in html and "<script>x" not in html


def test_tabla_sin_modificar_no_tiene_ese_formulario():
    html = get(construir_web(GatewayFalso()), "/tablas/especializado_en").cuerpo
    assert "/especializado_en/modificar" not in html


def test_insertar_ok_redirige_con_mensaje():
    gateway = GatewayFalso()
    r = post(construir_web(gateway), "/tablas/grado_escolar/insertar", id_grado="12", nombre="6°", nivel="Secundaria")
    assert r.estado == 303 and r.cabeceras["Location"].startswith("/tablas/grado_escolar?ok=")
    assert gateway.llamadas == [("sp_insertar_grado_escolar", (12, "6°", "Secundaria"))]


def test_insertar_invalido_no_llama_a_la_bd_y_conserva_datos():
    gateway = GatewayFalso()
    r = post(construir_web(gateway), "/tablas/grado_escolar/insertar", id_grado="abc", nombre="6°", nivel="Primaria")
    assert r.estado == 400 and "ID de grado" in r.cuerpo and 'value="6°"' in r.cuerpo
    assert gateway.llamadas == []


def test_rechazo_de_trigger_se_muestra():
    gateway = GatewayFalso(rechazar_con="Cruce de horario: el espacio ya está ocupado")
    r = post(construir_web(gateway), "/tablas/actividad/eliminar", id_actividad="1")
    assert r.estado == 400 and "Cruce de horario" in r.cuerpo


def test_reporte_se_genera_con_parametros():
    gateway = GatewayFalso()
    html = get(construir_web(gateway), "/reportes/1", id_seccion="5", generar="1").cuerpo
    assert gateway.llamadas == [("sp_reporte_01_horario_seccion", (5,))]
    assert "<table>" in html


def test_pagina_horarios_dibuja_grilla():
    gateway = GatewayFalso(
        procedimientos={"sp_reporte_01_horario_seccion": HORARIO_SECCION},
        tablas={"Seccion": Resultado(["ID_Seccion", "Letra_Identificadora", "ID_Grado"], [(5, "A", 3)]),
                "Grado_Escolar": Resultado(["ID_Grado", "Nombre", "Nivel"], [(3, "3°", "Primaria")]),
                "Docente": Resultado(["DNI", "Nombre"], []),
                "Espacio": Resultado(["Denominacion"], [])},
    )
    html = get(construir_web(gateway), "/horarios", seccion="5").cuerpo
    assert "3° Primaria - A (ID 5)" in html
    assert "<th>Miércoles</th>" in html and "Matemática" in html and "<td>08:00<br>08:45</td>" in html
