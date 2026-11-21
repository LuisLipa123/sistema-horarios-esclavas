"""Configuración de la conexión (S: solo sabe leer la configuración).

Los valores se toman de variables de entorno para que el mismo código sirva
en local (MySQL Workbench) y dentro de Docker, sin contraseñas en el código.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, replace
from typing import Mapping


@dataclass(frozen=True)
class ConfiguracionBD:
    host: str = "localhost"
    puerto: int = 3306
    usuario: str = "root"
    password: str | None = None
    base_datos: str = "bd_horarios_esclavas"
    charset: str = "utf8mb4"
    collation: str = "utf8mb4_spanish_ci"
    ssl: bool = True   # el modo portable (127.0.0.1) lo desactiva

    @classmethod
    def desde_entorno(cls, entorno: Mapping[str, str] = os.environ) -> "ConfiguracionBD":
        por_defecto = cls()
        return cls(
            host=entorno.get("DB_HOST", por_defecto.host),
            puerto=int(entorno.get("DB_PORT", por_defecto.puerto)),
            usuario=entorno.get("DB_USER", por_defecto.usuario),
            password=entorno.get("DB_PASSWORD") or None,
            base_datos=entorno.get("DB_NAME", por_defecto.base_datos),
        )

    def con_password(self, password: str) -> "ConfiguracionBD":
        return replace(self, password=password)
