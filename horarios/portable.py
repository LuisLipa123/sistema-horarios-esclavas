"""Punto de entrada de la versión portable (Iniciar.bat).

Arranca el MySQL que viaja en la carpeta, crea la base la primera vez con
database/init/*.sql, levanta la interfaz web y abre el navegador.
"""

from __future__ import annotations

import ctypes
import sys

from horarios.bootstrap import servir_web
from horarios.config import ConfiguracionBD
from horarios.dominio.errores import ErrorBaseDatos
from horarios.infraestructura.mysql import ProveedorConexionMySQL
from horarios.infraestructura.mysql_portable import (
    ErrorMySQLPortable,
    MySQLPortable,
    carpeta_base,
    puerto_libre,
)
from horarios.ui.consola import ConsolaEstandar

BANNER = """
==============================================================
  SISTEMA DE ASIGNACION DE HORARIOS Y CARGA ACADEMICA
  Colegio Particular Esclavas del Sagrado Corazon de Jesus
==============================================================
  No cierres esta ventana mientras uses el sistema.
  Para salir, cierra esta ventana o presiona Ctrl+C.
"""


def _al_cerrar_ventana(accion) -> None:
    """Apaga MySQL ordenadamente si el usuario cierra la ventana (Windows)."""
    if sys.platform != "win32":
        return
    TIPO = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_uint)

    def manejador(evento: int) -> bool:
        accion()
        return False

    _al_cerrar_ventana.referencia = TIPO(manejador)  # evita que el GC lo libere
    ctypes.windll.kernel32.SetConsoleCtrlHandler(_al_cerrar_ventana.referencia, True)


def main() -> None:
    try:  # que los mensajes aparezcan al instante
        sys.stdout.reconfigure(line_buffering=True, encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    consola = ConsolaEstandar()
    consola.mostrar(BANNER)
    base = carpeta_base()
    servidor_bd = MySQLPortable(base, puerto_libre(3399), avisar=consola.mostrar)
    try:
        nueva = servidor_bd.preparar()
        consola.mostrar("Iniciando base de datos...")
        servidor_bd.iniciar()
        _al_cerrar_ventana(servidor_bd.detener)
        if nueva:
            servidor_bd.cargar_scripts()
            consola.mostrar("Base de datos creada con los datos de prueba.")
        config = ConfiguracionBD(host="127.0.0.1", puerto=servidor_bd.puerto, usuario="root",
                                 password="", ssl=False)
        proveedor = ProveedorConexionMySQL(config)
        proveedor.verificar()
        servir_web(proveedor, consola, host="127.0.0.1", puerto=puerto_libre(8000, 8100))
    except (ErrorMySQLPortable, ErrorBaseDatos, OSError) as err:
        consola.mostrar(f"\nERROR: {err}")
        consola.mostrar(f"Revisa el archivo {base / 'datos_mysql.log'}")
        try:
            input("\nPresiona Enter para cerrar...")
        except EOFError:
            pass
    finally:
        consola.mostrar("Cerrando la base de datos...")
        servidor_bd.detener()


if __name__ == "__main__":
    main()
