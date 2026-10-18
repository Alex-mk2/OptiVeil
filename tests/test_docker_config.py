"""Guard de regresión de infraestructura.

Verifica que el servicio backend declara las capacidades que Scapy necesita
para los raw sockets. No prueba que el escaneo funcione (eso requiere Docker y
red), pero evita que NET_RAW/NET_ADMIN se borren por accidente del compose.
"""
import os

import pytest

yaml = pytest.importorskip("yaml")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMPOSE_PATH = os.path.join(PROJECT_ROOT, "docker-compose.yml")


@pytest.fixture(scope="module")
def backend_service():
    with open(COMPOSE_PATH, encoding="utf-8") as f:
        compose = yaml.safe_load(f)
    return compose["services"]["backend"]


@pytest.mark.parametrize("cap", ["NET_RAW", "NET_ADMIN"])
def test_backend_declara_capacidades_de_red(backend_service, cap):
    cap_add = backend_service.get("cap_add", [])
    assert cap in cap_add, f"docker-compose: backend debe declarar cap_add {cap}"


def test_backend_no_usa_privileged(backend_service):
    # cap_add acotado es preferible a privileged: true.
    assert not backend_service.get("privileged", False), \
        "Usa cap_add acotado, no privileged: true"
