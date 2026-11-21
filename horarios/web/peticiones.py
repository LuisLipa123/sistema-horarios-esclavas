"""Petición, respuesta y enrutador: lo mínimo de HTTP que necesita la app.

O (Abierto/Cerrado): una página nueva se agrega registrando una ruta, sin
modificar el enrutador ni el servidor.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable
from urllib.parse import quote, urlencode


@dataclass(frozen=True)
class Peticion:
    metodo: str
    ruta: str
    consulta: dict[str, str] = field(default_factory=dict)
    formulario: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class Respuesta:
    cuerpo: str = ""
    estado: int = 200
    cabeceras: dict[str, str] = field(default_factory=dict)

    @classmethod
    def redirigir(cls, ruta: str, **parametros: str) -> "Respuesta":
        destino = quote(ruta) + ("?" + urlencode(parametros) if parametros else "")
        return cls(estado=303, cabeceras={"Location": destino})


Manejador = Callable[..., Respuesta]


class Enrutador:
    def __init__(self, no_encontrado: Callable[[Peticion], Respuesta]):
        self._rutas: list[tuple[str, re.Pattern[str], Manejador]] = []
        self._no_encontrado = no_encontrado

    def agregar(self, metodo: str, patron: str, manejador: Manejador) -> None:
        self._rutas.append((metodo, re.compile(patron), manejador))

    def resolver(self, peticion: Peticion) -> Respuesta:
        for metodo, patron, manejador in self._rutas:
            coincidencia = patron.fullmatch(peticion.ruta)
            if metodo == peticion.metodo and coincidencia:
                return manejador(peticion, **coincidencia.groupdict())
        return self._no_encontrado(peticion)
