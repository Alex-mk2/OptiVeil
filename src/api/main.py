from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
import os
import json
from io import BytesIO
import markdown
from xhtml2pdf import pisa
from pydantic import BaseModel, Field
from src.core.engine import OptiVeilEngine

#Iniciamos la aplicación FastAPI
app = FastAPI(
    title="OptiVeil Core API",
    description="API de la plataforma de auditoría evolutiva",
    version="1.0.0"
)


#Ahora se configura el cors (para permitir peticiones desde el frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True
)


#Se define que se busca dentro del escaneo
class ScanRequest(BaseModel):
    target: str = Field(..., example="186.64.114.50")
    stealth: int = Field(5, ge=1, le=10)
    ports: int = Field(100, ge=1)
    
    

#Ahora comienza lo que sería la configuracion de CRUD
@app.get("/")
def health_check():
    """Checkear el estado de la API"""
    return {"status": "OptiVeil API is running"}


@app.post("/api/scan")
async def start_scan(request: ScanRequest):
    """Instanciar el motor de auditoría y ejecutar el ciclo completo"""
    try:
        engine = OptiVeilEngine(target=request.target, stealth=request.stealth, ports_count=request.ports)
        result = engine.execute()
        
        return {
            "best_config": result["best_config"],
            "findings": result["findings"],
            "pareto_front": result["pareto_front"],
            "status": result["status"]
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