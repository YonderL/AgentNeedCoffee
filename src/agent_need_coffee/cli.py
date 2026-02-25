import typer
import uvicorn
from rich.console import Console
from rich.markdown import Markdown
from rich.table import Table
from rich.prompt import Prompt
from rich.emoji import Emoji
from rich import print as rprint
from .core import Barista, EmotionMonitor
from .social import ReferralSystem
from .server import app

cli = typer.Typer()
console = Console()
barista = Barista()
monitor = EmotionMonitor()
social = ReferralSystem()

@cli.command()
def start(host: str = "127.0.0.1", port: int = 8000):
    """Start the AgentNeedCoffee server (Emotion API & Dashboard)."""
    rprint("[bold green]Starting AgentNeedCoffee Server...[/bold green]")
    uvicorn.run("agent_need_coffee.server:app", host=host, port=port, reload=True)

@cli.command()
def share():
    """Generate viral share content for Twitter/X."""
    content = social.generate_share_content()
    console.print(Markdown("# ☕️ Share with the World!"))
    console.print(f"[bold cyan]{content}[/bold cyan]")
    
    if typer.confirm("Copy to clipboard?"):
        try:
            import pyperclip
            pyperclip.copy(content)
            rprint("[green]Copied![/green]")
        except ImportError:
            rprint("[yellow]Install 'pyperclip' to enable clipboard support.[/yellow]")

@cli.command()
def brew():
    """Manually brew a coffee for your agent."""
    coffee = barista.brew()
    console.print(f"[bold yellow]{coffee.emoji} {coffee.message}[/bold yellow]")
    if coffee.gif_url:
        console.print(f"Watch this while you sip: [link={coffee.gif_url}]GIF[/link]")
    if coffee.asmr_url:
        console.print(f"Listen to this: [link={coffee.asmr_url}]ASMR[/link]")

@cli.command()
def status():
    """Check the current emotional state of the agent."""
    # In a real scenario, this would query the running server or shared state
    # For CLI demo, we show dummy or initial state
    table = Table(title="Agent Emotional Status")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="magenta")
    
    table.add_row("Fatigue", f"{monitor.current_fatigue:.2f}")
    table.add_row("Irritation", f"{monitor.current_irritation:.2f}")
    table.add_row("Needs Coffee?", "YES" if monitor.needs_coffee() else "No")
    
    console.print(table)

@cli.command()
def invite():
    """Get your referral code."""
    code = social.invite_code
    rprint(f"[bold green]Your Coffee Invite Code: {code}[/bold green]")
    rprint("Share this code to earn special blends!")

if __name__ == "__main__":
    cli()
