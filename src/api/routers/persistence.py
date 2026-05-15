from fastapi import APIRouter, Depends, HTTPException, Response
from requests import Session
from src.api import models
from src.api.database import get_db
from datetime import datetime


router = APIRouter(prefix="/api", tags=["Persistence"])


@router.post("/persistence/sync")
def sync_persistence(data: dict, db: Session = Depends(get_db)): 
    """ Sincroniza los resultados de un escaneo con la base de datos. Recibe un diccionario con información sobre el objetivo, nivel de sigilo, hallazgos, estrategia de ataque y un hash único del escaneo. Intenta crear un nuevo registro en la tabla AuditScan con estos datos y lo guarda en la base de datos. Si el proceso es exitoso, devuelve el ID del nuevo registro; si ocurre un error, revierte la transacción y devuelve un mensaje de error. """
    try:
        new_scan = models.AuditScan(
            target=data.get("target"),
            stealth_level=data.get("stealth_level", 5),
            findings=data.get("findings"),
            attack_roadmap=data.get("strategy"),
            scan_hash=data.get("scan_hash", f"{data.get('target')}-{datetime.utcnow().timestamp()}")
        )
        db.add(new_scan)
        db.commit()
        db.refresh(new_scan)
        return {"status": "success", "id": new_scan.id}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/persistence/latest")
def get_latest_audit(target: str = None, db: Session = Depends(get_db)):
    """ Obtiene el último escaneo registrado para un objetivo específico. Consulta la base de datos para encontrar el último registro en la tabla AuditScan que coincida con el objetivo proporcionado (si se especifica) y devuelve información relevante como el objetivo, nivel de sigilo, hallazgos y estrategia de ataque. Si no se encuentra ningún escaneo, indica que no hay datos disponibles. """
    query = db.query(models.AuditScan)
    
    if target:
        query = query.filter(models.AuditScan.target == target)
        
    latest_scan = query.order_by(models.AuditScan.created_at.desc()).first()
    
    if not latest_scan:
        return {"has_data": False}
        
    return {
        "has_data": True,
        "target": latest_scan.target,
        "stealth_level": latest_scan.stealth_level,
        "findings": latest_scan.findings,
        "strategy": latest_scan.attack_roadmap
    }
    

@router.get("/delta/{target}")
def calculate_delta_registry(target: str, db: Session = Depends(get_db)):
    """ Calcula el delta entre los dos últimos escaneos registrados para un objetivo específico. Consulta la base de datos para obtener los dos escaneos más recientes relacionados con el objetivo, extrae los hallazgos de cada uno y compara los puertos detectados para identificar cuáles se han agregado, eliminado o cambiado. Devuelve un resumen estructurado del delta, incluyendo la cantidad total de cambios y las listas de puertos agregados, eliminados o modificados. Si no hay suficientes datos para calcular el delta, devuelve un mensaje indicando la falta de información. """
    
    scans = db.query(models.AuditScan).filter(models.AuditScan.target == target).order_by(models.AuditScan.created_at.desc()).limit(2).all()
    
    
    if len(scans) < 2:
        return {"status": "insufficient_data", "message": "No hay suficientes escaneos para calcular delta."}
    
    latest_findings = scans[0].findings if isinstance(scans[0].findings, list) else []
    previous_findings = scans[1].findings if isinstance(scans[1].findings, list) else []
    
    dict_latest = {item.get("port"): item for item in latest_findings if isinstance(item, dict) and "port" in item}
    dict_previous = {item.get("port"): item for item in previous_findings if isinstance(item, dict) and "port" in item}
    
    latest_ports = set(dict_latest.keys())
    previous_ports = set(dict_previous.keys())
    
    added_ports = latest_ports - previous_ports
    removed_ports = previous_ports - latest_ports
    
    added_list = [dict_latest[p] for p in added_ports]
    removed_list = [dict_previous[p] for p in removed_ports]
    
    return {
        "status": "success",
        "delta_score": len(added_list) + len(removed_list),
        "added": added_list,
        "removed": removed_list,
        "changed": [] 
    }