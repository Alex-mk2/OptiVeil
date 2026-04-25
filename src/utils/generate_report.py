import json
from datetime import datetime
from pathlib import Path


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