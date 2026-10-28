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




# Config de escaneo: los 3 parámetros que optimiza NSGA-II. Los rangos son
# espejo de CONFIG_BOUNDS en src/modules/stealth/nsga_II.py (el espacio de
# búsqueda del problema), atados por un test de consistencia para evitar deriva.
# Así solo se aceptan configs dentro del espacio que NSGA optimiza (zero-trust):
# un valor fuera de rango da 422 al parsear la request, sin tocar la red.
class ScanConfig(BaseModel):
    wait_time_ms: float = Field(..., ge=10, le=5000)
    packet_size: int = Field(..., ge=64, le=1500)
    threads: int = Field(..., ge=1, le=10)


class ScanRequest(BaseModel):
    target: IPvAnyAddress = Field(..., example="186.64.114.50")
    stealth: int = Field(5, ge=1, le=10)
    ports: int = Field(100, ge=1, le=65535)
    # Config explícita elegida en el Frente de Pareto (SPEC-0006): si viene, manda
    # sobre `stealth`; si es None, se deriva de `stealth` como siempre (no-regresión).
    config: ScanConfig | None = None


class ParetoPoint(BaseModel):
    index: int
    noise: float
    time: float
    config: ScanConfig


class ParetoFrontResponse(BaseModel):
    ports: int
    pareto_front: list[ParetoPoint]


class NmapFinding(BaseModel):
    port: int
    service: str
    banner: str


class LiveStrategyRequest(BaseModel):
    target: str
    stealth: int
    findings: list[NmapFinding]


class ValidationRequest(BaseModel):
    target: str
    findings: list[NmapFinding]


class ValidationResult(BaseModel):
    port: int | None = None
    service: str = "unknown"
    # confirmed | likely | not_confirmed | not_tested
    status: str = "not_tested"
    # Evidencia reproducible (redactada): {reproduce, snippet, template, matches}.
    evidence: dict = Field(default_factory=dict)
    source: str = ""
    # SPEC-0007: qué, dónde y con qué gravedad (para reportar, no solo etiquetar).
    name: str = ""
    severity: str = "unknown"      # critical|high|medium|low|info|unknown
    location: str = ""             # URL/ruta exacta del hallazgo
    vuln_class: str = ""           # clase legible de la vulnerabilidad