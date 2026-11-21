from horarios.catalogo.entidades import ACTIVIDAD, ESPECIALIZADO_EN, GRADO_ESCOLAR
from horarios.dominio.puertos import Resultado
from horarios.servicios.crud import ServicioCrud
from horarios.ui.formulario import Formulario
from horarios.ui.menus import PantallaCrud
from horarios.ui.tabla import formatear_tabla
from tests.dobles import ConsolaFalsa, GatewayFalso


def test_formulario_reintenta_hasta_dato_valido():
    consola = ConsolaFalsa(["x", "7", "7°", "primaria"])
    valores = Formulario(consola).completar(GRADO_ESCOLAR.insertar.campos)
    assert valores == {"id_grado": 7, "nombre": "7°", "nivel": "Primaria"}
    assert "Ingresa un número entero válido." in consola.texto


def test_asignatura_solo_se_pide_si_es_clase():
    entradas_receso = ["1", "10:00", "10:30", "lunes", "receso", "2026", "Patio"]
    valores = Formulario(ConsolaFalsa(entradas_receso)).completar(ACTIVIDAD.insertar.campos)
    assert valores["asignatura"] is None

    entradas_clase = ["2", "08:00", "08:45", "lunes", "clase", "Matemática", "2026", "Aula 101"]
    valores = Formulario(ConsolaFalsa(entradas_clase)).completar(ACTIVIDAD.insertar.campos)
    assert valores["asignatura"] == "Matemática"


def test_pantalla_crud_inserta_y_muestra_rechazo():
    gateway = GatewayFalso(rechazar_con="Duplicate entry")
    consola = ConsolaFalsa(["1", "1", "3°", "Primaria", "0"])
    PantallaCrud(consola, GRADO_ESCOLAR, ServicioCrud(gateway, gateway), Formulario(consola)).abrir()
    assert gateway.llamadas == [("sp_insertar_grado_escolar", (1, "3°", "Primaria"))]
    assert "rechazó la operación: Duplicate entry" in consola.texto


def test_pantalla_sin_modificar_no_ofrece_esa_opcion():
    gateway = GatewayFalso()
    consola = ConsolaFalsa([])
    pantalla = PantallaCrud(consola, ESPECIALIZADO_EN, ServicioCrud(gateway, gateway), Formulario(consola))
    assert [nombre for nombre, _ in pantalla.opciones()] == ["Insertar", "Eliminar", "Listar"]


def test_formatear_tabla():
    texto = formatear_tabla(Resultado(["ID", "Nombre"], [(1, "Ana"), (10, None)]))
    assert texto.splitlines() == ["ID | Nombre", "---+-------", "1  | Ana", "10 |"]
    assert formatear_tabla(Resultado()) == "(sin resultados)"
