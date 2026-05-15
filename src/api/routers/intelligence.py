from fastapi import APIRouter, HTTPException, Response
import os
import requests


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
    """ Busca vulnerabilidades CVE relacionadas con un banner de servicio específico utilizando la base de datos del NIST. Construye una consulta a la API del NIST con el banner proporcionado, procesa la respuesta JSON para extraer información relevante sobre cada CVE encontrada, como su ID, descripción, puntuación y severidad, y devuelve un resumen estructurado de los resultados o un error si la consulta falla o no se encuentran vulnerabilidades. """
    try:
        url = f"https://services.nvd.nist.gov/rest/json/cves/2.0?keywordSearch={service_banner}&resultsPerPage=5"
        
        response = requests.get(url, timeout=15)
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail="Error al contactar la base de datos del NIST.")
            
        data = response.json()
        vulnerabilidades = []
        
        for item in data.get("vulnerabilities", []):
            cve_info = item.get("cve", {})
            cve_id = cve_info.get("id", "Desconocido")
            
            desc_list = cve_info.get("descriptions", [])
            descripcion = desc_list[0].get("value", "Sin descripción") if desc_list else "Sin descripción"
            
            metrics = cve_info.get("metrics", {})
            score = "N/A"
            severity = "UNKNOWN"
            
            if "cvssMetricV31" in metrics:
                score = metrics["cvssMetricV31"][0]["cvssData"]["baseScore"]
                severity = metrics["cvssMetricV31"][0]["cvssData"]["baseSeverity"]
                
            vulnerabilidades.append({
                "id": cve_id,
                "description": descripcion,
                "score": score,
                "severity": severity
            })
            
        return {
            "target_service": service_banner,
            "total_found": len(vulnerabilidades),
            "cves": vulnerabilidades
        }

    except requests.exceptions.Timeout:
        raise HTTPException(status_code=504, detail="Timeout: La base de datos del NIST tardó mucho en responder.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")