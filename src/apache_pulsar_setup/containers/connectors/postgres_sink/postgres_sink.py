from pathlib import Path
from typing import Optional

import typer

from .builder import PostgresSinkBuilder
from apache_pulsar_setup.core import BuildSpec, load_spec

app = typer.Typer(help="Postgres JDBC sink")

@app.command("build", help="Build the postgres sink for apache pulsar.")
def build(
        spec_file: Optional[Path] = typer.Option("configs/build.yaml", "--spec", "--s",
                                                 help="Path to build specification file."),
        image_name: Optional[str] = typer.Option("apache-pulsar-postgres-sink", "--image-name", "--n",
                                                 help="Name of new image."),
        image_tag: Optional[str] = typer.Option("", "--image-tag", "--t",
                                                help="Optional. Tag of new image"),
        cache_prefix: Optional[str] = typer.Option("", "--cache-prefix", "--c",
                                                   help="Optional. Custom prefix for generated images acting as cache layers."),
        version: Optional[str] = typer.Option("latest", "--version", "--v", help="Optional. Version of connector.")
):
    """
    Build the postgres sink for apache pulsar.

    :param version:
    :param cache_prefix:
    :param spec_file:
    :param image_name:
    :param image_tag:
    :return:
    """
    config = load_spec(spec_file, BuildSpec)

    builder = PostgresSinkBuilder(config, cache_prefix, image_name, image_tag, version)

    builder.build()


@app.command("delete-cache", help="Delete cache images used to build the postgres sink for apache pulsar image.")
def delete_cache(
        spec_file: Optional[Path] = typer.Option("configs/build.yaml", "--spec", "--s",
                                                 help="Path to build specification file."),
        cache_prefix: Optional[str] = typer.Option("", "--cache-prefix", "--c",
                                                   help="Optional. Custom prefix for generated images acting as cache layers.")
):
    """
    Delete cache images used to build image.

    :param spec_file: Path to build spec file.
    :param cache_prefix: Custom prefix for cache layers generated.

    :return:
    """
    config = load_spec(spec_file, BuildSpec)

    builder = PostgresSinkBuilder(config, cache_prefix)

    builder.prune_cache_images()
