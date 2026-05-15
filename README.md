# 🛡️ OptiVeil Core
**Framework de Auditoría Evolutiva y Threat Intelligence**

OptiVeil es una plataforma de ciberseguridad diseñada para realizar escaneos tácticos de red y análisis asistido por IA. Utiliza algoritmos evolutivos (NSGA-II) para optimizar configuraciones de escaneo buscando un equilibrio entre sigilo y tiempo de ejecución.

---

## 🧭 Estructura del repositorio

La organización actual del proyecto (estructura de carpetas) es la siguiente (resumen):

- `frontend/` — Aplicación React + Vite (dashboard e interfaz).
- `src/` — Código principal de la aplicación Python:
	- `src/api/` — FastAPI y puntos de entrada de la API.
	- `src/core/` — Motor evolutivo y lógica principal (`engine.py`).
	- `src/IA_guard/` — CLI y orquestador de operaciones (`cli.py`).
	- `src/inter/` — Módulos de fingerprinting y análisis (`fingerprint.py`, `IA_analyzer.py`).
	- `src/modules/stealth/` — Algoritmos NSGA-II y scanner.
	- `src/utils/` — Utilidades, generación de reportes y gráficas.
- `data/`, `results/` — Salidas, logs y reportes generados.
- `tests/` — Pruebas unitarias.

> Nota: esta sección reemplaza referencias a carpetas que no existen o que estaban equivocadas en versiones previas del README.

---

## 🧠 Arquitectura del Sistema

OptiVeil adopta un enfoque de monolito modular: un solo repositorio/proceso con responsabilidades separadas por carpetas y módulos.

| Módulo | Ubicación | Rol |
|---|---:|---|
| **Frontend** | `frontend/` | Dashboard táctico y visualización en tiempo real |
| **API / Backend** | `src/api/` | Endpoints FastAPI y orquestación |
| **Motor Evolutivo** | `src/core/` + `src/modules/stealth/` | NSGA-II (`pymoo`) para optimización multiobjetivo |
| **Motor de Escaneo** | `src/modules/stealth/` | Construcción/envío de paquetes (Scapy) y evasión |
| **IA / Análisis** | `src/inter/` + `src/IA_guard/` | Componentes IA, análisis y flujo CLI |
| **Generador YARA** | `src/utils/` | Generación de reglas YARA a partir de resultados |
| **Persistencia** | `data/`, `results/` | Salida de reportes y datos históricos |

### ¿Por qué NSGA-II?

OptiVeil modela la configuración del escaneo como un problema multiobjetivo: minimizar detección (ruido) y tiempo. NSGA-II produce un Frente de Pareto de soluciones no dominadas; el operador puede elegir la configuración según el `stealth_level` deseado.

---

## 🚀 Requisitos Previos

Antes de comenzar, instala y configura lo siguiente:

