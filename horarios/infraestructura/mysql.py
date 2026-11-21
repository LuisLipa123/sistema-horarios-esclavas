"""Implementación de los puertos con mysql-connector-python.

Es el ÚNICO módulo que importa el driver. Cambiar de motor (p. ej. a
PostgreSQL) solo requiere otra clase que cumpla los mismos protocolos.
"""

from __future__ import annotations

import re
from contextlib import closing, contextmanager
from typing import Any, Iterator, Sequence

import mysql.connector
from mysql.connector import Error

from horarios.config import ConfiguracionBD
from horarios.dominio.errores import ErrorConexion, OperacionRechazada
from horarios.dominio.puertos import Resultado

_IDENTIFICADOR = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


class ProveedorConexionMySQL:
    """S: solo abre conexiones."""

    def __init__(self, config: ConfiguracionBD):
        self._config = config

    @contextmanager
    def conexion(self) -> Iterator[Any]:
        try:
            cnx = mysql.connector.connect(
                host=self._config.host,
                port=self._config.puerto,
                user=self._config.usuario,
                password=self._config.password or "",
                database=self._config.base_datos,
                charset=self._config.charset,
                collation=self._config.collation,
                use_unicode=True,
                ssl_disabled=not self._config.ssl,
            )
        except Error as err:
            raise ErrorConexion(err.msg, err.errno) from err
        try:
            yield cnx
        finally:
            cnx.close()

    def verificar(self) -> None:
        with self.conexion():
            pass


class GatewayMySQL:
    """Cumple EjecutorProcedimientos, LectorProcedimientos y LectorTablas."""

    def __init__(self, proveedor: ProveedorConexionMySQL):
        self._proveedor = proveedor

    def ejecutar(self, procedimiento: str, parametros: Sequence[Any]) -> None:
        with self._proveedor.conexion() as cnx:
            try:
                with closing(cnx.cursor()) as cursor:
                    cursor.callproc(_validar(procedimiento), tuple(parametros))
                cnx.commit()
            except Error as err:
                cnx.rollback()
                raise OperacionRechazada(err.msg, err.errno) from err

    def consultar(self, procedimiento: str, parametros: Sequence[Any]) -> Resultado:
        with self._proveedor.conexion() as cnx:
            try:
                with closing(cnx.cursor()) as cursor:
                    cursor.callproc(_validar(procedimiento), tuple(parametros))
                    resultado = Resultado()
                    for conjunto in cursor.stored_results():
                        resultado = Resultado(
                            columnas=[c[0] for c in conjunto.description],
                            filas=conjunto.fetchall(),
                        )
                    return resultado
            except Error as err:
                raise OperacionRechazada(err.msg, err.errno) from err

    def listar(self, tabla: str, orden: str = "") -> Resultado:
        # El nombre de tabla y el ORDER BY vienen del catálogo (no del usuario),
        # aun así se valida el identificador.
        sql = f"SELECT * FROM `{_validar(tabla)}` {orden}"
        with self._proveedor.conexion() as cnx:
            try:
                with closing(cnx.cursor()) as cursor:
                    cursor.execute(sql)
                    return Resultado(
                        columnas=[c[0] for c in cursor.description],
                        filas=cursor.fetchall(),
                    )
            except Error as err:
                raise OperacionRechazada(err.msg, err.errno) from err


def _validar(identificador: str) -> str:
    if not _IDENTIFICADOR.fullmatch(identificador):
        raise ValueError(f"Identificador SQL inválido: {identificador!r}")
    return identificador
