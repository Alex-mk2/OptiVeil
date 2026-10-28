from functools import lru_cache

import numpy as np
from pymoo.core.problem import ElementwiseProblem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.operators.sampling.rnd import FloatRandomSampling

# Rango del espacio de búsqueda de la config de sigilo (xl/xu del problema).
# Única fuente de verdad: lo usa el problema para acotar NSGA-II y lo refleja la
# validación de la API (ver ScanConfig en src/api/schemas.py, atada por un test
# de consistencia). Orden de las variables: wait_time_ms, packet_size, threads.
CONFIG_BOUNDS = {
    "wait_time_ms": (10.0, 5000.0),
    "packet_size": (64, 1500),
    "threads": (1, 10),
}

class OptiVeilSthealthProblem(ElementwiseProblem):
    def __init__(self, target_ports):
        self.target_ports = target_ports
        super().__init__(
            n_var=3,
            n_obj=2,
            n_ieq_constr=0,
            xl=np.array([CONFIG_BOUNDS["wait_time_ms"][0],
                         CONFIG_BOUNDS["packet_size"][0],
                         CONFIG_BOUNDS["threads"][0]]),
            xu=np.array([CONFIG_BOUNDS["wait_time_ms"][1],
                         CONFIG_BOUNDS["packet_size"][1],
                         CONFIG_BOUNDS["threads"][1]]),
        )


    def _evaluate(self, x, out, *args, **kwargs):
        wait_time = x[0] 
        packet_size = x[1] 
        threads = x[2] 
        
        ruido = (1000 / wait_time) * threads
        
        if packet_size < 128:
            ruido *= 1.5
        
        tiempo_ejecucion = (self.target_ports / threads) * (wait_time / 1000.0)
        
        out["F"] = [ruido, tiempo_ejecucion]

@lru_cache(maxsize=32)
def run_nsga_ii(target_ports: int = 1000):
    """Ejecuta NSGA-II para un número de puertos dado.

    El Frente de Pareto solo depende de `target_ports`, así que se cachea:
    escaneos repetidos con el mismo recuento reutilizan la optimización en vez
    de recalcular 100 generaciones. Los arrays devueltos son de solo lectura
    para los llamadores (no se mutan aguas abajo).
    """
    problem = OptiVeilSthealthProblem(target_ports)
    
    algorithm = NSGA2(
        pop_size=100,
        n_offsprings=20,
        sampling=FloatRandomSampling(),
        crossover=SBX(prob=0.9, eta=15),
        mutation=PM(prob=0.1, eta=20),
        eliminate_duplicates=True
    )
    
    res = minimize(problem,
                   algorithm,
                   ('n_gen', 100),
                   verbose=False)
    
    return res.X, res.F

def select_best_configuration(X, F, stealth_level: int):
    stealth_level = max(1, min(10, stealth_level))
    sorted_indices = np.argsort(F[:, 0])  
    num_solutions = len(sorted_indices)
    
    percentile = (10 - stealth_level) / 9.0
    target_index = int(percentile * (num_solutions - 1))
    
    best_index = sorted_indices[target_index]
    best_x = X[best_index]
    best_f = F[best_index]
    
    config_seleccionada = {
        "wait_time_ms": float(best_x[0]),
        "packet_size": int(best_x[1]),
        "threads": int(best_x[2]),
        "metrics": {
            "noise_score": float(best_f[0]),
            "estimated_time_sec": float(best_f[1])
        }
    }
    
    pareto_data = [
        {"noise": float(f[0]), "time": float(f[1])} 
        for f in F
    ]
    
    return {
        "config": config_seleccionada,
        "pareto_front": pareto_data
    }


def pareto_front_with_configs(X, F):
    """Empareja cada solución (`X`) con sus objetivos (`F`) en puntos del frente,
    ordenados por ruido ascendente y con la config de cada punto, para que la API
    exponga el frente completo y el operador elija una solución concreta.

    Solo lectura: no muta `X` ni `F` (son los arrays cacheados de `run_nsga_ii`).
    """
    orden = np.argsort(F[:, 0])
    puntos = []
    for idx in orden:
        x = X[idx]
        f = F[idx]
        puntos.append({
            "index": int(idx),
            "noise": float(f[0]),
            "time": float(f[1]),
            "config": {
                "wait_time_ms": float(x[0]),
                "packet_size": int(x[1]),
                "threads": int(x[2]),
            },
        })
    return puntos


def metrics_for_config(config: dict, target_ports: int) -> dict:
    """Evalúa una config explícita con la MISMA función de fitness del problema
    (minimización), para no confiar en métricas que mande el cliente ni duplicar
    la fórmula. Devuelve `noise_score` y `estimated_time_sec`.
    """
    problem = OptiVeilSthealthProblem(target_ports)
    out = {}
    x = np.array(
        [config["wait_time_ms"], config["packet_size"], config["threads"]],
        dtype=float,
    )
    problem._evaluate(x, out)
    f = out["F"]
    return {"noise_score": float(f[0]), "estimated_time_sec": float(f[1])}