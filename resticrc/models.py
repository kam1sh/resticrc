import logging
from typing import List, Optional

from attr import attrs, attrib

from .filtering.api import process_filters, ExclusionSettings
from .runner import Runner
from .executor import executor

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

    def cleanup(self, keep_daily=None, prune=None):
        args = ["restic"] + self.get_args()
        if keep_daily:
            executor.run(args + ["forget", "--group-by", "host,tags", "--keep-daily", str(keep_daily)])
        if prune:
            executor.run(args + ["prune"])


@attrs
class Job:
    repo: Repository = attrib()
    tags: Optional[List[str]] = attrib()
    runner: Runner = attrib()
    _exclude: dict = attrib(factory=dict)
    conf: dict = attrib(factory=dict)

    def __attrs_post_init__(self):
        self._exclude_processed = None

    @property
    def exclude(self) -> ExclusionSettings:
        if self._exclude_processed:
            return self._exclude_processed
        log.debug("Exclude before processing filters: %s", self._exclude)
        val = process_filters(self._exclude)
        log.debug("Exclude after processing filters: %s", val)
        self._exclude_processed = val
        return val

    def run(self):
        self.runner(self)
