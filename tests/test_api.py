"""Tests de endpoints con TestClient sobre una BD sqlite en memoria.

Cubre el ciclo de jobs de /scan (con el motor mockeado), la topología y
los 404. No toca PostgreSQL ni la red.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from src.api import models
from src.api.database import Base, get_db
from src.api.main import app
from src.api.routers import scanner


FAKE_RESULT = {
    "status": "success",
    "best_config": {"wait_time_ms": 1000.0, "packet_size": 200, "threads": 4,
                     "metrics": {"noise_score": 2.5, "estimated_time_sec": 10.0}},
    "findings": [{"port": 22, "service": "ssh", "banner": "OpenSSH_9", "risk": "LOW (...)"}],
    "pareto_front": [{"noise": 2.5, "time": 10.0}],
    "attack_roadmap": {"steps": []},
    "files": {},
}


class _FakeEngine:
    def __init__(self, *args, **kwargs):
        pass

    def execute(self, status_callback=None):
        return FAKE_RESULT


@pytest.fixture
def client(monkeypatch):
    # BD sqlite en memoria compartida entre conexiones (request y worker).
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    def _get_test_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    # El worker de background usa SessionLocal directamente: lo apuntamos a la BD de test.
    monkeypatch.setattr(scanner, "SessionLocal", TestingSessionLocal)
    # El motor real (NSGA-II/Scapy/IA) se reemplaza por uno falso y determinista.
    monkeypatch.setattr(scanner, "OptiVeilEngine", _FakeEngine)

    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as c:
        c._SessionLocal = TestingSessionLocal  # por si un test quiere sembrar datos
        yield c
    app.dependency_overrides.clear()


def test_health_check(client):
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["status"].startswith("OptiVeil")


def test_scan_encola_y_completa_job(client):
    # TestClient ejecuta las BackgroundTasks tras la respuesta, de forma síncrona.
    r = client.post("/api/scan", json={"target": "10.0.0.5", "stealth": 5, "ports": 50})
    assert r.status_code == 202
    body = r.json()
    assert body["status"] == "pending"
    job_id = body["job_id"]

    r2 = client.get(f"/api/scan/{job_id}")
    assert r2.status_code == 200
    done = r2.json()
    assert done["status"] == "done"
    assert done["findings"] == FAKE_RESULT["findings"]
    assert done["best_config"]["metrics"]["noise_score"] == 2.5


def test_scan_persiste_auditoria(client):
    client.post("/api/scan", json={"target": "10.0.0.9", "stealth": 3, "ports": 20})
    db = client._SessionLocal()
    try:
        scans = db.query(models.AuditScan).filter(models.AuditScan.target == "10.0.0.9").all()
        assert len(scans) == 1
        assert scans[0].findings == FAKE_RESULT["findings"]
    finally:
        db.close()


def test_scan_status_job_inexistente_404(client):
    r = client.get("/api/scan/no-existe")
    assert r.status_code == 404


def test_topology_vacia_sin_datos(client):
    r = client.get("/api/topology/1.2.3.4")
    assert r.status_code == 200
    assert r.json() == {"nodes": [], "edges": []}


def test_topology_con_hallazgos(client):
    # Sembramos un scan directamente en la BD de test.
    db = client._SessionLocal()
    try:
        db.add(models.AuditScan(
            target="5.5.5.5", stealth_level=5, best_config={},
            findings=[{"port": 22, "service": "ssh"}, {"port": 80, "service": "http"}],
            scan_hash="seed-5.5.5.5",
        ))
        db.commit()
    finally:
        db.close()

    r = client.get("/api/topology/5.5.5.5")
    assert r.status_code == 200
    data = r.json()
    ids = {n["id"] for n in data["nodes"]}
    assert "attacker" in ids and "target" in ids
    assert "port-22" in ids and "port-80" in ids


# --- SPEC-0006: config explícita del Frente de Pareto en /api/scan ---

def test_scan_rechaza_config_fuera_de_rango(client):
    # threads=99 está fuera del espacio del problema (1-10): 422 al parsear, sin escanear.
    r = client.post("/api/scan", json={
        "target": "10.0.0.5", "stealth": 5, "ports": 50,
        "config": {"wait_time_ms": 1000, "packet_size": 256, "threads": 99},
    })
    assert r.status_code == 422


def test_scan_pasa_config_explicita_al_motor(client, monkeypatch):
    # Un motor espía captura el kwarg `config` con el que se instancia.
    capturado = {}

    class _SpyEngine:
        def __init__(self, *args, **kwargs):
            capturado["config"] = kwargs.get("config")

        def execute(self, status_callback=None):
            return {
                "status": "success",
                "best_config": FAKE_RESULT["best_config"],
                "findings": [],
                "pareto_front": [],
                "attack_roadmap": {"steps": []},
                "scan_stats": {},
            }

    monkeypatch.setattr(scanner, "OptiVeilEngine", _SpyEngine)
    cfg = {"wait_time_ms": 1234.0, "packet_size": 256, "threads": 4}
    r = client.post("/api/scan", json={
        "target": "10.0.0.5", "stealth": 5, "ports": 50, "config": cfg,
    })
    assert r.status_code == 202
    # La BackgroundTask ya corrió (TestClient la ejecuta tras la respuesta).
    assert capturado["config"] == cfg


def test_scan_sin_config_no_regresiona(client):
    # Sin `config`, el flujo es el de siempre (el motor falso decide): job completa.
    r = client.post("/api/scan", json={"target": "10.0.0.7", "stealth": 5, "ports": 50})
    assert r.status_code == 202
    job_id = r.json()["job_id"]
    done = client.get(f"/api/scan/{job_id}").json()
    assert done["status"] == "done"
