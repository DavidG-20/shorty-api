# shorty-api

API REST de **acortador de URLs con analíticas de clics y rate limiting**, construida con **FastAPI**, **SQLAlchemy 2.x**, **`uv`** y lista para ejecutarse con **Docker Compose + PostgreSQL**.

## Características principales

- **Acortamiento inteligente**: genera códigos aleatorios Base62 (`secrets.choice`) o permite definir un `custom_alias` opcional con validación de colisiones (`409 Conflict`) y rutas reservadas (`400 Bad Request`).
- **Redirección HTTP `307`**: redirige al enlace original sin que el navegador cachee permanentemente la ruta, permitiendo contar cada visita con precisión.
- **Analíticas en tiempo real**: registra cada clic en base de datos relacional (`urls` → `clicks`) y calcula total de clics, desglose por dispositivo (`mobile`, `tablet`, `desktop`, `bot`), principales orígenes (`Referer`) y último clic.
- **Rate limiting por IP**: ventana deslizante (*sliding window*) en el endpoint de creación que protege contra abusos devolviendo `429 Too Many Requests` y cabecera `Retry-After`.
- **Validación estricta**: rechaza URLs inválidas o esquemas peligrosos (`javascript:`) mediante `HttpUrl` de Pydantic (`422 Unprocessable Entity`).
- **Listo para Docker**: incluye `Dockerfile` y `docker-compose.yml` con **PostgreSQL 16** y *healthcheck*.

## Arquitectura por capas

```text
shorty-api/
├── .agents/skills/              # Skills de arquitectura y seguridad HTTP
├── AGENTS.md                    # Reglas generales del proyecto
├── Dockerfile                   # Imagen lista para producción con uv
├── docker-compose.yml           # Orquestación API + PostgreSQL 16
├── .env.example                 # Plantilla de variables de entorno
├── src/shorty_api/
│   ├── main.py                  # Entrada FastAPI, lifespan y /health
│   ├── core/
│   │   ├── config.py            # Configuración tipada con pydantic-settings
│   │   └── database.py          # Engine y sesiones de SQLAlchemy
│   ├── models/url.py            # Tablas ORM: urls y clicks
│   ├── schemas/url.py           # Esquemas Pydantic de entrada/salida
│   ├── services/
│   │   ├── url_service.py       # Lógica de negocio y analíticas
│   │   └── rate_limiter.py      # Rate limiter de ventana deslizante
│   └── routers/urls.py          # Endpoints REST
└── tests/
    ├── conftest.py              # Base de datos SQLite en memoria aislada
    └── test_urls_api.py         # Pruebas de integración de la API
```

## Endpoints principales

| Método | Ruta | Descripción |
| :--- | :--- | :--- |
| `GET` | `/health` | Verifica el estado del servicio |
| `POST` | `/api/v1/shorten` | Crea un enlace corto (`url` y `custom_alias` opcional) |
| `GET` | `/{short_code}` | Registra el clic y redirige (`307`) a la URL original |
| `GET` | `/api/v1/stats/{short_code}` | Devuelve las analíticas agregadas del enlace |
| `GET` | `/docs` | Documentación interactiva Swagger UI |

## Instalación y ejecución local (SQLite)

Asegúrate de tener [`uv`](https://docs.astral.sh/uv/) instalado:

```bash
git clone https://github.com/DavidG-20/shorty-api.git
cd shorty-api
cp .env.example .env
uv sync
uv run uvicorn shorty_api.main:app --reload
```

Luego abre `http://localhost:8000/docs` para probar todos los endpoints desde el navegador.

## Ejecución con Docker + PostgreSQL

```bash
docker compose up --build
```

Esto levanta automáticamente PostgreSQL 16 (esperando a que esté saludable) y la API conectada en `http://localhost:8000`.

## Ejemplo rápido con `curl`

```bash
# 1. Crear enlace corto
curl -X POST http://localhost:8000/api/v1/shorten \
  -H "Content-Type: application/json" \
  -d '{"url": "https://github.com/DavidG-20", "custom_alias": "mi-github"}'

# 2. Consultar estadísticas
curl http://localhost:8000/api/v1/stats/mi-github
```

## Ejecutar pruebas

Las pruebas usan una base de datos SQLite en memoria completamente aislada:

```bash
uv run pytest -v
```

## Licencia

MIT
