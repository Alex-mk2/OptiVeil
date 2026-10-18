from fastapi import APIRouter, HTTPException, Response
import os

from src.inter.cve_intel import fetch_cves


router = APIRouter(prefix="/api", tags=["Intelligence"])


@router.get("/rules/{target}")
def get_rule_content(target: str):
    """ Devuelve el contenido de la regla YARA correspondiente a un objetivo específico. Busca en la carpeta results/rules por archivos que contengan el nombre del objetivo y terminen con .yar. Si encuentra una coincidencia, devuelve su contenido; de lo contrario, indica que no se encontró la regla. """
    
    
    rules_dir = "results/rules"
    if not os.path.exists(rules_dir):
        return {"content": "// Carpeta de reglas no encontrada"}
    target_clean = target.replace(".", "_")
        
        
    for f in os.listdir(rules_dir):
        if (target in f or target_clean in f) and f.endswith(".yar"):
            with open(os.path.join(rules_dir, f), "r", encoding="utf-8") as file:
                return {"content": file.read()}
    
    return {"content": f"// Regla no encontrada para {target} (Busqué: {target_clean})"}


@router.get("/cve/{service_banner}")
def search_cves(service_banner: str):
    """ Busca CVEs relacionadas con un banner de servicio en el NVD (NIST) y devuelve un resumen estructurado. """
    cves = fetch_cves(service_banner)
    return {
        "target_service": service_banner,
        "total_found": len(cves),
        "cves": cves,
    }