from abc import ABC, abstractmethod
import glob
import logging
import subprocess
from typing import List, Optional

from attr import attrs, attrib


log = logging.getLogger(__name__)

def get_runner(conf: dict):
    paths = conf.pop("paths", None) or conf.pop("path", None)
    log.debug("Path: %s", paths)
    if isinstance(paths, str):
        paths = [paths]
    paths = None if paths == [] else paths
    run_cmd = conf.pop("cmd", None)
    if run_cmd:
        return PipedRunner(target=run_cmd, filename=conf.pop("save-as", None))
    return FileRunner(paths)

class Runner(ABC):

    @staticmethod
    def from_dict(conf: dict) -> 'Runner':
        return get_runner(conf)

    @staticmethod
    def get_args(job, executable="restic"):
        command = [executable, "backup"]
        command += job.repo.get_args()
        for tag in job.tags:
            command.extend(["--tag", tag])
        command.extend(job.exclude.as_args())
        return command

    @abstractmethod
    def __call__(self, job, dry_run=False):
        """ Perform backup. """

@attrs
class FileRunner(Runner):
    paths: List[str] = attrib()

    def __call__(self, job, dry_run=False):
        backup_files(self.paths, job, self.get_args(job), dry_run)


@attrs
class PipedRunner(Runner):
    target = attrib()
    filename = attrib(default=None)

    def get_options(self):
        out = ["--stdin"]
        if self.filename:
            out.extend(["--stdin-filename", self.filename])
        return out

    def __call__(self, job, dry_run=False):
        args = self.get_args(job)
        args = args[:2] + self.get_options() + args[2:]
        if dry_run:
            print(" ".join(args))
            return
        restic_proc = subprocess.Popen(args, stdin=subprocess.PIPE)
        subprocess.check_call(self.target.split(), stdout=restic_proc.stdin)
        restic_proc.stdin.close()
        restic_proc.wait(timeout=5)


def backup_files(paths: list, job, args, dry_run=False):
    # expand globs before passing them to restic
    if not paths:
        raise ValueError("No paths provided.")
    raw_paths = paths
    paths = []
    for item in raw_paths:
        result = glob.glob(item)
        if not result:
            log.warning("Failed to unglob %s - possible permission denied?", item)
            result = [item]
        paths.extend(result)
    paths = set(paths)
    if not paths:
        raise ValueError("No paths left after glob expanding.")
    log.debug("Paths before exclude %s", paths)
    _exclude_paths(job, paths)
    log.debug("After exclude: %s", paths)
    if not paths:
        raise ValueError("No paths left after exclude.")
    args.extend(paths)
    if dry_run:
        print(" ".join(args))
    else:
        subprocess.check_call(args)


def _exclude_paths(job, paths: set):
    for path in paths.copy():
        for item in job.exclude.exclude:
            if path.startswith(item):
                paths.remove(path)
        for item in job.exclude.iexclude:
            if path.lower().startswith(item.lower()):
                paths.remove(path)
