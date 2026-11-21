"""Arma la carpeta entregable dist/HorariosEsclavas (+ .zip).

Uso (en Windows, desde la raíz del proyecto):
    pip install -r requirements-dev.txt
    python empaquetado/construir_portable.py [--mysql "C:\\Program Files\\MySQL\\MySQL Server 8.4"]

La carpeta NO contiene ningún ejecutable sin firma digital, para que Windows
(Smart App Control / SmartScreen) no la bloquee:
  * python\   Python "embeddable" oficial de python.org (firmado por la PSF).
  * mysql\    mysqld y el cliente mysql de una instalación de MySQL Server
              (firmados por Oracle) + runtime de Visual C++ (firmado por Microsoft).
  * app\      El código del sistema (.py) y mysql-connector en modo Python puro.
  * Iniciar.bat lanza todo con doble clic.
"""

from __future__ import annotations

import argparse
import glob
import os
import shutil
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

import pefile

RAIZ = Path(__file__).resolve().parent.parent
DIST = RAIZ / "dist"
CACHE = RAIZ / "build" / "cache"
SALIDA = DIST / "HorariosEsclavas"
SYSTEM32 = Path(os.environ.get("SystemRoot", r"C:\Windows")) / "System32"
RUNTIME_VC = ("vcruntime", "msvcp", "concrt")
VERSION_PY = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"

INICIAR_BAT = r"""@echo off
chcp 65001 >nul
title Sistema de Horarios - Esclavas del Sagrado Corazon de Jesus
cd /d "%~dp0"
set "HORARIOS_BASE=%~dp0"
"%~dp0python\python.exe" -X utf8 -m horarios.portable
if errorlevel 1 pause
"""


# --- MySQL --------------------------------------------------------------------

def buscar_mysql() -> Path:
    candidatos = sorted(glob.glob(r"C:\Program Files\MySQL\MySQL Server *"), reverse=True)
    if not candidatos:
        sys.exit("No se encontró MySQL Server. Indica la ruta con --mysql.")
    return Path(candidatos[0])


def dependencias(exe: Path, carpeta: Path) -> tuple[set[str], set[str]]:
    """DLLs de MySQL y del runtime VC++ que necesita `exe` (recursivo)."""
    propias, runtime, vistas = set(), set(), set()

    def recorrer(ruta: Path) -> None:
        pe = pefile.PE(str(ruta), fast_load=True)
        pe.parse_data_directories(directories=[
            pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_IMPORT"],
            pefile.DIRECTORY_ENTRY["IMAGE_DIRECTORY_ENTRY_DELAY_IMPORT"]])
        entradas = list(getattr(pe, "DIRECTORY_ENTRY_IMPORT", [])) + list(getattr(pe, "DIRECTORY_ENTRY_DELAY_IMPORT", []))
        for entrada in entradas:
            nombre = entrada.dll.decode()
            if nombre.lower() in vistas:
                continue
            vistas.add(nombre.lower())
            if (carpeta / nombre).exists():
                propias.add(nombre)
                recorrer(carpeta / nombre)
            elif nombre.lower().startswith(RUNTIME_VC):
                runtime.add(nombre)

    recorrer(exe)
    return propias, runtime


def copiar_mysql(origen: Path) -> None:
    bin_origen, bin_destino = origen / "bin", SALIDA / "mysql" / "bin"
    bin_destino.mkdir(parents=True)
    propias, runtime = set(), set()
    for exe in ("mysqld.exe", "mysql.exe"):
        shutil.copy2(bin_origen / exe, bin_destino)
        p, r = dependencias(bin_origen / exe, bin_origen)
        propias |= p
        runtime |= r
    for dll in sorted(propias):
        shutil.copy2(bin_origen / dll, bin_destino)
    for dll in sorted(runtime):
        shutil.copy2(SYSTEM32 / dll, bin_destino)
    shutil.copytree(origen / "share", SALIDA / "mysql" / "share")
    if (origen / "lib" / "private").exists():  # datos ICU para REGEXP
        shutil.copytree(origen / "lib" / "private", SALIDA / "mysql" / "lib" / "private")
    for licencia in ("LICENSE", "README"):
        if (origen / licencia).exists():
            shutil.copy2(origen / licencia, SALIDA / "mysql" / licencia)
    print(f"  MySQL: mysqld.exe, mysql.exe + {sorted(propias)} + runtime {sorted(runtime)}")


# --- Python portátil y aplicación ----------------------------------------------

def copiar_python() -> None:
    nombre = f"python-{VERSION_PY}-embed-amd64.zip"
    archivo = CACHE / nombre
    if not archivo.exists():
        CACHE.mkdir(parents=True, exist_ok=True)
        url = f"https://www.python.org/ftp/python/{VERSION_PY}/{nombre}"
        print(f"  Descargando {url}")
        urllib.request.urlretrieve(url, archivo)
    destino = SALIDA / "python"
    with zipfile.ZipFile(archivo) as z:
        z.extractall(destino)
    pth = next(destino.glob("python*._pth"))
    lineas = [l for l in pth.read_text().splitlines() if l and not l.startswith("#")]
    pth.write_text("\n".join(lineas + [r"..\app", r"..\app\lib"]) + "\n")
    print(f"  Python {VERSION_PY} embeddable")


def copiar_app() -> None:
    app = SALIDA / "app"
    shutil.copytree(RAIZ / "horarios", app / "horarios", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    lib = app / "lib"
    subprocess.run([sys.executable, "-m", "pip", "install", "--quiet", "--no-deps", "--target", str(lib),
                    "mysql-connector-python"], check=True)
    # Solo el modo Python puro: fuera extensiones C, DLLs, X DevAPI y metadatos.
    for patron in ("**/*.pyd", "**/*.dll", "**/__pycache__"):
        for ruta in lib.glob(patron):
            shutil.rmtree(ruta) if ruta.is_dir() else ruta.unlink()
    for carpeta in ("mysqlx", "bin"):
        shutil.rmtree(lib / carpeta, ignore_errors=True)
    print("  App + mysql-connector (Python puro)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--mysql", type=Path, help="carpeta de MySQL Server (por defecto, la más reciente)")
    parser.add_argument("--sin-zip", action="store_true")
    args = parser.parse_args()
    origen = args.mysql or buscar_mysql()

    print(f"Armando {SALIDA} con MySQL de {origen}")
    if SALIDA.exists():
        shutil.rmtree(SALIDA)
    SALIDA.mkdir(parents=True)

    copiar_mysql(origen)
    copiar_python()
    copiar_app()
    shutil.copytree(RAIZ / "database" / "init", SALIDA / "database" / "init")
    shutil.copy2(RAIZ / "empaquetado" / "LEEME.txt", SALIDA)
    (SALIDA / "Iniciar.bat").write_text(INICIAR_BAT.replace("\n", "\r\n"), encoding="utf-8", newline="")

    if not args.sin_zip:
        destino = DIST / "HorariosEsclavas.zip"
        destino.unlink(missing_ok=True)
        archivo = shutil.make_archive(str(destino.with_suffix("")), "zip", DIST, "HorariosEsclavas")
        print(f"ZIP: {archivo} ({Path(archivo).stat().st_size / 1e6:.0f} MB)")
    print("Listo.")


if __name__ == "__main__":
    main()
