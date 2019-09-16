import glob
import itertools
import logging
import subprocess
from typing import List, Optional, Union

from attr import attrs, attrib

from .filtering.api import process_filters, ExclusionSettings
from .runner import get_args, backup_files


log = logging.getLogger(__name__)


@attrs
class FileRunner:
    paths: List[str] = attrib()

    def __call__(self, job, args, dry_run=False):
        backup_files(self.paths, job, args, dry_run)

@attrs
class PipedRunner:
    target = attrib()
    filename = attrib(default=None)

    def get_options(self):
        out = ["--stdin"]
        if self.filename:
            out.extend(["--stdin-filename", self.filename])
        return out

    def __call__(self, job, args, dry_run=False):
        args = args[:2] + self.get_options() + args[2:]
        if dry_run:
            print(" ".join(args))
            return
        restic_proc = subprocess.Popen(args, stdin=subprocess.PIPE)
        subprocess.check_call(self.target.split(), stdout=restic_proc.stdin)
        restic_proc.stdin.close()
        restic_proc.wait(timeout=5)


@attrs
class Repository:
    name: str = attrib()
    path: str = attrib()
    password_file: str = attrib(default=None)


@attrs
class Job:
    repo: Repository = attrib()
    tags: Optional[list] = attrib()
    _exclude: Optional[dict] = attrib(factory=dict)
    runner = attrib(default=None)

    @property
    def exclude(self) -> ExclusionSettings:
        settings = process_filters(self._exclude)
        settings.add_results()
        return settings

    def run(self, dry_run=False, conf=None):
        command = get_args(self)
        self.runner(self, args=command, dry_run=dry_run)
