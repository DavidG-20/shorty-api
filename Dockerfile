FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Copiar manifiestos primero para aprovechar la caché de capas de Docker
COPY pyproject.toml uv.lock README.md ./
COPY src ./src

# Instalar dependencias del proyecto + driver de PostgreSQL
RUN uv sync --frozen --no-dev && uv pip install --python .venv/bin/python "psycopg[binary]>=3.2"

EXPOSE 8000

CMD ["uv", "run", "--no-dev", "uvicorn", "shorty_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
