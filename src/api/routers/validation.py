from fastapi import APIRouter, HTTPException

from src.inter.validator import validate_findings
from src.api.schemas import ValidationRequest
from src.core.scope import enforce_scope


router = APIRouter(prefix="/api", tags=["Validation"])


@router.post("/validate")
def validate_findings_endpoint(req: ValidationRequest):
    """Valida de forma NO destructiva si los hallazgos son explotables (SPEC-0002).

    Acción activa sobre el objetivo => scope en modo ESTRICTO: sin scope definido
    o target fuera de alcance, se rechaza con 403 (al revés del modo pasivo de
    laboratorio). Devuelve, por hallazgo, un veredicto
    (confirmed/likely/not_confirmed/not_tested) con evidencia reproducible y
    redactada.
    """
    enforce_scope("validate", req.target, strict=True)
    try:
        findings = [
            {"port": f.port, "service": f.service, "banner": f.banner}
            for f in req.findings
        ]
        results = validate_findings(req.target, findings)
        return {"results": results}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
