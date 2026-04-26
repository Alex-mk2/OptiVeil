import os
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Agg')


def plot_pareto_front(F, best_idx=None, target="objective"):
    """
    Genera y guarda la gráfica del Frente de Pareto del NSGA-II.
    F: Lista de tuplas/arrays con los valores (Ruido, Tiempo).
    best_idx: Índice de la mejor configuración elegida para resaltarla.
    """
    ruido = [f[0] for f in F]
    tiempo = [f[1] for f in F]

    plt.figure(figsize=(10, 6))
    plt.scatter(ruido, tiempo, alpha=0.6, label='Soluciones Óptimas (Frontera)')
    
    
    if best_idx is not None:
        plt.scatter(ruido[best_idx], tiempo[best_idx], s=100, marker='*', 
                    label='Configuración Elegida', zorder=5)

    plt.title(f'Frente de Pareto OptiVeil NSGA-II - {target}')
    plt.xlabel('Objetivo 1: Score de Ruido (Minimizar)')
    plt.ylabel('Objetivo 2: Tiempo Estimado (s) (Minimizar)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()

    
    os.makedirs("results/plots", exist_ok=True)
    ruta_imagen = f"results/plots/pareto_{target.replace('.', '_')}.png"
    plt.savefig(ruta_imagen, dpi=300, bbox_inches='tight')
    plt.close()
    
    return ruta_imagen