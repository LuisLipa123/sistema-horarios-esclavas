"""Raíz de composición: el ÚNICO lugar donde se crean y conectan las piezas.

Aquí se aplica la Inversión de Dependencias: se instancia la implementación
concreta (MySQL) y se inyecta en servicios y pantallas, que solo conocen
abstracciones.
"""

from __future__ import annotations

import argparse
import os
import sys
import time
import webbrowser
from dataclasses import replace
from getpass import getpass

from horarios.catalogo.entidades import ENTIDADES
from horarios.catalogo.reportes import REPORTES
from horarios.config import ConfiguracionBD
from horarios.dominio.errores import ErrorConexion
from horarios.infraestructura.mysql import GatewayMySQL, ProveedorConexionMySQL
from horarios.servicios.crud import ServicioCrud
from horarios.servicios.horarios import ServicioHorarios
from horarios.servicios.reportes import ServicioReportes
from horarios.ui.consola import Consola, ConsolaEstandar
from horarios.ui.formulario import Formulario
from horarios.ui.menus import MenuPrincipal, PantallaCrud, PantallaReportes
from horarios.web.controladores import (
    ControladorEntidades,
    ControladorHorarios,
    ControladorInicio,
    ControladorReportes,
)
from horarios.web.peticiones import Enrutador
from horarios.web.servidor import crear_servidor

INTENTOS_PASSWORD = 3
INTENTOS_SERVIDOR = 10   # útil en Docker mientras MySQL termina de arrancar
ESPERA_SEGUNDOS = 3


def conectar(config: ConfiguracionBD, consola: Consola) -> ProveedorConexionMySQL | None:
    intentos_password = intentos_servidor = 0
    while True:
        if config.password is None:
            config = config.con_password(
                getpass(f"Contraseña de MySQL para {config.usuario}@{config.host}: "))
        proveedor = ProveedorConexionMySQL(config)
        try:
            proveedor.verificar()
            return proveedor
        except ErrorConexion as err:
            consola.mostrar(f"Error: no se pudo conectar: {err.mensaje}")
            if err.es_acceso_denegado and sys.stdin.isatty():
                intentos_password += 1
                if intentos_password >= INTENTOS_PASSWORD:
                    return None
                config = replace(config, password=None)
            elif err.es_servidor_no_disponible:
                intentos_servidor += 1
                if intentos_servidor >= INTENTOS_SERVIDOR:
                    return None
                consola.mostrar(f"  Reintentando en {ESPERA_SEGUNDOS} s...")
                time.sleep(ESPERA_SEGUNDOS)
            else:
                return None


def construir_app(proveedor: ProveedorConexionMySQL, consola: Consola) -> MenuPrincipal:
    """Interfaz de consola (modo --consola)."""
    gateway = GatewayMySQL(proveedor)
    formulario = Formulario(consola)
    servicio_crud = ServicioCrud(ejecutor=gateway, lector=gateway)
    servicio_reportes = ServicioReportes(lector=gateway)

    pantallas = [PantallaCrud(consola, e, servicio_crud, formulario) for e in ENTIDADES]
    pantallas.append(PantallaReportes(consola, REPORTES, servicio_reportes, formulario))
    return MenuPrincipal(consola, pantallas)


def construir_web(gateway) -> Enrutador:
    """Interfaz gráfica web. Recibe cualquier objeto que cumpla los puertos
    (MySQL en producción, un doble en memoria en las pruebas)."""
    inicio = ControladorInicio(ENTIDADES, REPORTES)
    tablas = ControladorEntidades(ENTIDADES, ServicioCrud(ejecutor=gateway, lector=gateway))
    reportes = ControladorReportes(REPORTES, ServicioReportes(lector=gateway))
    horarios = ControladorHorarios(ServicioHorarios(procedimientos=gateway, tablas=gateway))

    enrutador = Enrutador(no_encontrado=inicio.no_encontrado)
    enrutador.agregar("GET", r"/", inicio.inicio)
    enrutador.agregar("GET", r"/horarios", horarios.ver)
    enrutador.agregar("GET", r"/tablas", tablas.indice)
    enrutador.agregar("GET", r"/tablas/(?P<tabla>\w+)", tablas.ver)
    enrutador.agregar("POST", r"/tablas/(?P<tabla>\w+)/(?P<accion>\w+)", tablas.ejecutar)
    enrutador.agregar("GET", r"/reportes", reportes.indice)
    enrutador.agregar("GET", r"/reportes/(?P<numero>\d+)", reportes.ver)
    return enrutador


def iniciar_web(proveedor: ProveedorConexionMySQL, consola: Consola) -> None:
    host = os.environ.get("WEB_HOST", "127.0.0.1")
    puerto = int(os.environ.get("WEB_PORT", 8000))
    servidor = crear_servidor(construir_web(GatewayMySQL(proveedor)), host, puerto)
    url = f"http://localhost:{puerto}"
    consola.mostrar(f"Interfaz gráfica disponible en {url}  (Ctrl+C para detener)")
    if os.environ.get("ABRIR_NAVEGADOR", "1") != "0":
        webbrowser.open(url)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        consola.mostrar("\nServidor detenido.")
    finally:
        servidor.server_close()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(prog="horarios", description=__doc__.splitlines()[0])
    parser.add_argument("--consola", action="store_true", help="usar la interfaz de texto en vez de la web")
    args = parser.parse_args(argv)

    consola = ConsolaEstandar()
    config = ConfiguracionBD.desde_entorno()
    proveedor = conectar(config, consola)
    if proveedor is None:
        consola.mostrar("No se pudo establecer la conexión con MySQL. "
                        "Revisa usuario, contraseña y que el servicio esté activo.")
        sys.exit(1)
    consola.mostrar(f"Conectado a {config.base_datos} en {config.host}:{config.puerto}.")

    if not args.consola:
        iniciar_web(proveedor, consola)
        return
    try:
        construir_app(proveedor, consola).abrir()
    except (KeyboardInterrupt, EOFError):
        consola.mostrar("\nHasta luego.")
