"""Configuración compartida de pytest.

Añade la raíz del proyecto y `src/` al sys.path para que los tests puedan
importar tanto como `src.inter.xxx` (estilo API) como `inter.xxx`
(estilo engine, que usa sys.path.append en runtime).
"""
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.path.join(PROJECT_ROOT, "src")

for path in (PROJECT_ROOT, SRC):
    if path not in sys.path:
        sys.path.insert(0, path)

# Permite importar los módulos de la API sin una BD real: create_engine()
# acepta una URL sqlite en memoria sin conectarse. Solo si no hay una definida.
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
