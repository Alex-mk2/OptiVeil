import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from modules.stealth.nsga_II import run_nsga_ii, select_best_configuration
from modules.stealth.scanner import StealthScanner
from utils.generate_report import save_audit_report
from inter.fingerprint import ServiceIdentifier
from inter.response import RuleGenerator
from inter.ai_analyzer import analizar_auditoria
from utils.pareto_plot import plot_pareto_front

class OptiVeilEngine:
    def __init__(self, target: str, stealth: int, ports_count: int):
        self.target = target
        self.stealth = stealth
        self.ports_count = ports_count

    def execute(self, status_callback=None):
        def notify(msg):
            if status_callback:
                status_callback(msg)

        notify(f"Optimizando parámetros para sigilo {self.stealth}...")
        X, F = run_nsga_ii(target_ports=self.ports_count)
        
        optimization_data = select_best_configuration(X, F, stealth_level=self.stealth)
        
        best_config = optimization_data["config"]
        pareto_front = optimization_data["pareto_front"]
        
        plot_pareto_front(F, target=self.target)

        notify(f"Escaneando {self.target} (Bajo el radar)...")
        with StealthScanner(target_ip=self.target, config=best_config) as scanner:
            puertos_abiertos = scanner.run(ports_to_scan=list(range(1, self.ports_count + 1)))

        if not puertos_abiertos:
            return {
                "status": "no_ports_found", 
                "best_config": best_config,
                "pareto_front": pareto_front
            }

        notify("Identificando servicios y sistemas operativos...")
        hallazgos_detallados = []
        identificador = ServiceIdentifier(timeout=2)
        
        for puerto_num, os_guess in puertos_abiertos:
            info = identificador.identify(self.target, puerto_num)
            info["os_guess"] = os_guess
            hallazgos_detallados.append(info)

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
        reporte_ia = analizar_auditoria(ruta_reporte)
        ruta_md = f"results/reports_IA/executive_{self.target.replace('.', '_')}.md"
        os.makedirs("results/reports_IA", exist_ok=True)
        with open(ruta_md, "w", encoding="utf-8") as f:
            f.write(reporte_ia)

        return {
            "status": "success",
            "target": self.target,
            "best_config": best_config,
            "findings": hallazgos_detallados,
            "pareto_front": pareto_front,
            "files": {
                "json": ruta_reporte,
                "yara": ruta_reglas,
                "markdown": ruta_md
            }
        }