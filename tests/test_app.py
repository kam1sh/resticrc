import subprocess

import click.testing
from resticrc.models import Job, Repository, FileRunner, PipedRunner


def test_simple_job(mocker):
    mocker.patch.object(subprocess, "check_call")
    job = Job(
        repo=Repository("host", path="/backups/host"),
        tag="home",
        runner=FileRunner(paths=["/home"]),
        exclude={"logs": True, "paths": ["/home/user/share"]},
    )
    job.run()
    subprocess.check_call.assert_called_with(
        ("restic backup --repo /backups/host --tag home --exclude *.log"
         " --exclude /home/user/share /home").split()
    )


def test_job_cmd(mocker):
    mocker.patch.object(subprocess, "Popen")
    mocker.patch.object(subprocess, "check_call")
    job = Job(
        repo=Repository("host", path="/backups/host"),
        tag="postgres",
        runner=PipedRunner(target="pg_dumpall", filename="pgdump.bin")
    )
    job.run()
    subprocess.Popen.assert_called_with(
        ("restic backup --stdin --stdin-filename pgdump.bin --repo /backups/host --tag postgres").split(),
        stdin=subprocess.PIPE
    )

def test_dry_run(mocker, capsys):
    mocker.patch.object(subprocess, "Popen")
    mocker.patch.object(subprocess, "check_call")
    job = Job(
        repo=Repository("host", path="/backups/host"),
        tag="home",
        runner=FileRunner(paths=["/home"]),
        exclude={"logs": True, "paths": ["/home/user/share"]},
    )
    job.run(dry_run=True)
    assert not subprocess.check_call.called
    assert capsys.readouterr()
