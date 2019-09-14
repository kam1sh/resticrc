from resticrc.models import Repository, Job, FileRunner, PipedRunner
from resticrc.parser import Parser


class LazyParser(Parser):
    def __init__(self, conf):
        super().__init__(conf, read=False)


def test_repos_parser():
    conf = dict(repos=dict(test="/backups/host", db="/backups/db"))
    parser = LazyParser(conf)
    repos = parser.parse_repos()
    assert len(repos) == 2
    assert isinstance(repos["test"], Repository)
    assert repos["test"] == Repository(name="test", path="/backups/host")


def test_repo_password_file():
    conf = dict(
        repos=dict(host={"path": "/backups/host", "password_file": "/etc/test"})
    )
    parser = LazyParser(conf)
    repos = parser.parse_repos()
    assert repos["host"] == Repository(
        name="host", path="/backups/host", password_file="/etc/test"
    )


def test_job_parser():
    parser = LazyParser(
        dict(jobs={"testjob": {"repo": "testrepo", "paths": ["/var/lib/test"]}})
    )
    parser.repos = {"testrepo": Repository(name="testrepo", path="/backups/test")}
    parser.global_settings = {}
    jobs = parser.parse_jobs()
    assert len(jobs) == 1
    job = jobs["testjob"]
    assert isinstance(job.repo, Repository)


def test_job_cmd():
    jobs = {
        "postgres": {
            "repo": "db",
            "cmd": "sudo -u postgres pg_dumpall",
            "save-as": "pg_dumpall",
        }
    }
    parser = LazyParser(dict(jobs=jobs))
    parser.repos = {"db": Repository(name="db", path="/db")}
    job = parser.parse_jobs()["postgres"]
    assert job.runner.target == "sudo -u postgres pg_dumpall"


def test_parser_full():
    conf = {
        "repos": {"host": "/backups/host"},
        "global": {
            "repo": "host",
            "exclude": {"caches": True, "paths": [".bash_history"]},
        },
        "jobs": {
            "gitlab": ["/var/lib/gitlab", "/home/git"],
            "etc": "/etc",
            "postgresql": {"cmd": "pg_dumpall"},
            "home": {"path": "/home", "exclude": {"logs": True}},
        },
    }
    parser = Parser(conf)
    repo = Repository(name="host", path="/backups/host")
    exclude = {"caches": True, "paths": [".bash_history"]}
    assert parser.jobs
    assert parser.jobs["gitlab"] == Job(
        tag="gitlab",
        repo=repo,
        runner=FileRunner(["/var/lib/gitlab", "/home/git"]),
        exclude=exclude,
    )
    assert parser.jobs["etc"] == Job(
        tag="etc", repo=repo, runner=FileRunner(["/etc"]), exclude=exclude
    )
    assert parser.jobs["postgresql"].runner == PipedRunner(target="pg_dumpall")
    assert parser.jobs["home"].exclude == dict(**exclude, logs=True)
    assert parser.jobs["home"].runner.paths == ["/home"]


def test_exclude_str():
    conf = "/home/*/.local/lib"
    parser = LazyParser({})
    result = parser.parse_exclude(conf)
    assert result["paths"] == [conf]

def test_exclude_list():
    conf = ["/home/*/.local/lib"]
    parser = LazyParser({})
    result = parser.parse_exclude(conf)
    assert result["paths"] == conf

