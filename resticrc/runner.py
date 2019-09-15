from typing import List, Optional
import subprocess

from .models import Job
from .filtering.api import process_filters


def get_args(job: Job, executable="restic") -> List[str]:
    command = [executable, "backup"]
    # repo
    command.extend(["--repo", job.repo.path])
    if job.repo.password_file:
        command.extend(["--password-file", job.repo.password_file])
    command.extend(["--tag", job.tag])
    # exclude
    exclusions = process_filters(job.exclude).as_args()
    command.extend(exclusions)
    return command

def cleanup(keep_daily: Optional[int], prune: bool):
    command = ["restic"]
    if keep_daily:
        subprocess.check_call(f"restic forget --keep-daily {keep_daily}".split())
    if prune:
        subprocess.check_call(f"restic prune".split())
