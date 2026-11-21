"""Abstracción de entrada/salida para poder probar la UI sin teclado."""

from __future__ import annotations

from typing import Protocol


class Consola(Protocol):
    def leer(self, mensaje: str) -> str: ...

    def mostrar(self, texto: str = "") -> None: ...


class ConsolaEstandar:
    def leer(self, mensaje: str) -> str:
        return input(mensaje)

    def mostrar(self, texto: str = "") -> None:
        print(texto)
