import glob
import subprocess

from resticrc.models import Job, Repository
from resticrc.runner import FileRunner, PipedRunner


def test_simple_job(mocker):
    mocker.patch.object(subprocess, "check_call")
    job = Job(
        repo=Repository("host", path="/backups/host"),
        tags=["home"],
        runner=FileRunner(paths=["/home"]),
        exclude={"logs": True, "paths": ["/home/user/share"]},
    )
    mocker.patch.object(glob, "glob")
    glob.glob.return_value = ["/home"]
    job.run()
    cmd_args = subprocess.check_call.call_args[0][0]
    command = " ".join(cmd_args)
    assert len(cmd_args) == 11
    assert "restic backup --repo /backups/host --tag home" in command
    assert "--exclude *.log" in command
    assert "--exclude /home/user/share" in command
    assert command.endswith("/home")


def test_glob_empty(mocker):
    mocker.patch.object(subprocess, "check_call")
    mocker.patch.object(glob, "glob", return_value=[])
    job = Job(
        repo=Repository("test", "/backups/test"),
        tags=["test2"],
        runner=FileRunner(paths=["/home/user/data"]),
    )
    job.run()
    args = subprocess.check_call.call_args[0][0]
    assert len(args) == 7


def test_runner_glob_exclude(mocker):
    mocker.patch.object(subprocess, "check_call")
    mocker.patch.object(
        glob, "glob", return_value=["/home/user1/.config", "/home/user2/.config"]
    )
    job = Job(
        repo=Repository("test", "/backups/test"),
        tags=["testtag"],
        runner=FileRunner(paths=["/home/*/.config"]),
        exclude={"paths": ["/home/user2/.config"]},
    )
    run = job.run()
    glob.glob.assert_called_with("/home/*/.config")
    args = subprocess.check_call.call_args[0][0]
    assert len(args) == 9
    command = " ".join(args)
    assert "--exclude /home/user2/.config" in command
    assert command.endswith("/home/user1/.config")


def test_job_cmd(mocker):
    mocker.patch.object(subprocess, "Popen")
    mocker.patch.object(subprocess, "check_call")
    job = Job(
        repo=Repository("host", path="/backups/host"),
        tags=["postgres"],
        runner=PipedRunner(target="pg_dumpall", filename="pgdump.bin"),
    )
    job.run()
    subprocess.Popen.assert_called_with(
        (
            "restic backup --stdin --stdin-filename pgdump.bin --repo /backups/host --tag postgres"
        ).split(),
        stdin=subprocess.PIPE,
    )


def test_dry_run(mocker, capsys):
    mocker.patch.object(subprocess, "Popen")
    mocker.patch.object(subprocess, "check_call")
    job = Job(
        repo=Repository("host", path="/backups/host"),
        tags=["home"],
        runner=FileRunner(paths=["/home"]),
        exclude={"logs": True, "paths": ["/home/user/share"]},
    )
    job.run(dry_run=True)
    assert not subprocess.check_call.called
    assert capsys.readouterr()
