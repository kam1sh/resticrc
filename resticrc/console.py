import logging
from pathlib import Path

import click

from . import __version__
from .parser import Parser

levels = [logging.WARNING, logging.INFO, logging.DEBUG]

pass_parser = click.make_pass_decorator(Parser)


@click.group()
@click.version_option(__version__, prog_name="resticrc")
@click.option("-v", "--verbose", count=True)
@click.option("-c", "--config")
@click.pass_context
def cli(ctx, verbose, config):
    level = levels[min(verbose, 2)]
    logging.basicConfig(level=level)
    logging.getLogger("resticrc").setLevel(level)
    if config is None:
        confpath = Path.home().joinpath(".config")
        config = confpath / "resticrc"
        if not config.exists():
            config = confpath / "resticrc.yml"
    ctx.obj = Parser(config)


@cli.command()
@click.option(
    "-n", "--dry-run", is_flag=True, help="Prints restic command instead of running it"
)
@click.argument("jobname")
@pass_parser
def run(parser, jobname, dry_run):
    job = parser.jobs[jobname]
    job.run(dry_run=dry_run, conf=parser.conf)
    parser.cleanup()


@cli.command()
@pass_parser
def all(parser):
    """Execute all jobs"""
    for job in parser.jobs.values():
        job.run(conf=parser.conf)
    parser.cleanup()
