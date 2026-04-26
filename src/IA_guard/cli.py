import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import sys
import os

#Rutas relativas para importar módulos internos
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from core.engine import OptiVeilEngine

app = typer.Typer(help="OptiVeil: Framework de Auditoría Evolutiva y Sigilosa")
console = Console()


@app.command()
def audit(target: str, stealth: int = 5, ports: int = 1000):
    console.print(Panel(f"[bold green]OptiVeil Tactical Engine[/bold green]\nObjetivo: [cyan]{target}[/cyan]", expand=False))
    engine = OptiVeilEngine(target, stealth, ports)


    with console.status("[bold green]Trabajando...[/bold green]", spinner="dots") as status:
        def update_status(msg):
            status.update(f"[bold green]{msg}[/bold green]")
        
        resultado = engine.execute(status_callback=update_status)

    if resultado["status"] == "success":
        config = resultado["best_config"]
        table = Table(title="Configuración Evolutiva Aplicada", header_style="bold magenta")
        table.add_column("Parámetro")
        table.add_column("Valor", justify="right")
        table.add_row("Espera (ms)", f"{config['wait_time_ms']:.2f}")
        table.add_row("Hilos", str(config['threads']))
        table.add_row("Ruido (f1)", f"{config['metrics']['noise_score']:.2f}", style="red")
        console.print(table)

        
        console.print("\n[bold yellow]Resultados de Inteligencia:[/bold yellow]")
        for info in resultado["findings"]:
            color = "green" if "LOW" in info.get("risk_level", "INFO") else "red"
            console.print(f" [+] Puerto [bold]{info['port']}[/bold]: [cyan]{info['service'].upper()}[/cyan] ([magenta]{info['os_guess']}[/magenta])")
            console.print(f"     [dim]{info['banner']}[/dim] -> [{color}]{info.get('risk_level', 'INFO')}[/{color}]")

        
        console.print(Panel(
            f"[bold green]Auditoría Finalizada[/bold green]\n"
            f"JSON: [dim]{resultado['files']['json']}[/dim]\n"
            f"IA Report: [dim]{resultado['files']['markdown']}[/dim]",
            expand=False
        ))
    else:
        console.print("[bold red]No se encontraron puertos abiertos o hubo un error en el escaneo.[/bold red]")

if __name__ == "__main__":
    app()