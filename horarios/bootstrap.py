"""Raíz de composición: el ÚNICO lugar donde se crean y conectan las piezas.

Aquí se aplica la Inversión de Dependencias: se instancia la implementación
concreta (MySQL) y se inyecta en servicios y pantallas, que solo conocen
abstracciones.
"""

from __future__ import annotations

import sys
import time
from dataclasses import replace
from getpass import getpass

from horarios.catalogo.entidades import ENTIDADES
from horarios.catalogo.reportes import REPORTES
from horarios.config import ConfiguracionBD
from horarios.dominio.errores import ErrorConexion
from horarios.infraestructura.mysql import GatewayMySQL, ProveedorConexionMySQL
from horarios.servicios.crud import ServicioCrud
from horarios.servicios.reportes import ServicioReportes
from horarios.ui.consola import Consola, ConsolaEstandar
from horarios.ui.formulario import Formulario
from horarios.ui.menus import MenuPrincipal, PantallaCrud, PantallaReportes

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
            consola.mostrar(f"✘ No se pudo conectar: {err.mensaje}")
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
    gateway = GatewayMySQL(proveedor)
    formulario = Formulario(consola)
    servicio_crud = ServicioCrud(ejecutor=gateway, lector=gateway)
    servicio_reportes = ServicioReportes(lector=gateway)

    pantallas = [PantallaCrud(consola, e, servicio_crud, formulario) for e in ENTIDADES]
    pantallas.append(PantallaReportes(consola, REPORTES, servicio_reportes, formulario))
    return MenuPrincipal(consola, pantallas)


def main() -> None:
    consola = ConsolaEstandar()
    config = ConfiguracionBD.desde_entorno()
    proveedor = conectar(config, consola)
    if proveedor is None:
        consola.mostrar("No se pudo establecer la conexión con MySQL. "
                        "Revisa usuario, contraseña y que el servicio esté activo.")
        sys.exit(1)
    consola.mostrar(f"✔ Conectado a {config.base_datos} en {config.host}:{config.puerto}.")
    try:
        construir_app(proveedor, consola).abrir()
    except (KeyboardInterrupt, EOFError):
        consola.mostrar("\nHasta luego.")
