import json
from datetime import datetime
from pathlib import Path


def render_roadmap_markdown(roadmap: dict) -> str:
    """Convierte una hoja de ruta de ataque en una sección Markdown.

    Función pura y defensiva: tolera pasos sin los campos purple opcionales
    (mitre_technique, cve_refs, detection, mitigation).
    """
    if not roadmap or not roadmap.get("steps"):
        return ""

    lines = ["## 🎯 Ruta de Ataque (Purple Team)", ""]

    priorizados = roadmap.get("prioritized_findings") or []
    if priorizados:
        lines += ["### Hallazgos priorizados", "",
                  "| Prioridad | Puerto | Servicio | Riesgo | CVEs |",
                  "|---|---|---|---|---|"]
        for f in priorizados:
            cves = ", ".join(c.get("id", "") for c in (f.get("cves") or [])) or "—"
            lines.append(
                f"| {f.get('priority', '—')} | {f.get('port', '—')} | "
                f"{f.get('service', '—')} | {f.get('risk') or '—'} | {cves} |"
            )
        lines.append("")

    for step in roadmap["steps"]:
        lines.append(f"### Fase {step.get('id', '?')}: {step.get('phase', 'N/A')}")
        mitre = step.get("mitre_technique")
        if mitre:
            lines.append(f"- **MITRE ATT&CK:** `{mitre}`")
        lines.append(f"- **Acción:** {step.get('action', 'N/A')}")
        lines.append(f"- **Riesgo:** {step.get('risk', 'N/A')}")
        cve_refs = step.get("cve_refs") or []
        if cve_refs:
            lines.append(f"- **CVEs:** {', '.join(cve_refs)}")
        if step.get("justification"):
            lines.append(f"- **Justificación:** {step['justification']}")
        if step.get("detection"):
            lines.append(f"- **Detección (Blue Team):** {step['detection']}")
        if step.get("mitigation"):
            lines.append(f"- **Mitigación:** {step['mitigation']}")
        lines.append("")

    return "\n".join(lines)


def save_audit_report(target: str, stealth_level: int, config: dict, open_ports: list):
    """Guarda la evidencia de la auditoría para análisis posterior (Variación A)."""
    report_dir = Path("results/reports")
    report_dir.mkdir(parents=True, exist_ok=True)
    
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "target": target,
        "stealth_level": stealth_level,
        "optimization_metrics": {
            "wait_time_ms": config["wait_time_ms"],
            "packet_size": config["packet_size"],
            "threads": config["threads"],
            "noise_score_f1": config["metrics"]["noise_score"],
            "estimated_time_f2": config["metrics"]["estimated_time_sec"]
        },
        "findings": {
            "open_ports_count": len(open_ports),
            "ports": open_ports
        }
    }
    
    # Nombre de archivo: audit_IP_stealthN_timestamp.json
    filename = f"audit_{target.replace('.', '_')}_s{stealth_level}_{datetime.now().strftime('%H%M%S')}.json"
    full_path = report_dir / filename
    
    with open(full_path, "w") as f:
        json.dump(report_data, f, indent=4)
    
    return full_path