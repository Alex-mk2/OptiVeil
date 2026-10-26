"""Configuración compartida de pytest.

Añade la raíz del proyecto y `src/` al sys.path para que los tests puedan
importar tanto como `src.inter.xxx` (estilo API) como `inter.xxx`
(estilo engine, que usa sys.path.append en runtime).
"""
import os
import sys

import pytest

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(PROJECT_ROOT, "src")

for path in (PROJECT_ROOT, SRC):
    if path not in sys.path:
        sys.path.insert(0, path)

# Permite importar los módulos de la API sin una BD real: create_engine()
# acepta una URL sqlite en memoria sin conectarse. Solo si no hay una definida.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")

# Aísla los tests del .env del desarrollador. `database.py` hace load_dotenv() al
# importarse, así que un OPTIVEIL_SCOPE local se colaría en el entorno de test y
# sacaría de scope a los targets de prueba (p. ej. 10.0.0.1), rompiendo con 403
# los tests de escaneo/estrategia que asumen modo pasivo. Se fija ANTES de que se
# importe la app (load_dotenv no sobrescribe variables ya definidas). Los tests que
# necesitan scope lo ponen con monkeypatch.setenv, que sí tiene prioridad.
os.environ["OPTIVEIL_SCOPE"] = ""
os.environ["OPTIVEIL_SCOPE_FILE"] = os.path.join(PROJECT_ROOT, "__no_scope_file__")


@pytest.fixture(autouse=True)
def _silence_audit_log(monkeypatch):
    """Evita que enforce_scope escriba en results/audit.log durante los tests.
    El test unitario de audit_log usa su import directo y no se ve afectado."""
    try:
        import src.core.scope as scope
        monkeypatch.setattr(scope, "audit_log", lambda *a, **k: None)
    except Exception:
        pass
