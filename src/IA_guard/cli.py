import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import sys
import os

#Rutas relativas para importar módulos internos
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from modules.stealth.nsga_II import run_nsga_ii, select_best_configuration
from modules.stealth.scanner import StealthScanner
from utils.generate_report import save_audit_report
from inter.fingerprint import ServiceIdentifier
from inter.response import RuleGenerator


app = typer.Typer(help="OptiVeil: Framework de Auditoría Evolutiva y Sigilosa")
console = Console()


@app.command()
def audit(
    target: str = typer.Argument(..., help="IP o subred objetivo (ej. 192.168.1.0/24)"),
    stealth: int = typer.Option(5, "--stealth", "-s", min=1, max=10, help="Nivel de sigilo (1-10)"),
    ports: int = typer.Option(1000, "--ports", "-p", help="Cantidad de puertos a escanear")
):
    """Ejecuta una auditoría evolutiva y sigilosa contra el objetivo especificado."""

    console.print(Panel(
        f"[bold green]Iniciando OptiVeil[/bold green]\n"
        f"Objetivo: [cyan]{target}[/cyan]\n"
        f"Nivel de Sigilo: [yellow]{stealth}/10[/yellow]",
        expand=False
    ))

    with console.status("[bold green]Ejecutando auditoría NSGA-II...[/bold green]", spinner="dots"):
        X, F = run_nsga_ii(target_ports=ports)
        best_config = select_best_configuration(X, F, stealth_level=stealth)
    
    console.print(Panel("[bold green]Auditoría Completa[/bold green]\n"))

    table = Table(
        title="Parámetros de Escaneo Seleccionados",
        show_header=True,
        header_style="bold magenta"
    )
    
    table.add_column("Parámetro", justify="left")
    table.add_column("Valor Calculado", justify="right")
    table.add_row("Tiempo de Espera (ms)",            f"{best_config['wait_time_ms']:.2f}")
    table.add_row("Tamaño del Paquete (bytes)",        f"{best_config['packet_size']}")
    table.add_row("Número de Hilos",                   f"{best_config['threads']}",                          style="cyan")
    table.add_row("Score de Ruido (f1)",               f"{best_config['metrics']['noise_score']:.2f}",       style="red")
    table.add_row("Tiempo de Ejecución Estimado (s)",  f"{best_config['metrics']['estimated_time_sec']:.2f}", style="cyan")
    console.print(table)


    try:
        with console.status("[bold green]Ejecutando escaneo sigiloso...[/bold green]", spinner="dots"):
            with StealthScanner(target_ip=target, config=best_config) as scanner:
                puertos_abiertos = scanner.run(ports_to_scan=list(range(1, ports + 1)))
                
    except PermissionError as e:
        console.print(Panel(
            f"[bold red]Error de Permisos[/bold red]\n{e}",
            expand=False
        ))
        raise typer.Exit(code=1)
    
    
    hallazgos_detallados = []
    if puertos_abiertos:
        console.print("\n[bold yellow]Iniciando recolección de inteligencia (Fingerprinting)...[/bold yellow]")
        identificador = ServiceIdentifier(timeout=2)
        
        with console.status("[bold yellow]Analizando servicios en puertos abiertos...[/bold yellow]", spinner="bouncingBar"):
            for puerto in puertos_abiertos:
                info = identificador.identify(target, puerto)
                hallazgos_detallados.append(info)
                
                if info["service"] not in ["timeout", "closed", "error", "unknown"]:
                    console.print(f"  [+] Puerto [green]{puerto}[/green]: [bold cyan]{info['service'].upper()}[/bold cyan] -> [dim]{info['banner']}[/dim]")
                else:
                    estado = info['service'].upper() if info['service'] != 'empty_response' else 'SIN BANNER'
                    console.print(f"  [+] Puerto [green]{puerto}[/green]: [bold red]OPEN[/bold red] -> [dim]({estado})[/dim]")
        
        console.print(Panel(
            "[bold green]¡Auditoría y Recolección de Inteligencia Completadas![/bold green]",
            expand=False
        ))


        try:
            ruta_reporte = save_audit_report(
                target=target, 
                stealth_level=stealth, 
                config=best_config, 
                open_ports=hallazgos_detallados
            )
            console.print(f"[dim]Evidencia táctica guardada en: {ruta_reporte}[/dim]")

            
            generator = RuleGenerator({"ports": hallazgos_detallados})
            yara_rules = generator.generate_yara_rule()
            
            ruta_reglas = f"results/rules/rules_{target.replace('.', '_')}.yar"
            with open(ruta_reglas, "w") as f:
                f.write(yara_rules)
            
            console.print(f"[bold blue]Reglas de detección YARA generadas en: {ruta_reglas}[/bold blue]\n")

        except Exception as e:
            console.print(f"[bold red]Error en la fase de finalización:[/bold red] {e}")
            
    else:
        console.print(Panel(
            "[bold yellow]No se encontraron puertos abiertos en el objetivo.[/bold yellow]",
            expand=False
        ))


if __name__ == "__main__":
    app()