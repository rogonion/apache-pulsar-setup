from pathlib import Path
from typing import Optional

import typer

from .builder import RuntimeBuilder
from apache_pulsar_setup.core import BuildSpec, load_spec

app = typer.Typer(help="An apache pulsar runtime.")

@app.command("build", help="Build an apache pulsar runtime.")
def build(
        spec_file: Optional[Path] = typer.Option("configs/build.yaml", "--spec", "--s",
                                                 help="Path to build specification file."),
        image_name: Optional[str] = typer.Option("apache-pulsar", "--image-name", "--n",
                                                 help="Name of new apache pulsar runtime image."),
        image_tag: Optional[str] = typer.Option("", "--image-tag", "--t",
                                                help="Optional. Tag of new apache pulsar runtime image"),
        cache_prefix: Optional[str] = typer.Option("", "--cache-prefix", "--c",
                                                   help="Optional. Custom prefix for generated images acting as cache layers.")
):
    """
    Build Apache Pulsar runtime image.

    :param cache_prefix:
    :param spec_file:
    :param image_name:
    :param image_tag:
    :return:
    """
    config = load_spec(spec_file, BuildSpec)

    builder = RuntimeBuilder(config, cache_prefix, image_name, image_tag)

    builder.build()


@app.command("delete-cache", help="Delete cache images used to build apache pulsar runtime image.")
def delete_cache(
        spec_file: Optional[Path] = typer.Option("configs/build.yaml", "--spec", "--s",
                                                 help="Path to build specification file."),
        cache_prefix: Optional[str] = typer.Option("", "--cache-prefix", "--c",
                                                   help="Optional. Custom prefix for generated images acting as cache layers.")
):
    """
    Delete cache images used to build Apache Pulsar runtime.

    :param spec_file: Path to build spec file.
    :param cache_prefix: Custom prefix for cache layers generated.

    :return:
    """
    config = load_spec(spec_file, BuildSpec)

    builder = RuntimeBuilder(config, cache_prefix)

    builder.prune_cache_images()
