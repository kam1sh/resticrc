import glob
import itertools
import logging
import subprocess
from typing import List, Optional, Union

from attr import attrs, attrib


log = logging.getLogger(__name__)


@attrs
class FileRunner:
    paths: List[str] = attrib()

    def __call__(self, restic, dry_run=False):
        args = restic.get_args()
        # expand globs before passing them to restic
        paths = [glob.glob(x) for x in self.paths]
        paths = set(itertools.chain(*paths))
        log.debug("Paths before exclude %s", paths)
        # if restic.job.exclude
        restic.exclude_paths(paths)
        log.debug("After exclude: %s", paths)
        args.extend(paths)
        if dry_run:
            print(" ".join(args))
            return
        subprocess.check_call(args)


@attrs
class PipedRunner:
    target = attrib()
    filename = attrib(default=None)

    def get_options(self):
        out = ["--stdin"]
        if self.filename:
            out.extend(["--stdin-filename", self.filename])
        return out

    def __call__(self, restic, dry_run=False):
        args = restic.get_args()
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
    tag: Optional[str] = attrib()
    exclude: Optional[dict] = attrib(factory=dict)
    runner = attrib(default=None)

    def get_restic(self, conf=None):
        from .runner import Restic

        return Restic.fromjob(job=self, conf=conf)

    def run(self, dry_run=False, conf=None, cleanup=True):
        restic = self.get_restic(conf=conf)
        self.runner(restic, dry_run=dry_run)
        if cleanup:
            restic.cleanup()
        return restic
