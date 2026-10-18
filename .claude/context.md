# OptiVeil - Project Context & Directives

## 1. Project Overview
OptiVeil is an open-source evolutionary auditing and threat intelligence framework. It automates network security scanning and generates evasive payloads using grammar-guided evolutionary fuzzing and coverage-guided red teaming techniques.

## 2. Directory Structure
- `/src`: Backend core powered by Python and FastAPI. Contains the API routers, database engine, and core services.
- `/frontend`: User interface built with TypeScript and React for visualizing telemetry and pareto fronts.
- `/data` & `/results`: Storage for scans, logs, and optimization outputs.
- `/tests`: Test suites for backend and frontend.

## 3. Tech Stack & Execution
- **Backend:** Python (managed via `pyproject.toml`), FastAPI, `scapy` (packet crafting), `pymoo` (NSGA-II).
- **Frontend:** TypeScript, React.
- **Infrastructure:** Docker (managed via `docker-compose.yml`).

## 4. Architectural Rules & Code Style (CRITICAL)
- **Zero Trust & Paranoid Validation:** All backend data pipelines, database queries, and system integrations MUST include strict input validation. Never trust external input or Scapy log data without sanitizing.
- **First-Principles Engineering:** Dissect underlying mechanics when writing code. Avoid black-box solutions; explicit configurations (like Scapy parameters or API routing) are preferred over magic abstractions.
- **Strict Typing:** Use Python type hints (`pydantic` models) for all FastAPI endpoints and TypeScript interfaces for all React components.

## 5. Algorithmic Constraints (DO NOT IGNORE)
- The evolutionary engine uses **NSGA-II**. 
- **Minimization Rule:** The optimization model operates STRICTLY as a MINIMIZATION problem. Whether optimizing for detection rate, execution time, or payload size, always structure the fitness functions and algorithms to minimize the objectives. NEVER implement maximization logic for the evolutionary engine.

## 6. Claude Code Workflow
- Before suggesting structural changes to the `/src` backend, verify the impact on the FastAPI routers.
- When generating or modifying network payloads, ensure Scapy layers are correctly stacked and handle timeouts gracefully.