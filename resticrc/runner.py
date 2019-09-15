import logging
import subprocess
from typing import List, Optional

from attr import attrs, attrib

from .filtering.api import process_filters


@attrs
class Restic:
    repo = attrib()
    exclude: dict = attrib()
    tags: List[str] = attrib()
    executable: str = attrib(default="restic")
    conf: dict = attrib(default=None)
    excludeobj = attrib(default=None)

    @classmethod
    def fromjob(cls, job, conf=None):
        return cls(repo=job.repo, exclude=job.exclude, tags=[job.tag], conf=conf)

    def get_args(self):
        command = [self.executable, "backup"]
        command.extend(["--repo", self.repo.path])
        if self.repo.password_file:
            command.extend(["--password-file", self.repo.password_file])
        for tag in self.tags:
            command.extend(["--tag", tag])
        exclusions = process_filters(self.exclude)
        self.excludeobj = exclusions
        exclusions.add_results()
        command.extend(exclusions.as_args())
        return command

    def cleanup(self):
        if not self.conf:
            return
        self._cleanup(
            keep_daily=self.conf.get("keep-daily"), prune=self.conf.get("prune-after")
        )

    def _cleanup(self, keep_daily: Optional[int], prune: bool):
        command = ["restic"]
        if keep_daily:
            subprocess.check_call(f"restic forget --keep-daily {keep_daily}".split())
        if prune:
            subprocess.check_call(f"restic prune".split())

    def exclude_paths(self, paths: set):
        for path in paths.copy():
            for item in self.excludeobj.exclude:
                if path.startswith(item):
                    paths.remove(path)
            for item in self.excludeobj.iexclude:
                if path.lower().startswith(item.lower()):
                    paths.remove(path)
