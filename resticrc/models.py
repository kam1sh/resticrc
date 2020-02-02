import logging
import subprocess
from typing import List, Optional

from attr import attrs, attrib

from .filtering.api import process_filters, ExclusionSettings
from .runner import Runner

log = logging.getLogger(__name__)


@attrs
class Repository:
    name: str = attrib()
    path: str = attrib()
    password_file: str = attrib(default=None)

    def get_args(self):
        args = ["--repo", self.path]
        if self.password_file:
            args.extend(["--password-file", self.password_file])
        return args

    def cleanup(self, keep_daily=None, prune=None, dry_run=False):
        args = ["restic"] + self.get_args()
        command = " ".join(args)
        executor = print if dry_run else lambda x: subprocess.check_call(x.split())
        if keep_daily:
            executor(f"{command} forget --keep-daily {keep_daily}")
        if prune:
            executor(f"{command} prune")


@attrs
class Job:
    repo: Repository = attrib()
    tags: Optional[List[str]] = attrib()
    runner: Runner = attrib()
    _exclude: dict = attrib(factory=dict)

    @property
    def exclude(self) -> ExclusionSettings:
        return process_filters(self._exclude)

    def run(self, dry_run=False, conf=None):
        self.runner(self, dry_run=dry_run)
