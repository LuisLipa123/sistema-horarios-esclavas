# Sistema de Asignación de Horarios y Carga Académica

Aplicativo con **interfaz gráfica web** para el **Colegio Particular Esclavas del Sagrado
Corazón de Jesús**. Gestiona grados, secciones, docentes, asignaturas, espacios y bloques de
horario sobre una base de datos **MySQL (InnoDB)** con procedimientos almacenados, triggers de
validación de cruces y bitácora de auditoría.

- Python 3.10+ **sin frameworks**: la interfaz usa solo la biblioteca estándar
  (`http.server`) y el único paquete externo es el driver `mysql-connector-python`.
- **Horarios semanales en grilla** (Lunes–Viernes × franjas) por sección, docente o espacio.
- Mantenimiento de las **11 tablas** (insertar, modificar, eliminar, listar) a través de
  **31 procedimientos almacenados**.
- **10 reportes** (9 con JOIN).
- Modo consola opcional: `python -m horarios --consola`.
- Los **triggers** de la BD impiden cruces de horario por espacio y por docente.
- Diseño modular con los principios **SOLID** y pruebas automáticas.
- Todo se levanta con **Docker** en un solo comando.

---

## Ejecución rápida con Docker

Requisitos: [Docker Desktop](https://www.docker.com/products/docker-desktop/).

```bash
git clone <url-del-repositorio>
cd <carpeta-del-repositorio>
cp .env.example .env          # opcional: cambia las contraseñas
docker compose up -d          # levanta MySQL (con los scripts) y la interfaz web
```

Luego abre **http://localhost:8000** en el navegador.

La primera vez MySQL ejecuta automáticamente, en orden, los scripts de `database/init/`
(esquema → procedimientos → triggers → datos de prueba → reportes). Puede tardar unos 30 s.
La imagen de la BD (`database/Dockerfile`) copia esos scripts y fuerza UTF-8, para que las
tildes y el símbolo `°` se guarden bien también desde Windows.

> En los datos de prueba, las secciones con horario cargado son la **5** (3.° A primaria)
> y la **15**: úsalas para ver un horario completo.

| Acción | Comando |
|---|---|
| Iniciar todo | `docker compose up -d` y abrir http://localhost:8000 |
| Ver la versión de consola | `docker compose run --rm app python -m horarios --consola` |
| Detener todo | `docker compose down` |
| Borrar la BD y recargar los scripts desde cero | `docker compose down -v` |
| Conectarse con MySQL Workbench al contenedor | host `localhost`, puerto `3307`, usuario `app_horarios` |

## Ejecución local (sin Docker)

Contra un MySQL instalado (por ejemplo, el de MySQL Workbench):

1. Ejecuta en Workbench, en orden, los scripts de `database/init/`.
   Si la BD ya existe con datos, **solo** `02_procedimientos.sql`, `03_triggers.sql` y
   `05_reportes.sql` (el `01` borra la base). `database/local/00_crear_usuario.sql` es opcional.
2. Instala dependencias y ejecuta:

```bash
pip install -r requirements.txt
python -m horarios            # o: python main.py  → abre el navegador en http://localhost:8000
```

La conexión se configura con variables de entorno. Si no se define `DB_PASSWORD`,
la app la pide al iniciar (no se guarda en el código).
`WEB_PORT` cambia el puerto de la interfaz (8000 por defecto).

| Variable | Por defecto |
|---|---|
| `DB_HOST` | `localhost` |
| `DB_PORT` | `3306` |
| `DB_USER` | `root` |
| `DB_PASSWORD` | *(se pide por consola)* |
| `DB_NAME` | `bd_horarios_esclavas` |

## Pruebas

```bash
pip install -r requirements-dev.txt
pytest
```

Las pruebas no necesitan MySQL: usan dobles en memoria (`tests/dobles.py`) gracias a la
inversión de dependencias. En GitHub Actions (`.github/workflows/ci.yml`) además se
construye la imagen y se levanta MySQL con los scripts para verificar que cargan bien.

---

## Arquitectura

```
horarios/
├── __main__.py              python -m horarios
├── bootstrap.py             Raíz de composición: crea e inyecta las dependencias
├── config.py                Configuración desde variables de entorno
├── dominio/                 Núcleo, sin dependencias externas
│   ├── campos.py            Tipos de dato y su validación (Entero, Texto, Opción, Hora)
│   ├── modelos.py           Entidad, Operacion, Reporte (definiciones declarativas)
│   ├── puertos.py           Interfaces: EjecutorProcedimientos, LectorProcedimientos, LectorTablas
│   └── errores.py           ErrorConexion, OperacionRechazada
├── catalogo/                QUÉ hace el sistema (datos, no lógica)
│   ├── entidades.py         Las 11 tablas y sus procedimientos
│   ├── reportes.py          Los 10 reportes
│   └── valores.py           Valores permitidos por los CHECK
├── servicios/               Casos de uso
│   ├── crud.py              ServicioCrud
│   ├── horarios.py          ServicioHorarios: arma la grilla semanal
│   └── reportes.py          ServicioReportes
├── infraestructura/
│   └── mysql.py             Único módulo que conoce mysql-connector
├── web/                     Interfaz gráfica (biblioteca estándar)
│   ├── peticiones.py        Peticion, Respuesta, Enrutador
│   ├── controladores.py     Inicio, Tablas (CRUD genérico), Reportes, Horarios
│   ├── vistas.py            HTML: tablas, formularios generados desde los Campos, grilla
│   └── servidor.py          Adaptador http.server
└── ui/                      Interfaz de consola (modo --consola)
    ├── consola.py           Abstracción de entrada/salida
    ├── formulario.py        Pide y valida los campos
    ├── menus.py             PantallaCrud (genérica), PantallaReportes, MenuPrincipal
    └── tabla.py             Formatea resultados

database/
├── Dockerfile               Imagen MySQL 8.4 con los scripts y charset UTF-8
├── conf/charset.cnf
├── init/                    01_esquema … 05_reportes (los carga Docker)
└── local/00_crear_usuario.sql
```

Flujo de dependencias (las flechas apuntan hacia abstracciones):

```
web ─┐
     ├──► servicios ──► dominio/puertos ◄── infraestructura/mysql
ui  ─┘                       ▲
bootstrap ───────────────────┘ (instancia MySQL y lo inyecta)
```

### Principios SOLID aplicados

| Principio | Dónde se ve |
|---|---|
| **S** — Responsabilidad única | Cada clase hace una sola cosa: `ProveedorConexionMySQL` abre conexiones, `GatewayMySQL` ejecuta SQL, `Formulario` pide datos, `formatear_tabla` imprime, `ServicioCrud` arma la llamada al procedimiento, `Enrutador` despacha URLs y `vistas.py` solo genera HTML. |
| **O** — Abierto/Cerrado | Para agregar una tabla o un reporte se añade una definición en `catalogo/`: los formularios web, los menús y los servicios se generan solos. La interfaz web se agregó **sin modificar** dominio, catálogo ni servicios. Un tipo de dato nuevo es otra subclase de `Campo` y registra su control HTML con `@control_para`. |
| **L** — Sustitución de Liskov | Toda subclase de `Campo` y de `Pantalla` se usa donde se espera la base: el formulario y el menú principal no conocen el tipo concreto. |
| **I** — Segregación de interfaces | Tres puertos pequeños: `ServicioCrud` solo depende de `EjecutorProcedimientos` + `LectorTablas`; `ServicioReportes` solo de `LectorProcedimientos`; `ServicioHorarios` de `LectorProcedimientos` + `LectorTablas`. |
| **D** — Inversión de dependencias | Servicios y UI dependen de protocolos (`puertos.py`, `Consola`). `bootstrap.py` es el único lugar que instancia MySQL; en las pruebas se inyectan dobles en memoria. |

### Reglas de negocio en la base de datos

- **CHECK**: DNI de 8 dígitos, niveles, días, naturalezas y rangos de horas válidos.
- **Triggers de cruce**: no permiten dos actividades en el mismo espacio, día y periodo con
  horas solapadas, ni un docente asignado a dos actividades que se crucen.
- **Bitácora**: cada INSERT/UPDATE/DELETE sobre `Actividad`, `Docente` y `Docente_Actividad`
  queda registrado (reporte 10).
