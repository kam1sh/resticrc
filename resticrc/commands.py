import glob
import logging
import subprocess
import typing as ty

from .executor import executor

if ty.TYPE_CHECKING:
    from .models import Job

log = logging.getLogger(__name__)


class Command:
    def __init__(self, job: "Job", runner):
        self.job = job
        self.runner = runner


class Restic(Command):
    def base_args(self):
        cmd = ["restic"] + self.job.repo.get_args() + ["backup"]
        for tag in self.job.tags:
            cmd.extend(["--tag", tag])
        return cmd

    def backup_files(self, paths, cwd=None):
        args = self.base_args()
        paths = process_paths(paths, self.job)
        args.extend(self.job.exclude.as_args())
        args.extend(paths)
        executor.run(args, cwd=cwd)

    def backup_stdin(self, filename=None):
        args = self.base_args() + ["--stdin"]
        if filename:
            args.extend(["--stdin-filename", filename])
        if executor.dry_run:
            print("Executing:", args)
            return
        return subprocess.Popen(args, stdin=subprocess.PIPE)

    def backup_zstd(self, paths, filename="/archive.tar.zst", cwd=None):
        restic_proc = self.backup_stdin(filename)
        tar_args = ["tar", "-c", "-I", "zstd -T4"]
        if cwd:
            tar_args.extend(["-C", cwd])
        for item in self.job.exclude.exclude:
            tar_args.extend(["--exclude", item])
        tar_args.extend(paths)
        if executor.dry_run:
            return print("Executing:", tar_args)
        tar_proc = subprocess.Popen(tar_args, stdout=restic_proc.stdin)

def process_paths(paths: ty.Iterable[str], job: "Job"):
    # expand globs
    paths = set(unglob(paths))
    if not paths:
        raise ValueError("No paths left after glob expanding.")
    log.debug("Paths before exclude %s", paths)
    exclude_paths(job, paths)
    log.debug("After exclude: %s", paths)
    if not paths:
        raise ValueError("No paths left after exclude.")
    return paths


def unglob(paths: ty.Iterable[str]) -> ty.Iterable[str]:
    for path in paths:
        result = glob.glob(path)
        if not result:
            log.warning("Failed to unglob %s - possible permission denied?", path)
            result = [path]
        yield from result


def exclude_paths(job, paths: set):
    settings = job.exclude
    for path in paths.copy():
        for item in settings.exclude:
            if path.startswith(item):
                paths.remove(path)
        for item in settings.iexclude:
            if path.lower().startswith(item.lower()):
                paths.remove(path)
