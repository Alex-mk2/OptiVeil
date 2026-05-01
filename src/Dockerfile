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


WORKDIR /app/src
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY . .
ENV PYTHONPATH=/app
WORKDIR /app
CMD ["uvicorn", "src.api.main:app", "--host", "0.0.0.0", "--port", "8000"]