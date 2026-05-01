# 🛡️ OptiVeil Core
**Framework de Auditoría Evolutiva y Threat Intelligence**

OptiVeil es una plataforma de ciberseguridad avanzada diseñada para realizar escaneos tácticos de red. Utiliza algoritmos genéticos (NSGA-II) para optimizar la evasión de firmas IDS/IPS, equilibrando dinámicamente el ruido generado en la red y el tiempo de escaneo.

---

## 🧠 Arquitectura del Sistema

El proyecto está construido bajo una arquitectura moderna de microservicios contenerizados:

| Capa | Tecnología | Rol |
|---|---|---|
| **Frontend** | React + Vite | Dashboard táctico e interfaz en tiempo real |
| **Backend** | FastAPI (Python) | Orquestación ágil y telemetría |
| **Motor Evolutivo** | NSGA-II (`pymoo`) | Toma de decisiones multicriterio |
| **Motor de Escaneo** | Nmap (`python-nmap`) | Descubrimiento de servicios y puertos |
| **Inteligencia Artificial** | LangChain + OpenAI | Análisis de vulnerabilidades y generación de estrategias |
| **Base de Datos** | PostgreSQL | Persistencia histórica y Módulo Delta |

### ¿Por qué NSGA-II?

A diferencia de herramientas tradicionales que usan parámetros fijos, OptiVeil trata la configuración del escaneo como un **problema de optimización multiobjetivo**: minimizar simultáneamente el riesgo de detección (ruido en red) y el tiempo de ejecución. NSGA-II genera un **Frente de Pareto** de configuraciones no dominadas, y el parámetro `stealth_level` permite al operador navegar ese frente según su necesidad táctica.

---

## 🚀 Requisitos Previos

Antes de comenzar, asegúrate de tener instalado y configurado lo siguiente:

1. **[Git](https://git-scm.com/downloads)** — Para clonar el repositorio.
2. **[Docker Desktop](https://www.docker.com/products/docker-desktop/)** — O Docker Engine + Docker Compose en Linux. Asegúrate de que el servicio esté corriendo.
3. **[Npcap](https://npcap.com/#download)** *(solo Windows)* — Requerido por Scapy para captura de paquetes a nivel de driver.
4. **API Key de OpenAI** — Necesaria para el motor de análisis IA.

---

## 🛠️ Instalación y Despliegue

### Paso 1: Clonar el repositorio

```bash
git clone https://github.com/tu-usuario/OptiVeil.git
cd OptiVeil
```

### Paso 2: Configurar las variables de entorno

Por seguridad, las credenciales no están incluidas en el código. Crea un archivo `.env` en la raíz del proyecto con el siguiente contenido:

```env
DATABASE_URL=postgresql://postgres:password_seguro@db:5432/optiveildb
OPENAI_API_KEY=sk-TU_LLAVE_AQUI
```

> **Importante:** Reemplaza `sk-TU_LLAVE_AQUI` con tu API Key real de OpenAI. Nunca compartas ni subas este archivo a un repositorio público.

### Paso 3: Construir y orquestar los contenedores

```bash
docker-compose up -d --build
```

> La primera ejecución puede tardar unos minutos mientras Docker descarga las imágenes base de Linux, Python y Node.js.

### Paso 4: Acceder a la interfaz

Una vez que los contenedores estén en estado `Running`:

- **Dashboard Táctico (Frontend):** [http://localhost](http://localhost)
- **Documentación de la API (Backend):** [http://localhost:8000/docs](http://localhost:8000/docs)

### Paso 5: Detener el framework

```bash
docker-compose down
```

---

## 🖥️ Uso desde CLI

OptiVeil también puede operarse directamente desde la línea de comandos, sin necesidad del frontend:

```bash
# Requiere permisos de Administrador en Windows
python src/IA_guard/cli.py <IP_OBJETIVO> --stealth <1-10> --ports <N>

# Ejemplo: escanear los primeros 100 puertos con sigilo nivel 7
python src/IA_guard/cli.py 192.168.1.1 --stealth 7 --ports 100
```

| Parámetro | Descripción | Rango |
|---|---|---|
| `IP_OBJETIVO` | IPv4 del host a auditar | — |
| `--stealth` | Nivel de sigilo (1 = rápido, 10 = máximo sigilo) | 1–10 |
| `--ports` | Cantidad de puertos a escanear (desde el puerto 1) | 1–65535 |

---

## ⚠️ Disclaimer — Aviso Legal

OptiVeil fue desarrollado **estricta y exclusivamente** para fines académicos, de investigación (aplicación de optimización multiobjetivo en redes) y para auditorías de seguridad defensivas autorizadas.

El uso de esta herramienta para escanear, auditar o atacar redes, servidores u objetivos **sin el consentimiento previo, explícito y por escrito de sus propietarios** es una actividad ilegal y penada por la ley en la mayoría de jurisdicciones.

El autor y desarrollador de este repositorio **no asume ninguna responsabilidad** directa ni indirecta por el mal uso, daño, pérdida de datos o consecuencias legales derivadas de la utilización de este software.

Al clonar, instalar o ejecutar este código, el usuario acepta **total y absoluta responsabilidad** por sus acciones.

> Actúa con ética. Audita solo lo que tienes autorización explícita de auditar.