import glob
import logging
import subprocess
from typing import List, Optional

from attr import attrs, attrib


log = logging.getLogger(__name__)


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



def get_args(job, executable="restic"):
    command = [executable, "backup"]
    command.extend(["--repo", job.repo.path])
    if job.repo.password_file:
        command.extend(["--password-file", job.repo.password_file])
    for tag in job.tags:
        command.extend(["--tag", tag])
    command.extend(job.exclude.as_args())
    return command


def cleanup(keep_daily: Optional[int], prune: bool, dry_run=False):
    command = ["restic"]
    executor = print if dry_run else lambda x: subprocess.check_call(x.split())
    if keep_daily:
        executor(f"restic forget --keep-daily {keep_daily}")
    if prune:
        executor(f"restic prune")
