import pytest

from horarios.catalogo.entidades import ACTIVIDAD, ENTIDADES, GRADO_ESCOLAR
from horarios.catalogo.reportes import REPORTES
from horarios.dominio.errores import OperacionRechazada
from horarios.servicios.crud import ServicioCrud
from horarios.servicios.reportes import ServicioReportes
from tests.dobles import GatewayFalso


def test_crud_pasa_parametros_en_orden_del_procedimiento():
    gateway = GatewayFalso()
    servicio = ServicioCrud(gateway, gateway)
    servicio.ejecutar(GRADO_ESCOLAR.insertar, {"nivel": "Primaria", "id_grado": 7, "nombre": "7°"})
    assert gateway.llamadas == [("sp_insertar_grado_escolar", (7, "7°", "Primaria"))]


def test_campo_no_visible_se_envia_como_null():
    gateway = GatewayFalso()
    valores = {"id_actividad": 1, "hora_inicio": "08:00:00", "hora_fin": "08:45:00", "dia": "Lunes",
               "naturaleza": "Receso", "asignatura": None, "anio": 2026, "espacio": "Patio"}
    ServicioCrud(gateway, gateway).ejecutar(ACTIVIDAD.insertar, valores)
    assert gateway.llamadas[0][1] == (1, "08:00:00", "08:45:00", "Lunes", "Receso", None, 2026, "Patio")


def test_rechazo_de_la_bd_se_propaga():
    gateway = GatewayFalso(rechazar_con="Cruce de horario")
    with pytest.raises(OperacionRechazada, match="Cruce"):
        ServicioCrud(gateway, gateway).ejecutar(GRADO_ESCOLAR.eliminar, {"id_grado": 1})


def test_listar_usa_tabla_y_orden_del_catalogo():
    gateway = GatewayFalso()
    ServicioCrud(gateway, gateway).listar(GRADO_ESCOLAR)
    assert gateway.listados == [("Grado_Escolar", "ORDER BY ID_Grado")]


def test_reporte_sin_parametros():
    gateway = GatewayFalso()
    reporte = next(r for r in REPORTES if r.procedimiento.endswith("condicion_especial"))
    ServicioReportes(gateway).generar(reporte, {})
    assert gateway.llamadas == [(reporte.procedimiento, ())]


def test_catalogo_completo():
    assert len(ENTIDADES) == 11
    assert len(REPORTES) == 10
    operaciones = [op for e in ENTIDADES for op in (e.insertar, e.modificar, e.eliminar) if op]
    assert len(operaciones) == 31  # = procedimientos de 02_procedimientos.sql
    for op in operaciones:
        nombres = [c.nombre for c in op.campos]
        assert len(nombres) == len(set(nombres)), op.procedimiento
