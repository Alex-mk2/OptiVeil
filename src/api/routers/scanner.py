import logging
import uuid
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from datetime import datetime
import subprocess
import xml.etree.ElementTree as ET
from src.api.schemas import ScanRequest
from src.core.engine import OptiVeilEngine
from src.modules.stealth.nsga_II import run_nsga_ii, select_best_configuration
from src.api.database import get_db, SessionLocal
from src.api import models
from src.core.scope import enforce_scope


logger = logging.getLogger("optiveil.scanner")

router = APIRouter(prefix="/api", tags=["Scanner & Topology"])


def parse_nmap_xml(xml_output: str) -> list[dict]:
    """Extrae los puertos abiertos de la salida XML de Nmap.

    Función pura (sin red ni subprocess) para poder testearla con fixtures.
    Lanza ET.ParseError si el XML es inválido.
    """
    root = ET.fromstring(xml_output)
    puertos_encontrados = []
    for host in root.findall('host'):
        for port in host.findall('.//port'):
            state = port.find('state')
            if state is None or state.get('state') != 'open':
                continue
            service = port.find('service')
            if service is None:
                continue
            banner = f"{service.get('product', '')} {service.get('version', '')}".strip()
            puertos_encontrados.append({
                "port": int(port.get('portid')),
                "service": service.get('name', 'unknown').upper(),
                "banner": banner if banner else "BANNER OCULTO",
            })
    return puertos_encontrados


def _run_scan_job(job_id: str, target: str, stealth: int, ports: int):
    """Ejecuta el motor en un worker síncrono (threadpool de Starlette), con su
    propia sesión de BD, y persiste el estado del job. No bloquea el event loop."""
    db = SessionLocal()
    try:
        job = db.query(models.ScanJob).filter(models.ScanJob.id == job_id).first()
        if job is None:
            logger.error("Job %s desapareció antes de iniciar", job_id)
            return
        job.status = "running"
        db.commit()

        engine = OptiVeilEngine(target=target, stealth=stealth, ports_count=ports)
        result = engine.execute()

        scan = models.AuditScan(
            target=target,
            stealth_level=stealth,
            best_config=result.get("best_config"),
            findings=result.get("findings"),
            attack_roadmap=result.get("attack_roadmap"),
            scan_hash=f"{target}-{datetime.utcnow().timestamp()}",
        )
        db.add(scan)

        job.status = "done"
        job.result = {
            "best_config": result.get("best_config"),
            "findings": result.get("findings"),
            "pareto_front": result.get("pareto_front"),
            "scan_status": result.get("status"),  # estado del motor (success/no_ports_found)
            "attack_roadmap": result.get("attack_roadmap"),
            "scan_stats": result.get("scan_stats"),
        }
        db.commit()
    except Exception as e:
        logger.exception("Fallo en el job de escaneo %s", job_id)
        db.rollback()
        job = db.query(models.ScanJob).filter(models.ScanJob.id == job_id).first()
        if job is not None:
            job.status = "error"
            job.error = str(e)
            db.commit()
    finally:
        db.close()


@router.post("/scan", status_code=202)
def start_scan(request: ScanRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Encola un escaneo en background y devuelve un job_id para consultar su estado.
    El trabajo pesado (NSGA-II, Scapy, IA) corre fuera del event loop."""
    enforce_scope("scan", str(request.target))
    job_id = uuid.uuid4().hex
    job = models.ScanJob(
        id=job_id,
        target=str(request.target),
        stealth_level=request.stealth,
        ports=request.ports,
        status="pending",
    )
    db.add(job)
    db.commit()

    background_tasks.add_task(
        _run_scan_job, job_id, str(request.target), request.stealth, request.ports
    )
    return {"job_id": job_id, "status": "pending"}


@router.get("/scan/{job_id}")
def get_scan_status(job_id: str, db: Session = Depends(get_db)):
    """Devuelve el estado del job y, si terminó, su resultado completo."""
    job = db.query(models.ScanJob).filter(models.ScanJob.id == job_id).first()
    if job is None:
        raise HTTPException(status_code=404, detail="Job no encontrado")

    payload = {"job_id": job.id}
    if job.status == "done":
        payload.update(job.result or {})
    elif job.status == "error":
        payload["error"] = job.error
    payload["status"] = job.status  # el estado del job siempre manda sobre el payload
    return payload


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
    # nmap -sV -O es la acción más intrusiva de la app: debe pasar por el scope
    # (y quedar auditada) ANTES de tocar la red. Va fuera del try para que el 403
    # no lo capture el `except Exception` de abajo y se degrade a 500.
    enforce_scope("nmap", str(req.target))

    nmap_command = ["nmap", "-sV", "-O", "-oX", "-"]

    # Premisa del proyecto: NSGA-II es el motor que optimiza la configuración de
    # sigilo y nmap la ejecuta. En vez de los presets -T (3 velocidades fijas que
    # pelearían con un timing explícito), se deriva la config Pareto-óptima para el
    # nº de puertos y el stealth pedido, y se mapea a los flags equivalentes de nmap.
    num_ports = min(req.ports, 65535)
    X, F = run_nsga_ii(target_ports=num_ports)
    config = select_best_configuration(X, F, stealth_level=req.stealth)["config"]

    # wait_time_ms -> --scan-delay; threads -> --max-parallelism; packet_size ->
    # --data-length (relleno aditivo: aproxima la dimensión de tamaño del motor).
    scan_delay_ms = int(round(config["wait_time_ms"]))
    max_parallelism = int(config["threads"])
    data_length = int(config["packet_size"])
    nmap_command.extend([
        "--scan-delay", f"{scan_delay_ms}ms",
        "--max-parallelism", str(max_parallelism),
        "--data-length", str(data_length),
    ])

    if req.ports < 65535:
        nmap_command.extend(["--top-ports", str(req.ports)])
    else:
        nmap_command.append("-p-")

    nmap_command.append(str(req.target))


    try:
        result = subprocess.run(
            nmap_command, capture_output=True, text=True, check=True, timeout=300
        )

        puertos_encontrados = parse_nmap_xml(result.stdout)

        return {
            "target": str(req.target),
            "stealth_applied": req.stealth,
            "status": "success",
            "findings": puertos_encontrados,
            # Config que NSGA-II seleccionó y que nmap ejecutó (visibilidad: deja
            # claro que el sigilo es el del motor, no un preset de nmap).
            "nsga_config": {
                "scan_delay_ms": scan_delay_ms,
                "max_parallelism": max_parallelism,
                "data_length": data_length,
                "noise_score": config["metrics"]["noise_score"],
                "estimated_time_sec": config["metrics"]["estimated_time_sec"],
            },
        }

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Timeout: Nmap excedió el tiempo límite (300s).")
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Nmap no está instalado o no está en el PATH.")
    except subprocess.CalledProcessError as e:
        raise HTTPException(status_code=500, detail=f"Fallo en ejecución de Nmap: {e.stderr}")
    except ET.ParseError:
        raise HTTPException(status_code=500, detail="Salida de Nmap no es XML válido.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))