"""Generación de HTML (funciones puras, todo el texto se escapa).

Estilo sencillo y amigable: fondo cálido, tarjetas redondeadas y un único
color de acento. Sin librerías externas; solo un poco de CSS.
"""

from __future__ import annotations

from html import escape
from typing import Any, Callable, Iterable, Mapping, Sequence

from horarios.dominio.campos import Campo, CampoEntero, CampoHora, CampoOpcion, CampoTexto
from horarios.dominio.puertos import Resultado
from horarios.servicios.horarios import Grilla

CSS = """
:root{
  --bg:#ffffff; --surface:#ffffff; --soft:#faf7f7; --ink:#2a2224; --muted:#75696b; --line:#ece3e4;
  --accent:#7b1e2f; --accent-dark:#5e1623; --accent-soft:#f7ecee; --accent-ink:#ffffff;
  --ok:#2a2224; --ok-soft:#faf7f7; --error:#7b1e2f; --error-soft:#f7ecee;
  --otro:#f3f0f0; --radius:14px; --shadow:0 1px 2px rgba(60,20,28,.05),0 6px 18px rgba(60,20,28,.06);
}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);
  font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial,sans-serif}
a{color:inherit}
.top{background:var(--accent);color:var(--accent-ink)}
.top-in{max-width:1180px;margin:0 auto;padding:14px 20px;display:flex;align-items:center;gap:14px;flex-wrap:wrap}
.marca{display:flex;align-items:center;gap:12px;text-decoration:none;margin-right:auto}
.logo{width:38px;height:38px;border-radius:11px;background:rgba(255,255,255,.14);color:#fff;
  display:grid;place-items:center}
.marca b{display:block;font-size:16px;letter-spacing:-.01em}
.marca small{display:block;color:rgba(255,255,255,.75);font-size:12.5px}
nav{display:flex;gap:4px;flex-wrap:wrap}
nav a{text-decoration:none;padding:7px 14px;border-radius:999px;color:rgba(255,255,255,.82);font-weight:500}
nav a:hover{background:rgba(255,255,255,.12);color:#fff}
nav a.activo{background:#fff;color:var(--accent)}
main{max-width:1180px;margin:0 auto;padding:28px 20px 48px}
h1{font-size:26px;letter-spacing:-.02em;margin:0 0 4px}
.sub{color:var(--muted);margin:0 0 22px}
h3{font-size:16px;margin:0 0 12px}
.aviso{border-radius:12px;padding:11px 14px;margin:0 0 18px;font-weight:500}
.aviso.ok{background:var(--ok-soft);color:var(--ok);border:1px solid var(--line);border-left:3px solid var(--accent)}
.aviso.error{background:var(--error-soft);color:var(--error);border-left:3px solid var(--error)}
.tarjeta{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);
  box-shadow:var(--shadow);padding:18px}
.tarjetas{display:grid;grid-template-columns:repeat(auto-fill,minmax(250px,1fr));gap:14px}
a.tarjeta{text-decoration:none;display:block;transition:transform .15s,border-color .15s}
a.tarjeta:hover{transform:translateY(-2px);border-color:var(--accent)}
.icono{width:42px;height:42px;border-radius:12px;background:var(--accent-soft);color:var(--accent);
  display:grid;place-items:center;margin-bottom:12px}
.tarjeta b{display:block;font-size:16px;margin-bottom:2px}
.tarjeta span{color:var(--muted);font-size:13.5px}
.num{font-size:12px;font-weight:600;color:var(--accent);margin-bottom:6px;display:block}
.nota{background:var(--accent-soft);color:var(--accent-dark);border-left:3px solid var(--accent);border-radius:12px;padding:10px 14px;margin:0 0 18px;font-size:14px}
.acciones{display:grid;grid-template-columns:repeat(auto-fit,minmax(270px,1fr));gap:14px;margin:0 0 26px;align-items:start}
details.tarjeta{padding:0}
details.tarjeta summary{cursor:pointer;list-style:none;padding:14px 18px;font-weight:600;display:flex;justify-content:space-between}
details.tarjeta summary::-webkit-details-marker{display:none}
details.tarjeta summary::after{content:"+";color:var(--muted);font-weight:400}
details[open].tarjeta summary::after{content:"–"}
details.tarjeta form{padding:0 18px 18px}
label{display:block;margin:0 0 12px;font-size:13.5px;font-weight:500}
label small{display:block;color:var(--muted);font-weight:400}
input,select{display:block;width:100%;margin-top:4px;padding:9px 11px;font:inherit;color:var(--ink);
  background:var(--soft);border:1px solid var(--line);border-radius:10px;outline:none}
input:focus,select:focus{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-soft)}
button{font:inherit;font-weight:600;padding:9px 18px;border:0;border-radius:10px;cursor:pointer;
  background:var(--accent);color:var(--accent-ink)}
button:hover{background:var(--accent-dark)}
button.peligro{background:#fff;color:var(--accent);border:1.5px solid var(--accent)}
button.peligro:hover{background:var(--accent);color:#fff}
.bloque-titulo{display:flex;align-items:baseline;gap:10px;margin:0 0 10px}
.chip{font-size:12px;background:var(--soft);border:1px solid var(--line);border-radius:999px;padding:2px 10px;color:var(--muted)}
.tabla{background:var(--surface);border:1px solid var(--line);border-radius:var(--radius);
  box-shadow:var(--shadow);overflow:auto;max-height:70vh}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{padding:9px 12px;text-align:left;vertical-align:top;border-bottom:1px solid var(--line)}
th{position:sticky;top:0;background:var(--soft);font-size:12px;text-transform:uppercase;
  letter-spacing:.04em;color:var(--muted);z-index:1}
tbody tr:last-child td{border-bottom:0}
tbody tr:hover td{background:var(--soft)}
.vacio{color:var(--muted);text-align:center;padding:30px}
.selectores{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:14px;margin:0 0 24px}
.selectores form{display:flex;flex-direction:column;height:100%}
.selectores label{flex:1}
.grilla{max-height:none}
.grilla table{table-layout:fixed;min-width:760px}
.grilla th:first-child,.grilla td:first-child{width:112px}
.grilla td{border-left:1px solid var(--line);padding:6px}
.grilla td:first-child{border-left:0;color:var(--muted);font-size:13px;font-variant-numeric:tabular-nums;padding:10px 12px}
.grilla tbody tr:hover td{background:transparent}
.b{border-radius:9px;padding:7px 9px;margin:0 0 5px;background:var(--accent-soft);border-left:3px solid var(--accent)}
.b strong{display:block;font-size:13.5px;line-height:1.3}
.b small{display:block;color:var(--muted);font-size:12px}
.b.otro{background:var(--otro);border-left-color:var(--muted)}
.b.otro strong{font-weight:500;font-style:italic}
.leyenda{display:flex;gap:16px;color:var(--muted);font-size:13px;margin:12px 2px 0}
.leyenda i{display:inline-block;width:12px;height:12px;border-radius:4px;vertical-align:-1px;margin-right:6px;
  background:var(--accent-soft);border-left:3px solid var(--accent)}
.leyenda i.otro{background:var(--otro);border-left-color:var(--muted)}
.volver{display:inline-block;margin-top:18px;color:var(--muted)}
@media (max-width:640px){main{padding:20px 14px 40px}h1{font-size:22px}.top-in{padding:12px 14px}}
"""

