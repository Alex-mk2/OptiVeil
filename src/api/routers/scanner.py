from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime
import subprocess
import xml.etree.ElementTree as ET
from src.api.schemas import ScanRequest
from src.core.engine import OptiVeilEngine
from src.api.database import get_db
from src.api import models


router = APIRouter(prefix="/api", tags=["Scanner & Topology"])


@router.post("/scan")
async def start_scan(request: ScanRequest, db: Session = Depends(get_db)):
    """ Inicia un escaneo utilizando OptiVeilEngine con los parámetros proporcionados y almacena los resultados en la base de datos. """
    try:
        engine = OptiVeilEngine(target=str(request.target), stealth=request.stealth, ports_count=request.ports)
        result = engine.execute()
        
        scan = models.AuditScan(
            target=str(request.target),
            stealth_level=request.stealth,
            best_config=result["best_config"],
            findings=result["findings"],
            attack_roadmap=result.get("attack_roadmap"),
            scan_hash=f"{str(request.target)}-{datetime.utcnow().timestamp()}"
        )
        db.add(scan)
        db.commit()
        db.refresh(scan)

        return {
            "best_config": result["best_config"],
            "findings": result["findings"],
            "pareto_front": result["pareto_front"],
            "status": result["status"],
            "attack_roadmap": result.get("attack_roadmap"),
        }
    except Exception as e:
        print(f"CRITICAL ERROR EN API: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    

@router.get("/topology/{target}")
def get_topology(target: str, db: Session = Depends(get_db)):
    """ Devuelve la topología de red y los hallazgos relacionados para un objetivo específico. Consulta la base de datos para obtener el último escaneo realizado sobre el objetivo y construye una representación de nodos y conexiones basada en los hallazgos encontrados, como puertos abiertos y servicios detectados. Si no se encuentran datos, devuelve una estructura vacía. """
    scan = db.query(models.AuditScan).filter(models.AuditScan.target == target).order_by(models.AuditScan.id.desc()).first()
    
    
    if not scan or not scan.findings:
        return {"nodes": [], "edges": []}

    nodes = [
        {
            "id": "attacker", 
            "type": "tactical", 
            "position": {"x": 250, "y": 0},
            "data": {
                "type": "attacker",
                "label_title": "Terminal Ofensiva",
                "label_value": "OptiVeil Core"
            }
        },
        {
            "id": "target", 
            "type": "tactical", 
            "position": {"x": 250, "y": 150},
            "data": {
                "type": "target",
                "label_title": "Objetivo",
                "label_value": target
            }
        }
    ]
    
    edges = [{"id": "e1", "source": "attacker", "target": "target", "animated": True}]

    if isinstance(scan.findings, list):
        lista_puertos = scan.findings
    elif isinstance(scan.findings, dict):
        lista_puertos = scan.findings.get("ports", [])
    else:
        lista_puertos = []

    for i, port_info in enumerate(lista_puertos):
        if isinstance(port_info, dict):
            port_num = port_info.get("port", "Desconocido")
            service_name = port_info.get("service", "Servicio").upper()
        else:
            port_num = port_info[0] if len(port_info) > 0 else "N/A"
            service_name = port_info[1].upper() if len(port_info) > 1 else "SERVICIO"

        port_id = f"port-{port_num}"
        nodo_tipo = "critical" if port_num in [21, 80, 23, 445] else "port"
        
        nodes.append({
            "id": port_id,
            "type": "tactical",
            "position": {"x": (i * 180) + 50, "y": 300},
            "data": {
                "type": nodo_tipo,
                "label_title": f"Puerto {port_num}",
                "label_value": service_name
            }
        })
        edges.append({"id": f"e-{port_id}", "source": "target", "target": port_id})

    return {"nodes": nodes, "edges": edges}


@router.post("/nmap")
def execute_nmap(req: ScanRequest):
    """ Ejecuta un escaneo de Nmap con los parámetros especificados en la solicitud. Construye el comando de Nmap dinámicamente según el nivel de sigilo y la cantidad de puertos a escanear, ejecuta el comando y procesa la salida XML para extraer información sobre los puertos abiertos, servicios y banners detectados. Devuelve un resumen estructurado de los hallazgos o un error si la ejecución falla. """
    nmap_command = ["nmap", "-sV", "-O", "-oX", "-"]
    
    
    if req.stealth > 7:
        nmap_command.append("-T0")
    elif req.stealth > 4:
        nmap_command.append("-T2")
    else:
        nmap_command.append("-T3")
        
        
    if req.ports < 65535:
        nmap_command.extend(["--top-ports", str(req.ports)])
    else:
        nmap_command.append("-p-")
        
    nmap_command.append(str(req.target))


    try:
        result = subprocess.run(nmap_command, capture_output=True, text=True, check=True)
        
        root = ET.fromstring(result.stdout)
        puertos_encontrados = []
        
        for host in root.findall('host'):
            for port in host.findall('.//port'):
                if port.find('state').get('state') == 'open':
                    service = port.find('service')
                    if service is not None:
                        banner = f"{service.get('product', '')} {service.get('version', '')}".strip()
                        puertos_encontrados.append({
                            "port": int(port.get('portid')),
                            "service": service.get('name', 'unknown').upper(), 
                            "banner": banner if banner else "BANNER OCULTO"
                        })
                        
        return {
            "target": str(req.target),
            "stealth_applied": req.stealth,
            "status": "success",
            "findings": puertos_encontrados
        }

    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Fallo en ejecución de Nmap: {e.stderr}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))