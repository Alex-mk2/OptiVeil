import numpy as np
from pymoo.core.problem import ElementwiseProblem
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
from pymoo.operators.crossover.sbx import SBX
from pymoo.operators.mutation.pm import PM
from pymoo.operators.sampling.rnd import FloatRandomSampling

class OptiVeilSthealthProblem(ElementwiseProblem):
    def __init__(self, target_ports):
        self.target_ports = target_ports
        super().__init__(n_var=3,
                         n_obj=2,
                         n_ieq_constr = 0,
                         xl = np.array([10, 64, 1]),  
                         xu = np.array([5000, 1500, 10]))                 
        

    def _evaluate(self, x, out, *args, **kwargs):
        wait_time = x[0] 
        packet_size = x[1] 
        threads = x[2] 
        
        ruido = (1000 / wait_time) * threads
        
        if packet_size < 128:
            ruido *= 1.5
        
        tiempo_ejecucion = (self.target_ports / threads) * (wait_time / 1000.0)
        
        out["F"] = [ruido, tiempo_ejecucion]

def run_nsga_ii(target_ports: int = 1000):
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