1. **[Git](https://git-scm.com/downloads)**
2. **[Python 3.11+](https://www.python.org/downloads/)**
3. **[Npcap](https://npcap.com/#download)** *(solo Windows)* — Requerido por Scapy para captura a bajo nivel.
4. **Permisos de Administrador** *(solo Windows)* — Necesarios para sockets raw.
5. **API Key de OpenAI** — Si vas a usar el componente de IA.

---

## 🛠️ Instalación y Despliegue

### Paso 1: Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/OptiVeil.git
cd OptiVeil
```

### Paso 2: Instalar dependencias (backend)

```bash
pip install -r src/requirements.txt
```

*(Si prefieres usar `pyproject.toml`/`poetry`, adapta los comandos según tu flujo.)*

### Paso 3: Configurar variables de entorno

Crea un archivo `.env` en la raíz del proyecto con las credenciales necesarias:

```env
DATABASE_URL=postgresql://postgres:password_seguro@localhost:5432/optiveildb
OPENAI_API_KEY=sk-TU_LLAVE_AQUI
```

### Paso 4: Levantar el backend (FastAPI)

```bash
uvicorn src.api.main:app --reload
```

### Paso 5: Levantar el frontend

```bash
cd frontend
npm install
npm run dev
```

Accede a:

- **Dashboard Táctico:** http://localhost:5173
- **Documentación de la API:** http://localhost:8000/docs

---

## 🖥️ Uso desde CLI

Puedes ejecutar las utilidades CLI directamente:

```bash
# Requiere permisos de Administrador en Windows para operaciones de red raw
python src/IA_guard/cli.py <IP_OBJETIVO> --stealth <1-10> --ports <N>

# Ejemplo: escanear los primeros 100 puertos con sigilo nivel 7
python src/IA_guard/cli.py 192.168.1.1 --stealth 7 --ports 100
```

Archivo del CLI: [src/IA_guard/cli.py](src/IA_guard/cli.py)

| Parámetro | Descripción | Rango |
|---|---|---|
| `IP_OBJETIVO` | IPv4 del host a auditar | — |
| `--stealth` | Nivel de sigilo (1 = rápido, 10 = máximo sigilo) | 1–10 |
| `--ports` | Cantidad de puertos a escanear (desde el puerto 1) | 1–65535 |

---

## 🔎 Archivos relevantes

- Código API: [src/api](src/api)
- Motor evolutivo: [src/core/engine.py](src/core/engine.py)
- Módulos stealth: [src/modules/stealth](src/modules/stealth)
- Utilidades y reportes: [src/utils](src/utils)

---

## 🔗 Endpoints de la API

La API pública está disponible bajo el prefijo `/api`. Rutas principales disponibles:

- `POST /api/scan` — Inicia un escaneo (cuerpo: `target`, `stealth`, `ports`).
- `GET /api/topology/{target}` — Obtiene la topología y nodos generados para un objetivo.
- `POST /api/nmap` — Ejecuta un escaneo Nmap y devuelve hallazgos.
- `GET /api/strategy/{target}` — Devuelve la estrategia generada para un objetivo (si existe en `results/attack_reports`).
- `POST /api/strategy/live` — Genera una estrategia en tiempo real (body: `LiveStrategyRequest`).
- `GET /api/reports` — Lista reportes de inteligencia disponibles (`results/reports_IA`).
- `GET /api/reports/{filename}` — Devuelve contenido de un reporte Markdown.
- `GET /api/reports/{filename}/pdf` — Exporta un reporte a PDF.
- `GET /api/rules/{target}` — Devuelve la regla YARA generada para un objetivo (busca en `results/rules`).
- `GET /api/cve/{service_banner}` — Busca CVEs relacionadas con un banner de servicio (consulta NIST).
- `POST /api/persistence/sync` — Sincroniza resultados de escaneo en la base de datos.
- `GET /api/persistence/latest` — Obtiene el último escaneo registrado (opcional `target` query).
- `GET /api/delta/{target}` — Calcula delta entre los dos últimos escaneos para un objetivo.

Estas rutas están registradas en `src/api/main.py` mediante los routers definidos en `src/api/routers/`.

### Ejemplos de payloads (POST)

A continuación se muestran ejemplos mínimos de payloads JSON para los endpoints `POST` más relevantes. **No incluyas claves ni secretos en el repositorio público**; usa `.env` o variables de entorno en el entorno de ejecución.

- `POST /api/scan` — Inicia un escaneo.

```json
{
	"target": "192.168.1.1",
	"stealth": 7,
	"ports": 100
}
```

Respuesta esperada (resumen):

```json
{
	"best_config": {...},
	"findings": [...],
	"pareto_front": [...],
	"status": "done",
	"attack_roadmap": {...}
}
```

- `POST /api/nmap` — Ejecuta Nmap con los parámetros especificados.

```json
{
	"target": "192.168.1.1",
	"stealth": 5,
	"ports": 50
}
```

Respuesta esperada (resumen):

```json
{
	"target": "192.168.1.1",
	"stealth_applied": 5,
	"status": "success",
	"findings": [
		{"port": 22, "service": "SSH", "banner": "OpenSSH 7.4"},
		...
	]
}
```

- `POST /api/strategy/live` — Genera estrategia en tiempo real.

```json
{
	"stealth": 6,
	"findings": [
		{"port": 80, "service": "http", "banner": "Apache 2.4"},
		{"port": 22, "service": "ssh", "banner": "OpenSSH"}
	]
}
```

Respuesta esperada: JSON con la estructura de la `attack_roadmap` generada.

- `POST /api/persistence/sync` — Sincroniza resultados en la base de datos.

```json
{
	"target": "192.168.1.1",
	"stealth_level": 7,
	"findings": [...],
	"strategy": {...},
	"scan_hash": "192.168.1.1-1234567890"
}
```

Respuesta esperada:

```json
{ "status": "success", "id": 123 }
```

Se recomienda a los integradores tomar estos payloads como plantilla y validar contra los `schemas` definidos en `src/api/schemas.py`.

---

> Seguridad: crea un archivo `.env.example` con variables de entorno de ejemplo y mantén el archivo `.env` real fuera del repositorio (añádelo a `.gitignore`).

## ⚠️ Disclaimer — Aviso Legal

OptiVeil fue desarrollado **estricta y exclusivamente** para fines académicos, de investigación y auditorías defensivas autorizadas.

El uso de esta herramienta para actividades no autorizadas es ilegal. El autor no asume responsabilidad por el mal uso.

Actúa con ética. Audita solo lo que tienes autorización explícita para auditar.