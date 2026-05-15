from fastapi import APIRouter, HTTPException, Response
import os
import markdown
from xhtml2pdf import pisa
from io import BytesIO


router = APIRouter(prefix="/api", tags=["Intelligence Reports"])


@router.get("/reports")
def list_reports():
    """ Devuelve una lista de los reportes de inteligencia disponibles en la carpeta results/reports_IA con su nombre de archivo y el objetivo al que corresponden. """
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


@router.get("/reports/{filename}")
def get_report_content(filename: str):
    """ Devuelve el contenido de un reporte específico dado su nombre de archivo. """
    file_path = os.path.join("results/reports_IA", filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    
    with open(file_path, "r", encoding="utf-8") as f:
        return {"content": f.read()}
    

@router.get("/reports/{filename}/pdf")
async def export_report_pdf(filename: str):
    """ Genera un PDF a partir de un reporte de inteligencia en formato Markdown. Aplica estilos personalizados para mejorar la presentación y devuelve el PDF como una descarga. """
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