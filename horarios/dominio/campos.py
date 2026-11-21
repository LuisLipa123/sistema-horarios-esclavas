"""Tipos de campo que se piden al usuario y su validación.

O (Abierto/Cerrado): para un nuevo tipo de dato se crea otra subclase de
Campo; el formulario y los menús no se modifican.
L (Sustitución de Liskov): cualquier subclase se usa donde se espera un
Campo, porque todas respetan el mismo contrato de `procesar`.
"""

from __future__ import annotations

import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Mapping

Condicion = Callable[[Mapping[str, Any]], bool]


class ValorInvalido(ValueError):
    """El texto ingresado no es válido para el campo."""


@dataclass(frozen=True)
class Campo(ABC):
    nombre: str
    etiqueta: str
    opcional: bool = False
    # Si se define, el campo solo se pide cuando la condición es verdadera
    # (recibe los valores ya ingresados). Si no se pide, su valor es None.
    visible_si: Condicion | None = field(default=None, compare=False)

    def es_visible(self, valores: Mapping[str, Any]) -> bool:
        return self.visible_si is None or self.visible_si(valores)

    def indicacion(self) -> str:
        """Texto que acompaña a la etiqueta al pedir el dato."""
        return self.etiqueta

    def procesar(self, texto: str) -> Any:
        """Método plantilla: maneja vacíos y delega la conversión."""
        texto = texto.strip()
        if not texto:
            if self.opcional:
                return None
            raise ValorInvalido("Este dato es obligatorio.")
        return self.convertir(texto)

    @abstractmethod
    def convertir(self, texto: str) -> Any: ...


@dataclass(frozen=True)
class CampoTexto(Campo):
    patron: str | None = None
    mensaje_patron: str = "Formato inválido."

    def convertir(self, texto: str) -> str:
        if self.patron and not re.fullmatch(self.patron, texto):
            raise ValorInvalido(self.mensaje_patron)
        return texto


@dataclass(frozen=True)
class CampoEntero(Campo):
    minimo: int | None = None

    def convertir(self, texto: str) -> int:
        try:
            valor = int(texto)
        except ValueError:
            raise ValorInvalido("Ingresa un número entero válido.") from None
        if self.minimo is not None and valor < self.minimo:
            raise ValorInvalido(f"Debe ser mayor o igual a {self.minimo}.")
        return valor


@dataclass(frozen=True)
class CampoOpcion(Campo):
    opciones: tuple[str, ...] = ()

    def indicacion(self) -> str:
        return f"{self.etiqueta} ({'/'.join(self.opciones)})"

    def convertir(self, texto: str) -> str:
        for opcion in self.opciones:
            if opcion.lower() == texto.lower():
                return opcion  # con la capitalización oficial
        raise ValorInvalido(f"Valor no válido. Opciones: {', '.join(self.opciones)}")


@dataclass(frozen=True)
class CampoHora(Campo):
    def indicacion(self) -> str:
        return f"{self.etiqueta} (HH:MM)"

    def convertir(self, texto: str) -> str:
        coincidencia = re.fullmatch(r"(\d{1,2}):(\d{2})", texto)
        if coincidencia:
            h, m = int(coincidencia[1]), int(coincidencia[2])
            if 0 <= h < 24 and 0 <= m < 60:
                return f"{h:02d}:{m:02d}:00"
        raise ValorInvalido("Formato inválido, usa HH:MM (ej. 08:30).")
