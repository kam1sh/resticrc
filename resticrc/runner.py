from abc import ABC, abstractmethod
import glob
import logging
import subprocess
from typing import List, TYPE_CHECKING

from attr import attrs, attrib

from .executor import executor

if TYPE_CHECKING:
    from .models import Job

log = logging.getLogger(__name__)


class Runner(ABC):
    @staticmethod
    def from_dict(conf: dict) -> "Runner":
        paths = conf.pop("paths", None) or conf.pop("path", None)
        if isinstance(paths, str):
            paths = [paths]
        log.debug("Paths: %s", paths)
        run_cmd = conf.pop("cmd", None)
        runner = None
        if run_cmd:
            runner = PipedRunner(target=run_cmd, filename=conf.pop("save-as", None))
        zfs_dataset = conf.pop("zfs-dataset", None)
        if zfs_dataset:
            mountpoint = conf.pop("zfs-mountpoint", None)
            if mountpoint is None:
                raise ValueError("No snapshot mountpoint provided.")
            runner = ZFSSnapshotRunner(dataset=zfs_dataset, paths=paths or ["."])
        if runner is None:
            if not paths:
                raise ValueError("No paths provided.")
            runner = FileRunner(paths)
        log.info("Selected runner: %s", runner)
        return runner

    @staticmethod
    def get_args(job, executable="restic"):
        command = [executable, "backup"]
        command += job.repo.get_args()
        for tag in job.tags:
            command.extend(["--tag", tag])
        command.extend(job.exclude.as_args())
        return command

    @abstractmethod
    def __call__(self, job: "Job"):
        """ Perform backup. """


@attrs
class FileRunner(Runner):
    paths: List[str] = attrib()

    def __call__(self, job: "Job"):
        backup_files(self.paths, job, self.get_args(job))


@attrs
class ZFSSnapshotRunner(Runner):
    dataset: str = attrib()
    mountpoint: str = attrib(default="/mnt")
    paths: List[str] = attrib(default=["."])

    def __call__(self, job: "Job"):
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

    def __call__(self, job: "Job"):
        args = self.get_args(job)
        args = args[:2] + self.get_options() + args[2:]
        if executor.dry_run:
            print(" ".join(args))
            return
        restic_proc = subprocess.Popen(args, stdin=subprocess.PIPE)
        subprocess.check_call(self.target.split(), stdout=restic_proc.stdin)
        restic_proc.stdin.close()
        restic_proc.wait()


def backup_files(paths: list, job, args, cwd=None):
    paths = process_paths(paths, job)
    args.extend(paths)
    executor.run(args, cwd=cwd)


def process_paths(paths: list, job: "Job"):
    # expand globs before passing them to restic
    raw_paths = paths
    paths = set(unglob(raw_paths))
    if not paths:
        raise ValueError("No paths left after glob expanding.")
    log.debug("Paths before exclude %s", paths)
    _exclude_paths(job, paths)
    log.debug("After exclude: %s", paths)
    if not paths:
        raise ValueError("No paths left after exclude.")
    return paths


def unglob(paths: list):
    for path in paths:
        result = glob.glob(path)
        if not result:
            log.warning("Failed to unglob %s - possible permission denied?", path)
            result = [path]
        yield from result


def _exclude_paths(job, paths: set):
    settings = job.exclude
    for path in paths.copy():
        for item in settings.exclude:
            if path.startswith(item):
                paths.remove(path)
        for item in settings.iexclude:
            if path.lower().startswith(item.lower()):
                paths.remove(path)
