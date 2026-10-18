"""Tests de autorización: scope y audit log."""
import json

import pytest
from fastapi.testclient import TestClient

from src.core import scope as scope_mod
from src.core.scope import parse_scope, is_in_scope, audit_log
from src.api.main import app


def test_parse_scope_ignora_comentarios_y_blancos():
    entries = parse_scope(["# comentario", "", "  10.0.0.1  ", "scanme.nmap.org"])
    assert entries == ["10.0.0.1", "scanme.nmap.org"]


def test_sin_scope_permite_todo():
    assert is_in_scope("8.8.8.8", []) is True


def test_scope_ip_exacta():
    assert is_in_scope("10.0.0.5", ["10.0.0.5"]) is True
    assert is_in_scope("10.0.0.6", ["10.0.0.5"]) is False


def test_scope_cidr():
    assert is_in_scope("192.168.1.42", ["192.168.1.0/24"]) is True
    assert is_in_scope("192.168.2.42", ["192.168.1.0/24"]) is False


def test_scope_hostname_exacto():
    assert is_in_scope("scanme.nmap.org", ["scanme.nmap.org"]) is True
    assert is_in_scope("evil.com", ["scanme.nmap.org"]) is False


def test_audit_log_escribe_json(tmp_path):
    path = tmp_path / "audit.log"
    audit_log("scan", "10.0.0.1", True, detail="test", path=str(path))
    audit_log("scan", "8.8.8.8", False, path=str(path))
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    first = json.loads(lines[0])
    assert first["action"] == "scan" and first["allowed"] is True


def test_scan_fuera_de_scope_devuelve_403(monkeypatch):
    monkeypatch.setenv("OPTIVEIL_SCOPE", "10.0.0.0/8")
    with TestClient(app) as c:
        r = c.post("/api/scan", json={"target": "8.8.8.8", "stealth": 5, "ports": 5})
    assert r.status_code == 403


def test_strategy_fuera_de_scope_devuelve_403(monkeypatch):
    monkeypatch.setenv("OPTIVEIL_SCOPE", "10.0.0.0/8")
    with TestClient(app) as c:
        r = c.post("/api/strategy/live", json={
            "target": "8.8.8.8", "stealth": 5,
            "findings": [{"port": 22, "service": "ssh", "banner": "x"}],
        })
    assert r.status_code == 403
