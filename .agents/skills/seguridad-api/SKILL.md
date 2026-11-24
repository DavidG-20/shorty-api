---
name: seguridad-api
description: Reglas de validación, seguridad HTTP y pruebas aisladas para shorty-api.
---

# Reglas de Seguridad y Pruebas de API

- Valida todas las URLs de entrada con `HttpUrl` de Pydantic (solo esquemas `http` y `https`; rechaza `javascript:` o texto inválido).
- Usa **rate limiting** en la creación de enlaces cortos para evitar abusos y devuelve HTTP `429 Too Many Requests` cuando se supera el límite.
- Maneja los errores esperados con códigos HTTP semánticos (`404` enlace no encontrado, `409` alias ya en uso, `422` validación, `429` límite de peticiones).
- En pruebas con `pytest`, usa siempre una base de datos SQLite temporal/en memoria aislada; nunca ejecutes tests sobre una base de datos real.
- Nunca subas archivos `.env` ni bases de datos `.db` al repositorio (manténlos en `.gitignore`).
