import glob
import subprocess

from resticrc.models import Job, Repository
from resticrc.runner import FileRunner, PipedRunner
from resticrc.executor import executor


def test_simple_job(helpers):
    helpers.glob.return_value = ["/home"]
    job = Job(
        repo=Repository("host", path="/backups/host"),
        tags=["home"],
        runner=FileRunner(paths=["/home"]),
        exclude={"logs": True, "paths": ["/home/user/share"]},
    )
    job.run()
    assert helpers.exec.called
    cmd_args = helpers.exec.call_args[0][0]
    command = " ".join(cmd_args)
    assert len(cmd_args) == 11
    assert command.startswith("restic")
    assert "--repo /backups/host" in command
    assert "--tag home" in command
    assert "--exclude *.log" in command
    assert "--exclude /home/user/share" in command
    assert command.endswith("/home")


def test_glob_empty(helpers):
    helpers.glob.return_value = []
    job = Job(
        repo=Repository("test", "/backups/test"),
        tags=["test2"],
        runner=FileRunner(paths=["/home/user/data"]),
    )
    job.run()
    assert helpers.exec.called
    args = helpers.exec.call_args[0][0]
    assert len(args) == 7


def test_runner_glob_exclude(helpers):
    helpers.glob.return_value = ["/home/user1/.config", "/home/user2/.config"]
    job = Job(
        repo=Repository("test", "/backups/test"),
        tags=["testtag"],
        runner=FileRunner(paths=["/home/*/.config"]),
        exclude={"paths": ["/home/user2/.config"]},
    )
    run = job.run()
    glob.glob.assert_called_with("/home/*/.config")
    args = helpers.exec.call_args[0][0]
    assert len(args) == 9
    command = " ".join(args)
    assert "--exclude /home/user2/.config" in command
    assert command.endswith("/home/user1/.config")


def test_job_cmd(helpers):
    job = Job(
        repo=Repository("host", path="/backups/host"),
        tags=["postgres"],
        runner=PipedRunner(target="pg_dumpall", filename="pgdump.bin"),
    )
    job.run()
    helpers.sp_popen.assert_called_with(
        [
            "restic",
            "--repo",
            "/backups/host",
            "backup",
            "--tag",
            "postgres",
            "--stdin",
            "--stdin-filename",
            "pgdump.bin",
        ],
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
    executor.dry_run = True
    job.run()
    assert not subprocess.check_call.called
    assert capsys.readouterr()
