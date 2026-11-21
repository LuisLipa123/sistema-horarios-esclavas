"""Servidor MySQL portátil (versión entregable en carpeta, sin instalar nada).

S: esta clase solo gestiona el proceso mysqld que viaja dentro de la carpeta:
crear la base la primera vez, arrancarla, cargar los scripts y apagarla.
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Callable

import mysql.connector
from mysql.connector import Error

_SIN_VENTANA = getattr(subprocess, "CREATE_NO_WINDOW", 0)
MARCA_LISTO = "base_lista.txt"


def puerto_libre(desde: int, hasta: int | None = None) -> int:
    for puerto in range(desde, (hasta or desde + 50) + 1):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.bind(("127.0.0.1", puerto))
                return puerto
            except OSError:
                continue
    raise RuntimeError(f"No hay puertos libres entre {desde} y {hasta}")


class ErrorMySQLPortable(RuntimeError):
    pass


class MySQLPortable:
    def __init__(self, base: Path, puerto: int, avisar: Callable[[str], None] = print):
        self.base = base
        self.puerto = puerto
        self._avisar = avisar
        self._bin = base / "mysql" / "bin"
        self._datos = base / "datos"
        self._log = base / "datos_mysql.log"
        self._scripts = base / "database" / "init"
        self._proceso: subprocess.Popen | None = None
        self._job = None

    # --- Estado ------------------------------------------------------------
    @property
    def lista(self) -> bool:
        return (self._datos / MARCA_LISTO).exists()

    def _comunes(self) -> list[str]:
        return ["--no-defaults", f"--basedir={self.base / 'mysql'}", f"--datadir={self._datos}",
                f"--log-error={self._log}"]

    # --- Ciclo de vida -----------------------------------------------------
    def preparar(self) -> bool:
        """Crea el directorio de datos si no existe. Devuelve True si es nuevo."""
        if self.lista:
            return False
        if self._datos.exists():          # quedó a medias en un intento anterior
            shutil.rmtree(self._datos)
        self._avisar("Primera vez: creando la base de datos (puede tardar 1 o 2 minutos)...")
        resultado = subprocess.run(
            [str(self._bin / "mysqld.exe"), *self._comunes(), "--initialize-insecure"],
            creationflags=_SIN_VENTANA, capture_output=True, text=True)
        if resultado.returncode != 0:
            raise ErrorMySQLPortable("No se pudo inicializar MySQL.\n" + self._final_log())
        return True

    def iniciar(self, espera_max: float = 90) -> None:
        self._proceso = subprocess.Popen(
            [str(self._bin / "mysqld.exe"), *self._comunes(),
             f"--port={self.puerto}", "--bind-address=127.0.0.1", "--mysqlx=OFF",
             "--character-set-server=utf8mb4", "--collation-server=utf8mb4_spanish_ci",
             "--disable-log-bin", "--innodb-buffer-pool-size=64M"],
            creationflags=_SIN_VENTANA, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self._job = _atar_al_proceso_actual(self._proceso)
        limite = time.monotonic() + espera_max
        while time.monotonic() < limite:
            if self._proceso.poll() is not None:
                raise ErrorMySQLPortable("MySQL se detuvo al arrancar.\n" + self._final_log())
            try:
                mysql.connector.connect(host="127.0.0.1", port=self.puerto, user="root", password="",
                                        connection_timeout=2, ssl_disabled=True).close()
                return
            except Error:
                time.sleep(1)
        raise ErrorMySQLPortable("MySQL tardó demasiado en arrancar.\n" + self._final_log())

    def cargar_scripts(self) -> None:
        """Ejecuta database/init/*.sql en orden con el cliente mysql.exe
        (soporta DELIMITER, procedimientos y triggers)."""
        for script in sorted(self._scripts.glob("*.sql")):
            self._avisar(f"  Cargando {script.name}...")
            with open(script, "rb") as entrada:
                resultado = subprocess.run(
                    [str(self._bin / "mysql.exe"), "--protocol=TCP", "-h127.0.0.1",
                     f"-P{self.puerto}", "-uroot", "--default-character-set=utf8mb4"],
                    stdin=entrada, capture_output=True, creationflags=_SIN_VENTANA)
            if resultado.returncode != 0:
                error = resultado.stderr.decode("utf-8", "replace")
                raise ErrorMySQLPortable(f"Error al cargar {script.name}:\n{error}")
        (self._datos / MARCA_LISTO).write_text("Base creada con database/init.\n", encoding="utf-8")

    def detener(self) -> None:
        if self._proceso is None or self._proceso.poll() is not None:
            return
        try:
            cnx = mysql.connector.connect(host="127.0.0.1", port=self.puerto, user="root", password="",
                                          ssl_disabled=True)
            cnx.cmd_query("SHUTDOWN")
            cnx.close()
        except Error:
            pass
        try:
            self._proceso.wait(timeout=30)
        except subprocess.TimeoutExpired:
            self._proceso.kill()

    def _final_log(self, lineas: int = 15) -> str:
        try:
            texto = self._log.read_text(encoding="utf-8", errors="replace").splitlines()
            return "\n".join(texto[-lineas:])
        except OSError:
            return "(sin log)"


def _atar_al_proceso_actual(proceso: subprocess.Popen):
    """Windows: mete mysqld en un Job Object con KILL_ON_JOB_CLOSE, para que
    si Iniciar.exe termina de golpe (o se cierra la ventana) mysqld no quede
    huérfano bloqueando la carpeta 'datos'. Devuelve el handle del job, que
    debe mantenerse vivo mientras dure el programa."""
    if sys.platform != "win32":
        return None
    import ctypes
    from ctypes import wintypes

    class Basica(ctypes.Structure):
        _fields_ = [("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64),
                    ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                    ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                    ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD),
                    ("SchedulingClass", wintypes.DWORD)]

    class ContadoresIO(ctypes.Structure):
        _fields_ = [(n, ctypes.c_uint64) for n in ("Read", "Write", "Other", "ReadT", "WriteT", "OtherT")]

    class Extendida(ctypes.Structure):
        _fields_ = [("Basica", Basica), ("IO", ContadoresIO), ("ProcessMemoryLimit", ctypes.c_size_t),
                    ("JobMemoryLimit", ctypes.c_size_t), ("PeakProcessMemoryUsed", ctypes.c_size_t),
                    ("PeakJobMemoryUsed", ctypes.c_size_t)]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateJobObjectW.restype = wintypes.HANDLE
    kernel32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
    kernel32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
    kernel32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]

    job = kernel32.CreateJobObjectW(None, None)
    if not job:
        return None
    info = Extendida()
    info.Basica.LimitFlags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
    kernel32.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info))  # 9 = ExtendedLimitInformation
    kernel32.AssignProcessToJobObject(job, wintypes.HANDLE(int(proceso._handle)))
    return job


def carpeta_base() -> Path:
    """Carpeta de la versión portable: la indica Iniciar.bat en HORARIOS_BASE
    (si no, se usa el directorio actual)."""
    return Path(os.environ.get("HORARIOS_BASE") or Path.cwd()).resolve()
