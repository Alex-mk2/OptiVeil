from fastapi import APIRouter, HTTPException
import os
import json
from src.inter.IA_offensive import generate_attack_path
from src.api.schemas import LiveStrategyRequest


router = APIRouter(prefix="/api", tags=["Attack Strategies"])

STRATEGY_DIR = "results/attack_reports"


def _safe_strategy_path(target: str) -> str:
    """Resuelve la ruta del archivo de estrategia validando que quede dentro
    de STRATEGY_DIR (evita path-traversal con `..`, `/` o rutas absolutas)."""
    base = os.path.abspath(STRATEGY_DIR)
    target_clean = target.replace(".", "_")
    file_path = os.path.abspath(os.path.join(base, f"strategy_{target_clean}.json"))
    if os.path.commonpath([base, file_path]) != base:
        raise HTTPException(status_code=400, detail="Objetivo inválido")
    return file_path


@router.get("/strategy/{target}")
def get_strategy_content(target: str):
    """ Devuelve el contenido de la estrategia de ataque generada para un objetivo específico. Busca en results/attack_reports el archivo JSON del objetivo (validando la ruta contra path-traversal). Si existe, devuelve su contenido; si no, 404. """
    file_path = _safe_strategy_path(target)
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)

    raise HTTPException(status_code=404, detail=f"Estrategia no encontrada para {target}")


@router.post("/strategy/live")
def generate_live_strategy(req: LiveStrategyRequest):
    """ Genera una estrategia de ataque en tiempo real basada en los hallazgos proporcionados. Calcula un nivel de ruido ajustado a partir del nivel de sigilo especificado, construye una lista de hallazgos en formato texto a partir de la información de puertos, servicios y banners detectados, y luego llama a la función generate_attack_path para obtener una estrategia de ataque estructurada en formato JSON. Devuelve la estrategia generada o un error si el proceso falla. """
    try:
        ruido_calculado = 10.0 - float(req.stealth)
        hallazgos = [
            {"port": f.port, "service": f.service, "banner": f.banner}
            for f in req.findings
        ]

        estrategia_json = generate_attack_path(hallazgos, ruido_calculado)
        return estrategia_json

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))