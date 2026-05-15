from fastapi import APIRouter, HTTPException
import os
import json
from src.inter.IA_offensive import generate_attack_path
from src.api.schemas import LiveStrategyRequest


router = APIRouter(prefix="/api", tags=["Attack Strategies"])


@router.get("/strategy/{target}")
def get_strategy_content(target: str):
    """ Devuelve el contenido de la estrategia de ataque generada para un objetivo específico. Busca en la carpeta results/attack_reports por archivos JSON que contengan el nombre del objetivo. Si encuentra una coincidencia, devuelve su contenido; de lo contrario, indica que no se encontró la estrategia. """
    
    target_clean = target.replace(".", "_")
    posibles_rutas = [
        os.path.join("results/attack_reports", f"strategy_{target_clean}.json")
    ]
    
    
    for file_path in posibles_rutas:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
                
    raise HTTPException(status_code=404, detail=f"Estrategia no encontrada para {target}")


@router.post("/strategy/live")
def generate_live_strategy(req: LiveStrategyRequest):
    """ Genera una estrategia de ataque en tiempo real basada en los hallazgos proporcionados. Calcula un nivel de ruido ajustado a partir del nivel de sigilo especificado, construye una lista de hallazgos en formato texto a partir de la información de puertos, servicios y banners detectados, y luego llama a la función generate_attack_path para obtener una estrategia de ataque estructurada en formato JSON. Devuelve la estrategia generada o un error si el proceso falla. """
    try:
        ruido_calculado = 10.0 - float(req.stealth)
        hallazgos_texto = [
            f"Puerto {f.port} ({f.service}) - Banner/Versión: {f.banner}" 
            for f in req.findings
        ]
        
        estrategia_json = generate_attack_path(hallazgos_texto, ruido_calculado)
        return estrategia_json
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))