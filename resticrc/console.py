import logging
from pathlib import Path

import click

from . import __version__
from .parser import Parser

levels = [logging.WARNING, logging.INFO, logging.DEBUG]


@click.command()
@click.version_option(__version__, prog_name="resticrc")
@click.option("-v", "--verbose", count=True)
@click.option("-c", "--config", default=Path.home().joinpath(".config", "resticrc"))
@click.argument("jobname")
def cli(verbose, config, jobname):
    level = levels[min(verbose, 2)]
    logging.basicConfig(level=level)
    logging.getLogger("resticrc").setLevel(level)
    parser = Parser(config)
    job = parser.jobs[jobname]
    job.run()
