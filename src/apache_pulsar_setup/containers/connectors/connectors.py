import typer

from .postgres_sink import app as postgres_sink_app

app = typer.Typer(help="Connectors for the pulsar stack.")

app.add_typer(postgres_sink_app, name="postgres-sink")
