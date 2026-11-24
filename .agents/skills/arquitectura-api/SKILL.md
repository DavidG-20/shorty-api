---
name: arquitectura-api
description: Reglas de separación de capas para la API REST shorty-api con FastAPI y SQLAlchemy.
---

# Arquitectura por Capas (FastAPI)

- **`routers/`**: solo recibe peticiones HTTP, valida entrada con Pydantic y devuelve respuestas HTTP. No debe contener consultas SQL ni lógica de negocio.
- **`services/`**: contiene la lógica de negocio (generación de códigos cortos, registro de clics, cálculo de analíticas y rate limiting).
- **`models/`**: modelos ORM de SQLAlchemy (tablas `urls` y `clicks`).
- **`schemas/`**: esquemas Pydantic para entrada y salida de la API (nunca expongas modelos ORM crudos sin schema).
- **`core/`**: configuración (`config.py` con `pydantic-settings`) y conexión a base de datos (`database.py`).
- Incluye *type hints* en todas las funciones y mantén cada módulo pequeño y enfocado.
