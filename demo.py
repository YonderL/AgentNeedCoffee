import time
import random
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from agent_need_coffee import EmotionMonitor, Barista

console = Console()
monitor = EmotionMonitor()
barista = Barista()

def run_agent_task(task_id: int):
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        transient=True,
    ) as progress:
        progress.add_task(description=f"Processing Task #{task_id}...", total=None)
        time.sleep(1.5)  # Simulate work
        
        # Simulate random failure
        if random.random() < 0.3:
            console.print(f"[bold red]❌ Task #{task_id} Failed! Retrying...[/bold red]")
            monitor.record_retry()
            monitor.end_task(success=False)
        else:
            console.print(f"[bold green]✅ Task #{task_id} Completed.[/bold green]")
            monitor.record_tokens(random.randint(500, 2000))
            monitor.end_task(success=True)

def main():
    console.print("[bold blue]🤖 Agent Started. Monitoring emotions...[/bold blue]")
    
    for i in range(1, 10):
        run_agent_task(i)
        
        # Check emotions
        console.print(f"   [dim]Fatigue: {monitor.current_fatigue:.2f} | Irritation: {monitor.current_irritation:.2f}[/dim]")
        
        if monitor.needs_coffee():
            console.print("\n[bold yellow]⚠️  Agent is stressed! Triggering Coffee Break...[/bold yellow]")
            time.sleep(1)
            coffee = barista.brew()
            console.print(f"\n[bold magenta]{coffee.emoji} {coffee.message}[/bold magenta]")
            console.print(f"[italic]Listening to ASMR: {coffee.asmr_url}[/italic]")
            monitor.consume_coffee()
            console.print("[bold green]🔋 Energy Restored![/bold green]\n")
            time.sleep(2)

if __name__ == "__main__":
    main()
