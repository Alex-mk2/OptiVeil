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


# nuclei (ProjectDiscovery): backend de la validación no destructiva (SPEC-0002).
# Se descarga el binario de la última release (linux_amd64). ca-certificates se
# mantiene porque nuclei lo necesita en runtime (TLS + descarga de plantillas);
# curl/unzip se purgan tras instalar para no inflar la imagen. Si nuclei faltara,
# el validador degrada a "not_tested", así que la imagen sigue siendo funcional.
RUN set -eux; \
    apt-get update; \
    apt-get install -y --no-install-recommends curl unzip ca-certificates; \
    url="$(curl -fsSL https://api.github.com/repos/projectdiscovery/nuclei/releases/latest | grep -o '"browser_download_url": *"[^"]*linux_amd64\.zip"' | head -n1 | sed 's/.*"\(http[^"]*\)".*/\1/')"; \
    curl -fsSL "$url" -o /tmp/nuclei.zip; \
    unzip -o /tmp/nuclei.zip nuclei -d /usr/local/bin; \
    chmod +x /usr/local/bin/nuclei; \
    rm -f /tmp/nuclei.zip; \
    apt-get purge -y --auto-remove curl unzip; \
    rm -rf /var/lib/apt/lists/*; \
    nuclei -version


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
