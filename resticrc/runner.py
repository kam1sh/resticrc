from typing import List
import subprocess

from .models import Job, BackupRunner, PipedRunner
from .filtering.api import process_filters


def get_args(job: Job, executable="restic") -> List[str]:
    command = [executable]
    # repo
    command.extend(["--repo", job.repo.path])
    if job.repo.password_file:
        command.extend(["--password-file", job.repo.password_file])
    command.extend(["--tag", job.tag])
    # exclude
    exclusions = process_filters(job.exclude).as_args()
    command.extend(exclusions)
    return command


def run(job):
    pass
