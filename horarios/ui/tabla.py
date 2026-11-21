"""Formateo de resultados como tabla de texto (función pura)."""

from __future__ import annotations

from horarios.dominio.puertos import Resultado


def formatear_tabla(resultado: Resultado) -> str:
    if resultado.vacio:
        return "(sin resultados)"

    def texto(valor) -> str:
        return "" if valor is None else str(valor)

    anchos = [len(c) for c in resultado.columnas]
    for fila in resultado.filas:
        for i, valor in enumerate(fila):
            anchos[i] = max(anchos[i], len(texto(valor)))

    def linea(valores) -> str:
        return " | ".join(texto(v).ljust(anchos[i]) for i, v in enumerate(valores)).rstrip()

    lineas = [linea(resultado.columnas), "-+-".join("-" * a for a in anchos)]
    lineas.extend(linea(fila) for fila in resultado.filas)
    return "\n".join(lineas)
