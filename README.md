# Sistema de Asignación de Horarios y Carga Académica

Aplicativo de consola para el **Colegio Particular Esclavas del Sagrado Corazón de Jesús**.
Gestiona grados, secciones, docentes, asignaturas, espacios y bloques de horario sobre una
base de datos **MySQL (InnoDB)** con procedimientos almacenados, triggers de validación de
cruces y bitácora de auditoría.

- Python 3.10+ sin frameworks (solo el driver `mysql-connector-python`).
- Mantenimiento de las **11 tablas** a través de **31 procedimientos almacenados**.
- **10 reportes** (9 con JOIN).
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
docker compose run --rm app   # levanta MySQL, carga los scripts y abre la app
```

La primera vez MySQL ejecuta automáticamente, en orden, los scripts de `database/init/`
(esquema → procedimientos → triggers → datos de prueba → reportes). Puede tardar unos 30 s.
La imagen de la BD (`database/Dockerfile`) copia esos scripts y fuerza UTF-8, para que las
tildes y el símbolo `°` se guarden bien también desde Windows.

> En los datos de prueba, las secciones con horario cargado son la **5** (3.° A primaria)
> y la **15**: úsalas para probar el reporte 1.

| Acción | Comando |
|---|---|
| Abrir la app (otra vez) | `docker compose run --rm app` |
| Detener MySQL | `docker compose down` |
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
python -m horarios            # o: python main.py
```

La conexión se configura con variables de entorno. Si no se define `DB_PASSWORD`,
la app la pide al iniciar (no se guarda en el código).

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
│   └── reportes.py          ServicioReportes
├── infraestructura/
│   └── mysql.py             Único módulo que conoce mysql-connector
└── ui/                      Interfaz de consola
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
ui ──► servicios ──► dominio/puertos ◄── infraestructura/mysql
                         ▲
bootstrap ───────────────┘ (instancia MySQL y lo inyecta)
```

### Principios SOLID aplicados

| Principio | Dónde se ve |
|---|---|
| **S** — Responsabilidad única | Cada clase hace una sola cosa: `ProveedorConexionMySQL` abre conexiones, `GatewayMySQL` ejecuta SQL, `Formulario` pide datos, `formatear_tabla` imprime, `ServicioCrud` arma la llamada al procedimiento. |
| **O** — Abierto/Cerrado | Para agregar una tabla o un reporte se añade una definición en `catalogo/`; los menús y servicios **no se tocan**. Un tipo de dato nuevo es otra subclase de `Campo`. |
| **L** — Sustitución de Liskov | Toda subclase de `Campo` y de `Pantalla` se usa donde se espera la base: el formulario y el menú principal no conocen el tipo concreto. |
| **I** — Segregación de interfaces | Tres puertos pequeños: `ServicioCrud` solo depende de `EjecutorProcedimientos` + `LectorTablas`; `ServicioReportes` solo de `LectorProcedimientos`. |
| **D** — Inversión de dependencias | Servicios y UI dependen de protocolos (`puertos.py`, `Consola`). `bootstrap.py` es el único lugar que instancia MySQL; en las pruebas se inyectan dobles en memoria. |

### Reglas de negocio en la base de datos

- **CHECK**: DNI de 8 dígitos, niveles, días, naturalezas y rangos de horas válidos.
- **Triggers de cruce**: no permiten dos actividades en el mismo espacio, día y periodo con
  horas solapadas, ni un docente asignado a dos actividades que se crucen.
- **Bitácora**: cada INSERT/UPDATE/DELETE sobre `Actividad`, `Docente` y `Docente_Actividad`
  queda registrado (reporte 10).
