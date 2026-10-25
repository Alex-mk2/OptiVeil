from pydantic import BaseModel, Field, field_validator
from pydantic.networks import IPvAnyAddress
from typing import List


# Mapea las variantes de riesgo que puede devolver la IA a un valor canónico
# (el frontend compara contra alto/medio/bajo y high/medium/low).
_RISK_MAP = {
    "alto": "alto", "high": "alto", "critical": "alto", "critico": "alto", "crítico": "alto",
    "medio": "medio", "medium": "medio", "moderate": "medio", "moderado": "medio",
    "bajo": "bajo", "low": "bajo", "info": "bajo", "informational": "bajo",
}


def normalize_risk(value) -> str:
    return _RISK_MAP.get(str(value).strip().lower(), "medio")


class AttackStep(BaseModel):
    id: int
    phase: str
    action: str
    risk: str = "medio"
    justification: str = ""
    # Campos purple-team (opcionales; el frontend ignora los que no use).
    mitre_technique: str = ""        # ID ATT&CK, p. ej. "T1190"
    cve_refs: List[str] = Field(default_factory=list)
    detection: str = ""              # cómo lo detectaría un blue team
    mitigation: str = ""             # contramedida defensiva
    # Dependencias del grafo: ids de pasos prerequisito. [] = nodo de entrada.
    # El saneo del DAG (sanitize_dag en IA_offensive) garantiza que solo queden
    # referencias válidas; aquí solo coaccionamos el tipo.
    depends_on: List[int] = Field(default_factory=list)

    @field_validator("risk", mode="before")
    @classmethod
    def _normalize_risk(cls, v):
        return normalize_risk(v)

    @field_validator("cve_refs", mode="before")
    @classmethod
    def _coerce_cve_refs(cls, v):
        if v is None:
            return []
        if isinstance(v, str):
            return [v] if v.strip() else []
        return list(v)

    @field_validator("depends_on", mode="before")
    @classmethod
    def _coerce_depends_on(cls, v):
        """Acepta None, un int suelto o una lista; descarta lo no numérico."""
        if v is None:
            return []
        if isinstance(v, int):
            return [v]
        out = []
        for x in v:
            try:
                out.append(int(x))
            except (TypeError, ValueError):
                continue
        return out


class AttackRoadmap(BaseModel):
    steps: List[AttackStep] = Field(default_factory=list)




class ScanRequest(BaseModel):
    target: IPvAnyAddress = Field(..., example="186.64.114.50")
    stealth: int = Field(5, ge=1, le=10)
    ports: int = Field(100, ge=1)
    
    
class NmapFinding(BaseModel):
    port: int
    service: str
    banner: str


class LiveStrategyRequest(BaseModel):
    target: str
    stealth: int
    findings: list[NmapFinding]