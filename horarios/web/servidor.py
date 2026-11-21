"""Servidor HTTP de la biblioteca estándar. Solo traduce HTTP <-> Peticion/Respuesta."""

from __future__ import annotations

import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, unquote, urlsplit

from horarios.web import vistas
from horarios.web.peticiones import Enrutador, Peticion, Respuesta


def _a_dict(texto: str) -> dict[str, str]:
    return {k: v[-1] for k, v in parse_qs(texto, keep_blank_values=True, encoding="utf-8").items()}


def crear_servidor(enrutador: Enrutador, host: str, puerto: int) -> ThreadingHTTPServer:
    class Manejador(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            self._atender("GET")

        def do_POST(self) -> None:
            self._atender("POST")

        def _atender(self, metodo: str) -> None:
            url = urlsplit(self.path)
            formulario = {}
            if metodo == "POST":
                largo = int(self.headers.get("Content-Length") or 0)
                formulario = _a_dict(self.rfile.read(largo).decode("utf-8"))
            peticion = Peticion(metodo, unquote(url.path), _a_dict(url.query), formulario)
            try:
                respuesta = enrutador.resolver(peticion)
            except Exception:
                traceback.print_exc()
                respuesta = Respuesta(vistas.pagina("Error interno", "<p>Ocurrió un error inesperado.</p>"), 500)
            cuerpo = respuesta.cuerpo.encode("utf-8")
            self.send_response(respuesta.estado)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(cuerpo)))
            for clave, valor in respuesta.cabeceras.items():
                self.send_header(clave, valor)
            self.end_headers()
            self.wfile.write(cuerpo)

        def log_message(self, formato, *args) -> None:  # silencia el log por petición
            pass

    return ThreadingHTTPServer((host, puerto), Manejador)
