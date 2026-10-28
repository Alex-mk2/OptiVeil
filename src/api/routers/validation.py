from fastapi import APIRouter, HTTPException

from src.inter.validator import validate_findings
from src.inter.exposure import find_exposed_routes
from src.api.schemas import ValidationRequest
from src.core.scope import enforce_scope


router = APIRouter(prefix="/api", tags=["Validation"])


@router.post("/validate")
def validate_findings_endpoint(req: ValidationRequest):
    """Valida de forma NO destructiva dónde y cómo es explotable un objetivo
    (SPEC-0002/0003/0007).

    Acción activa sobre el objetivo => scope en modo ESTRICTO: sin scope definido
    o target fuera de alcance, se rechaza con 403 **antes** de tocar la red.
    Devuelve una lista de veredictos con clase, ubicación, severidad y evidencia
    reproducible redactada, de dos fuentes NO destructivas:
    - nuclei (plantillas de detección por servicio);
    - búsqueda de rutas que exponen información sensible (forced browsing GET).
    """
    enforce_scope("validate", req.target, strict=True)
    try:
        findings = [
            {"port": f.port, "service": f.service, "banner": f.banner}
            for f in req.findings
        ]
        # Ambos backends son no destructivos. Se concatenan en una lista plana:
        # las exposiciones de rutas son entradas propias (cada una con su location).
        results = validate_findings(req.target, findings)
        results += find_exposed_routes(req.target, findings)
        return {"results": results}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