ENLACES = (("/", "Inicio"), ("/horarios", "Horarios"), ("/tablas", "Tablas"), ("/reportes", "Reportes"))

# Iconos de trazo simple (24x24), heredan el color del texto.
_SVG = '<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{}</svg>'
ICONOS = {
    "calendario": _SVG.format('<rect x="3" y="4" width="18" height="17" rx="3"/><path d="M8 2v4M16 2v4M3 10h18"/>'),
    "tabla": _SVG.format('<rect x="3" y="4" width="18" height="16" rx="3"/><path d="M3 10h18M9 10v10"/>'),
    "reporte": _SVG.format('<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>'),
}


def e(valor: Any) -> str:
    return escape("" if valor is None else str(valor))


def pagina(titulo: str, cuerpo: str, ok: str | None = None, error: str | None = None,
           activo: str = "", subtitulo: str = "") -> str:
    avisos = ""
    if ok:
        avisos += f'<div class="aviso ok">{e(ok)}</div>'
    if error:
        avisos += f'<div class="aviso error">{e(error)}</div>'
    marca_activo = ' class="activo"'
    nav = "".join(f'<a href="{href}"{marca_activo if href == activo else ""}>{e(texto)}</a>'
                  for href, texto in ENLACES)
    sub = f'<p class="sub">{e(subtitulo)}</p>' if subtitulo else '<div style="height:14px"></div>'
    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="light">
