import pytest

from horarios.dominio.campos import CampoEntero, CampoHora, CampoOpcion, CampoTexto, ValorInvalido


def test_entero_valido_y_minimo():
    campo = CampoEntero("id", "ID", minimo=1)
    assert campo.procesar(" 5 ") == 5
    with pytest.raises(ValorInvalido):
        campo.procesar("0")
    with pytest.raises(ValorInvalido):
        campo.procesar("abc")


def test_obligatorio_y_opcional():
    with pytest.raises(ValorInvalido, match="obligatorio"):
        CampoTexto("n", "Nombre").procesar("   ")
    assert CampoTexto("n", "Nombre", opcional=True).procesar("") is None


def test_opcion_respeta_capitalizacion_oficial():
    campo = CampoOpcion("dia", "Día", opciones=("Lunes", "Miércoles"))
    assert campo.procesar("miércoles") == "Miércoles"
    with pytest.raises(ValorInvalido):
        campo.procesar("Sábado")


def test_hora_se_normaliza():
    campo = CampoHora("h", "Hora")
    assert campo.procesar("8:05") == "08:05:00"
    for invalida in ("25:00", "08:60", "0830", "ocho"):
        with pytest.raises(ValorInvalido):
            campo.procesar(invalida)


def test_dni_con_patron():
    campo = CampoTexto("dni", "DNI", patron=r"\d{8}")
    assert campo.procesar("12345678") == "12345678"
    with pytest.raises(ValorInvalido):
        campo.procesar("1234")
