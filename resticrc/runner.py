from abc import ABC, abstractmethod
import glob
import logging
import subprocess
from typing import List, Optional

from attr import attrs, attrib

from .executor import executor

log = logging.getLogger(__name__)


class Runner(ABC):

    @staticmethod
    def from_dict(conf: dict) -> 'Runner':
        paths = conf.pop("paths", None) or conf.pop("path", None)
        log.debug("Path: %s", paths)
        if isinstance(paths, str):
            paths = [paths]
        run_cmd = conf.pop("cmd", None)
        if run_cmd:
            return PipedRunner(target=run_cmd, filename=conf.pop("save-as", None))
        zfs_dataset = conf.pop("zfs-dataset", None)
        if zfs_dataset:
            mountpoint = conf.pop("zfs-mountpoint", None)
            if mountpoint is None:
                raise ValueError("No snapshot mountpoint provided.")
            return ZFSSnapshotRunner(dataset=zfs_dataset, paths=paths or ["."])
        if not paths:
            raise ValueError("No paths provided.")
        return FileRunner(paths)

    @staticmethod
    def get_args(job, executable="restic"):
        command = [executable, "backup"]
        command += job.repo.get_args()
        for tag in job.tags:
            command.extend(["--tag", tag])
        command.extend(job.exclude.as_args())
        return command

    @abstractmethod
    def __call__(self, job):
        """ Perform backup. """

@attrs
class FileRunner(Runner):
    paths: List[str] = attrib()

    def __call__(self, job):
        backup_files(self.paths, job, self.get_args(job))

@attrs
class ZFSSnapshotRunner(Runner):
    dataset: str = attrib()
    mountpoint: str = attrib(default="/mnt")
    paths: List[str] = attrib(default=["."])

    def __call__(self, job):
        snapshot_name = f"{self.dataset}@restic"
        executor.run(["/usr/sbin/zfs", "snapshot", snapshot_name])
        executor.run(["/usr/bin/mount", "-t", "zfs", snapshot_name, self.mountpoint])
        try:
            backup_files(self.paths, job, self.get_args(job), cwd=self.mountpoint)
        finally:
            executor.run(["/usr/bin/umount", self.mountpoint])
            executor.run(["/usr/sbin/zfs", "destroy", snapshot_name])


@attrs
class PipedRunner(Runner):
    target = attrib()
    filename = attrib(default=None)

    def get_options(self):
        out = ["--stdin"]
        if self.filename:
            out.extend(["--stdin-filename", self.filename])
        return out

    def __call__(self, job):
        args = self.get_args(job)
        args = args[:2] + self.get_options() + args[2:]
        if executor.dry_run:
            print(" ".join(args))
            return
        restic_proc = subprocess.Popen(args, stdin=subprocess.PIPE)
        subprocess.check_call(self.target.split(), stdout=restic_proc.stdin)
        restic_proc.stdin.close()
        restic_proc.wait(timeout=5)


def backup_files(paths: list, job, args, cwd=None):
    # expand globs before passing them to restic
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
    executor.run(args, cwd=cwd)


def _exclude_paths(job, paths: set):
    for path in paths.copy():
        for item in job.exclude.exclude:
            if path.startswith(item):
                paths.remove(path)
        for item in job.exclude.iexclude:
            if path.lower().startswith(item.lower()):
                paths.remove(path)
