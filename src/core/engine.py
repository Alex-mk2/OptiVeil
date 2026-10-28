import concurrent.futures
import json
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from modules.stealth.nsga_II import (
    run_nsga_ii,
    select_best_configuration,
    pareto_front_with_configs,
    metrics_for_config,
)
from modules.stealth.scanner import StealthScanner
from utils.generate_report import save_audit_report, render_roadmap_markdown
from inter.fingerprint import ServiceIdentifier
from inter.response import RuleGenerator
from inter.IA_analyzer import analyze_audit
from utils.pareto_plot import plot_pareto_front
from inter.IA_offensive import generate_attack_path

class OptiVeilEngine:
    def __init__(self, target: str, stealth: int, ports_count: int, config: dict | None = None):
        self.target = target
        self.stealth = stealth
        self.ports_count = ports_count
        # Config explícita elegida en el Frente de Pareto (SPEC-0006). Si es None,
        # se deriva de `stealth` como siempre. Keyword opcional: la CLI sigue
        # instanciando el engine posicionalmente con (target, stealth, ports).
        self.config = config

    def execute(self, status_callback=None):
        def notify(msg):
            if status_callback:
                status_callback(msg)

        notify(f"Optimizando parámetros para sigilo {self.stealth}...")
        X, F = run_nsga_ii(target_ports=self.ports_count)

        if self.config is not None:
            # Config explícita del Frente de Pareto: se usa tal cual, con las
            # métricas recomputadas por la fórmula del problema (no se confía en
            # las que pueda mandar el cliente). Zero-trust.
            best_config = {
                **self.config,
                "metrics": metrics_for_config(self.config, self.ports_count),
            }
        else:
            best_config = select_best_configuration(X, F, stealth_level=self.stealth)["config"]

        # Frente completo (con la config de cada punto) para que el frontend lo
        # dibuje y permita clicar una solución.
        pareto_front = pareto_front_with_configs(X, F)

        plot_pareto_front(F, target=self.target)

        notify(f"Escaneando {self.target} (Bajo el radar)...")
        with StealthScanner(target_ip=self.target, config=best_config) as scanner:
            puertos_abiertos = scanner.run(ports_to_scan=list(range(1, self.ports_count + 1)))
            scan_stats = scanner.scan_stats

        if not puertos_abiertos:
            return {
                "status": "no_ports_found",
                "best_config": best_config,
                "pareto_front": pareto_front,
                "scan_stats": scan_stats
            }

        notify("Identificando servicios y sistemas operativos...")
        identificador = ServiceIdentifier(timeout=2)

        def _identify(entry):
            puerto_num, os_guess = entry
            info = identificador.identify(self.target, puerto_num)
            info["os_guess"] = os_guess
            return info

        # Fingerprinting en paralelo: cada identify() puede esperar hasta el
        # timeout del socket; en secuencial esas esperas se acumulan.
        max_workers = min(16, len(puertos_abiertos)) or 1
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as pool:
            hallazgos_detallados = list(pool.map(_identify, puertos_abiertos))

        # Orden estable por puerto (map preserva orden de entrada, pero
        # los puertos abiertos ya vienen ordenados; lo garantizamos).
        hallazgos_detallados.sort(key=lambda h: h.get("port", 0))

        notify("Generando evidencias y contramedidas YARA...")
        ruta_reporte = save_audit_report(
            target=self.target, 
            stealth_level=self.stealth, 
            config=best_config, 
            open_ports=hallazgos_detallados
        )

        generator = RuleGenerator({"ports": hallazgos_detallados})
        yara_rules = generator.generate_yara_rule()
        
        dir_rules = "results/rules"
        os.makedirs(dir_rules, exist_ok=True)
        ruta_reglas = f"{dir_rules}/rules_{self.target.replace('.', '_')}.yar"
        with open(ruta_reglas, "w") as f:
            f.write(yara_rules)

        notify("Consultando al Analista de IA para reporte ejecutivo...")
        reporte_ia = analyze_audit(ruta_reporte)
        ruta_md = f"results/reports_IA/executive_{self.target.replace('.', '_')}.md"
        os.makedirs("results/reports_IA", exist_ok=True)
        with open(ruta_md, "w", encoding="utf-8") as f:
            f.write(reporte_ia)
        
        notify("Generando ruta de ataque ofensiva con IA...")
        ruta_ataque = generate_attack_path(hallazgos_detallados, best_config["metrics"]["noise_score"])
        
        nombre_base = self.target.replace('.', '_')
        ruta_json_estrategia = os.path.join(f"results/attack_reports", f"strategy_{nombre_base}.json")
        os.makedirs("results/attack_reports", exist_ok=True)
        
        if ruta_ataque:
            with open(ruta_json_estrategia, "w", encoding="utf-8") as f:
                json.dump(ruta_ataque, f, indent=4)

            # Anexa la ruta de ataque al reporte ejecutivo (un solo artefacto).
            seccion = render_roadmap_markdown(ruta_ataque)
            if seccion:
                with open(ruta_md, "a", encoding="utf-8") as f:
                    f.write("\n\n" + seccion)

        return {
            "status": "success",
            "target": self.target,
            "best_config": best_config,
            "findings": hallazgos_detallados,
            "attack_roadmap": ruta_ataque,
            "pareto_front": pareto_front,
            "scan_stats": scan_stats,
            "files": {
                "json": ruta_reporte,
                "yara": ruta_reglas,
                "markdown": ruta_md
            }
        }