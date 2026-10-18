FROM python:3.10-slim


ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1


RUN apt-get update && apt-get install -y \
    nmap \
    gcc \
    python3-dev \
    libcairo2-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*


# El build context es la raíz del repo (ver docker-compose.yml) para poder
# incluir alembic.ini y migrations/, que viven fuera de src/.
WORKDIR /app
COPY src/requirements.txt src/requirements.txt
RUN pip install --no-cache-dir -r src/requirements.txt


COPY src/ src/
COPY alembic.ini alembic.ini
COPY migrations/ migrations/
ENV PYTHONPATH=/app


# Aplica migraciones (Alembic es la fuente de verdad del esquema) y arranca la API.
CMD ["sh", "-c", "alembic upgrade head && uvicorn src.api.main:app --host 0.0.0.0 --port 8000"]