<title>{e(titulo)} · Horarios</title><style>{CSS}</style></head>
<body>
<header class="top"><div class="top-in">
  <a class="marca" href="/"><span class="logo">{ICONOS["calendario"]}</span>
    <span><b>Horarios Esclavas</b><small>Asignación de horarios y carga académica</small></span></a>
  <nav>{nav}</nav>
</div></header>
<main><h1>{e(titulo)}</h1>{sub}{avisos}{cuerpo}</main>
</body></html>"""


def tarjeta_enlace(href: str, titulo: str, texto: str, icono: str = "", numero: str = "") -> str:
    icono_html = f'<div class="icono">{ICONOS[icono]}</div>' if icono else ""
    numero_html = f'<span class="num">{e(numero)}</span>' if numero else ""
    return (f'<a class="tarjeta" href="{e(href)}">{icono_html}{numero_html}'
            f"<b>{e(titulo)}</b><span>{e(texto)}</span></a>")


def tabla(resultado: Resultado, titulo: str = "") -> str:
    encabezado = ""
    if titulo:
        encabezado = (f'<div class="bloque-titulo"><h3 style="margin:0">{e(titulo)}</h3>'
                      f'<span class="chip">{len(resultado.filas)} registro(s)</span></div>')
    if resultado.vacio:
        return f'{encabezado}<div class="tabla"><p class="vacio">Sin resultados</p></div>'
    cabecera = "".join(f"<th>{e(c)}</th>" for c in resultado.columnas)
    filas = "".join("<tr>" + "".join(f"<td>{e(v)}</td>" for v in fila) + "</tr>" for fila in resultado.filas)
    return f'{encabezado}<div class="tabla"><table><thead><tr>{cabecera}</tr></thead><tbody>{filas}</tbody></table></div>'


# --- Controles de formulario --------------------------------------------------
# Registro tipo de Campo -> función que dibuja su control. Para un tipo nuevo se
# registra otra función (Abierto/Cerrado); si no hay, se usa la de la clase base.

_CONTROLES: dict[type, Callable[[Campo, str, str], str]] = {}


def control_para(tipo: type):
    def registrar(funcion):
        _CONTROLES[tipo] = funcion
        return funcion
    return registrar


def _requerido(campo: Campo) -> str:
    return "" if campo.opcional or campo.visible_si else " required"


@control_para(Campo)
def _control_texto(campo: Campo, nombre: str, valor: str) -> str:
    return f'<input type="text" name="{e(nombre)}" value="{e(valor)}"{_requerido(campo)}>'


@control_para(CampoTexto)
def _control_texto_patron(campo: CampoTexto, nombre: str, valor: str) -> str:
    patron = f' pattern="{e(campo.patron)}" title="{e(campo.mensaje_patron)}"' if campo.patron else ""
    return f'<input type="text" name="{e(nombre)}" value="{e(valor)}"{patron}{_requerido(campo)}>'


@control_para(CampoEntero)
def _control_entero(campo: CampoEntero, nombre: str, valor: str) -> str:
    minimo = f' min="{campo.minimo}"' if campo.minimo is not None else ""
    return f'<input type="number" name="{e(nombre)}" value="{e(valor)}"{minimo}{_requerido(campo)}>'


@control_para(CampoHora)
def _control_hora(campo: CampoHora, nombre: str, valor: str) -> str:
    return f'<input type="time" name="{e(nombre)}" value="{e(valor)}"{_requerido(campo)}>'


@control_para(CampoOpcion)
def _control_opcion(campo: CampoOpcion, nombre: str, valor: str) -> str:
    opciones = '<option value="">Elegir…</option>'
    opciones += "".join(
        f'<option{" selected" if o == valor else ""}>{e(o)}</option>' for o in campo.opciones)
    return f'<select name="{e(nombre)}"{_requerido(campo)}>{opciones}</select>'


def control(campo: Campo, valor: str = "") -> str:
    for tipo in type(campo).__mro__:
        if tipo in _CONTROLES:
            return _CONTROLES[tipo](campo, campo.nombre, valor)
    raise TypeError(f"Sin control para {type(campo).__name__}")


def formulario(titulo: str, campos: Sequence[Campo], accion: str, boton: str, *,
               metodo: str = "post", valores: Mapping[str, str] | None = None,
               confirmar: str | None = None, ocultos: Mapping[str, str] | None = None,
               plegable: bool = False, abierto: bool = False) -> str:
    valores = valores or {}
    etiquetas = "".join(
        f'<label>{e(c.etiqueta)}{f"<small>{e(c.ayuda)}</small>" if c.ayuda else ""}'
        f'{control(c, valores.get(c.nombre, ""))}</label>'
        for c in campos)
    ocultos_html = "".join(f'<input type="hidden" name="{e(k)}" value="{e(v)}">'
                           for k, v in (ocultos or {}).items())
    al_enviar = f' onsubmit="return confirm(\'{e(confirmar)}\')"' if confirmar else ""
    clase_boton = ' class="peligro"' if confirmar else ""
    form = (f'<form method="{metodo}" action="{e(accion)}" accept-charset="utf-8"{al_enviar}>'
            f"{etiquetas}{ocultos_html}<button{clase_boton}>{e(boton)}</button></form>")
    if plegable:
        return (f'<details class="tarjeta"{" open" if abierto else ""}>'
                f"<summary>{e(titulo)}</summary>{form}</details>")
    encabezado = f"<h3>{e(titulo)}</h3>" if titulo else ""
    return f'<div class="tarjeta">{encabezado}{form}</div>'


def selector(titulo: str, nombre: str, opciones: Iterable[tuple[str, str]],
             seleccionado: str, accion: str) -> str:
    items = '<option value="">Elegir…</option>' + "".join(
        f'<option value="{e(v)}"{" selected" if v == seleccionado else ""}>{e(t)}</option>'
        for v, t in opciones)
    return (f'<div class="tarjeta"><form method="get" action="{e(accion)}"><h3>{e(titulo)}</h3>'
            f'<label><select name="{e(nombre)}" required>{items}</select></label>'
            f"<button>Ver horario</button></form></div>")


def grilla(g: Grilla) -> str:
    if g.vacia:
        return (f'<div class="bloque-titulo"><h3 style="margin:0">{e(g.titulo)}</h3></div>'
                '<div class="tabla"><p class="vacio">No tiene actividades programadas</p></div>')
    cabecera = "<th>Hora</th>" + "".join(f"<th>{e(d)}</th>" for d in g.dias)
    filas = []
    total = 0
    for franja in g.franjas:
        celdas = []
        for dia in g.dias:
            bloques = g.bloques(franja, dia)
            total += len(bloques)
            celdas.append("<td>" + "".join(
                f'<div class="b{"" if b.es_clase else " otro"}"><strong>{e(b.titulo)}</strong>'
                f"<small>{e(b.detalle)}</small></div>" for b in bloques) + "</td>")
        filas.append(f"<tr><td>{e(franja[0])}<br>{e(franja[1])}</td>{''.join(celdas)}</tr>")
    return (f'<div class="bloque-titulo"><h3 style="margin:0">{e(g.titulo)}</h3>'
            f'<span class="chip">{total} bloque(s)</span></div>'
            f'<div class="tabla grilla"><table><thead><tr>{cabecera}</tr></thead>'
            f"<tbody>{''.join(filas)}</tbody></table></div>"
            '<div class="leyenda"><span><i></i>Clase</span>'
            '<span><i class="otro"></i>Receso, consejo, pastoral u otro rol</span></div>')
