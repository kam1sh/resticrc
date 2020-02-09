from abc import ABC, abstractmethod
import glob
import logging
import subprocess
from typing import List, TYPE_CHECKING

from attr import attrs, attrib

from .executor import executor
from .commands import Restic

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
        return runner

    @abstractmethod
    def __call__(self, job: "Job"):
        """ Perform backup. """


@attrs
class FileRunner(Runner):
    paths: List[str] = attrib()

    def __call__(self, job: "Job"):
        restic = Restic(job, self)
        restic.backup_files(self.paths)


@attrs
class ZFSSnapshotRunner(Runner):
    dataset: str = attrib()
    mountpoint: str = attrib(default="/mnt")
    paths: List[str] = attrib(default=["."])

    def __call__(self, job: "Job"):
        snapshot_name = f"{self.dataset}@restic"
        executor.run(["zfs", "snapshot", snapshot_name])
        executor.run(["mount", "-t", "zfs", snapshot_name, self.mountpoint])
        try:
            restic = Restic(job, self)
            restic.backup_files(paths=self.paths, cwd=self.mountpoint)
        finally:
            executor.run(["umount", self.mountpoint])
            executor.run(["zfs", "destroy", snapshot_name])


@attrs
class PipedRunner(Runner):
    target = attrib()
    filename = attrib(default=None)

    def __call__(self, job: "Job"):
        restic = Restic(job, self)
        restic_proc = restic.backup_stdin(filename=self.filename)
        if executor.dry_run:
            return
        subprocess.check_call(self.target.split(), stdout=restic_proc.stdin)
        restic_proc.stdin.close()
        restic_proc.wait()
