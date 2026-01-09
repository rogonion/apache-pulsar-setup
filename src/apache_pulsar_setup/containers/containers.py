import typer
from rich.console import Console
from .core import app as core_app
from .runtime import app as runtime_app
from .connectors import app as connectors_app

app = typer.Typer(help="Container components for the apache pulsar stack.")
console = Console()

app.add_typer(core_app, name="core")
app.add_typer(runtime_app, name="runtime")
app.add_typer(connectors_app, name="connectors")
