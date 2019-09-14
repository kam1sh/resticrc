import subprocess
from typing import List, Optional, Union

from attr import attrs, attrib


@attrs
class FileRunner:
    paths: List[str] = attrib()

    def __call__(self, args: List[str], dry_run=False):
        args.extend(self.paths)
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

    def __call__(self, args: List[str], dry_run=False):
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

    def run(self, executable="restic", dry_run=False):
        from .runner import get_args

        args = get_args(self, executable=executable)
        self.runner(args, dry_run=dry_run)
