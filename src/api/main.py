from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
import os
import json
from io import BytesIO
import markdown
from xhtml2pdf import pisa
from pydantic import BaseModel, Field
from src.core.engine import OptiVeilEngine
from .database import engine, get_db
from sqlalchemy.orm import Session
from fastapi import Depends
from . import models



#Iniciamos la aplicación FastAPI
app = FastAPI(
    title="OptiVeil Core API",
    description="API de la plataforma de auditoría evolutiva",
    version="1.0.0"
)


#Ahora se configura el cors (para permitir peticiones desde el frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"], 
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)


#Se define que se busca dentro del escaneo
class ScanRequest(BaseModel):
    target: str = Field(..., example="186.64.114.50")
    stealth: int = Field(5, ge=1, le=10)
    ports: int = Field(100, ge=1)
    


#Se crean las tablas
models.Base.metadata.create_all(bind=engine)


#Ahora comienza lo que sería la configuracion de CRUD
@app.get("/")
def health_check():
    """Checkear el estado de la API"""
    return {"status": "OptiVeil API is running"}


@app.post("/api/scan")
async def start_scan(request: ScanRequest, db: Session = Depends(get_db)):
    """Instanciar el motor de auditoría y ejecutar el ciclo completo"""
    try:
        engine = OptiVeilEngine(target=request.target, stealth=request.stealth, ports_count=request.ports)
        result = engine.execute()
        
        
        scan = models.AuditScan(
            target=request.target,
            stealth_level=request.stealth,
            best_config=result["best_config"],
            findings=result["findings"],
            attack_roadmap=result.get("attack_roadmap")
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


@app.get("/api/reports/")
def list_reports():
    """Listar los reportes con metadatos para el frontend"""
    reports_dir = "results/reports_IA"
    if not os.path.exists(reports_dir):
        return [] 
    
    files = os.listdir(reports_dir)
    reports_data = []
    
    for f in files:
        if f.endswith(".md"):
            target_display = f.replace("executive_", "").replace(".md", "").replace("_", ".")
            reports_data.append({
                "filename": f,
                "target": target_display
            })
            
    return reports_data


@app.get("/api/reports/{filename}")
def get_report_content(filename: str):
    """Lee y devuelve el contenido de un reporte Markdown específico."""
    file_path = os.path.join("results/reports_IA", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    
    with open(file_path, "r", encoding="utf-8") as f:
        return {"content": f.read()}
    

@app.get("/api/rules/{target}")
def get_rule_content(target: str):
    """Busca la regla YARA asociada a un objetivo específico."""
    rules_dir = "results/rules"
    if not os.path.exists(rules_dir):
        return {"content": "// Carpeta de reglas no encontrada"}
    target_clean = target.replace(".", "_")
        
    for f in os.listdir(rules_dir):
        if (target in f or target_clean in f) and f.endswith(".yar"):
            with open(os.path.join(rules_dir, f), "r", encoding="utf-8") as file:
                return {"content": file.read()}
    
    return {"content": f"// Regla no encontrada para {target} (Busqué: {target_clean})"}


@app.get("/api/reports/{filename}/pdf")
async def export_report_pdf(filename: str):
    file_path = os.path.join("results/reports_IA", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Archivo no encontrado")

    with open(file_path, "r", encoding="utf-8") as f:
        md_content = f.read()
    html_content = markdown.markdown(md_content)
    
    
    styled_html = f"""
    <html>
        <head>
            <style>
                @page {{ size: A4; margin: 2cm; }}
                body {{ font-family: 'Helvetica', 'Arial', sans-serif; color: #333; }}
                h1 {{ color: #0891b2; border-bottom: 2px solid #0891b2; padding-bottom: 10px; }}
                h2, h3 {{ color: #1e293b; margin-top: 20px; }}
                pre {{ background-color: #f1f5f9; padding: 10px; border-radius: 5px; }}
                .footer {{ position: fixed; bottom: 0; width: 100%; text-align: center; font-size: 10px; color: #64748b; }}
            </style>
        </head>
        <body>
            <h1>REPORTE DE INTELIGENCIA - OPTIVEIL</h1>
            {html_content}
            <div class="footer">Generado automáticamente por OptiVeil Core - Framework de Auditoría Evolutiva</div>
        </body>
    </html>
    """
    pdf_buffer = BytesIO()
    pisa_status = pisa.CreatePDF(styled_html, dest=pdf_buffer)

    if pisa_status.err:
        raise HTTPException(status_code=500, detail="Error al generar el PDF")

    return Response(
        content=pdf_buffer.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=Reporte_OptiVeil_{filename.replace('.md', '.pdf')}"
        }
    )


@app.get("/api/strategy/{target}")
def get_strategy_content(target: str):
    """Busca y devuelve el JSON de la estrategia ofensiva para el objetivo."""
    target_clean = target.replace(".", "_")
    
    posibles_rutas = [
        os.path.join("results/attack_reports", f"strategy_{target_clean}.json")
    ]
    
    for file_path in posibles_rutas:
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
                
    raise HTTPException(status_code=404, detail=f"Estrategia no encontrada para {target}")


@app.get("/api/topology/{target}")
def get_topology(target: str, db: Session = Depends(get_db)):
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
            "position": {"x": 100 * (i + 1), "y": 300},
            "data": {
                "type": nodo_tipo,
                "label_title": f"Puerto {port_num}",
                "label_value": service_name
            }
        })
        edges.append({"id": f"e-{port_id}", "source": "target", "target": port_id})

    return {"nodes": nodes, "edges": edges}