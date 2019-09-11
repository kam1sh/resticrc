from resticrc.models import Job, Repository, BackupRunner, PipedRunner
import subprocess


def test_simple_job(mocker):
    mocker.patch.object(subprocess, "check_call")
    job = Job(
        repo=Repository("host", path="/backups/host"),
        tag="home",
        runner=BackupRunner(paths=["/home"]),
        exclude={"logs": True, "paths": "/home/user/share"},
    )
    job.run()
    subprocess.check_call.assert_called_with(
        "restic --repo /backups/host --tag home --exclude *.log /home".split()
    )


def test_job(mocker):
    mocker.patch.object(subprocess, "Popen")
