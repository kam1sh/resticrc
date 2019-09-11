import subprocess
from typing import List, Optional, Union

from attr import attrs, attrib


@attrs
class BackupRunner:
    paths: List[str] = attrib()

    def __call__(self, args: List[str]):
        args.extend(self.paths)
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

    def __call__(self, args):
        args = args[0] + self.get_options() + args[1:]
        restic_proc = subprocess.Popen(args, stdin=subprocess.PIPE)
        subprocess.check_call(self.target.split(), stdout=restic_proc.stdin)
        restic_proc.stdin.close()


@attrs
class Repository:
    name: str = attrib()
    path: str = attrib()
    password_file: str = attrib(default=None)


@attrs
class Job:
    repo: Repository = attrib()
    tag: Optional[str] = attrib()
    exclude: Optional[dict] = attrib(default=None)
    runner = attrib(default=None)

    def run(self, executable="restic", params=None):
        from .runner import get_args

        args = get_args(self, executable=executable)
        self.runner(args)
