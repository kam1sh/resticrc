from resticrc.parser import Parser
from resticrc.models import Repository


class LazyParser(Parser):
    def __init__(self, conf):
        super().__init__(conf, read=False)


def test_repos_parser():
    conf = dict(
        repos=dict(test="/backups/host", db="/backups/db")
    )
    parser = LazyParser(conf)
    repos = parser.parse_repos()
    assert len(repos) == 2
    assert isinstance(repos["test"], Repository)
    assert repos["test"] == Repository(name="test", path="/backups/host")


def test_job_parser():
    parser = LazyParser(
        dict(jobs={"testjob": {"repo": "testrepo", "paths": ["/var/lib/test"]}})
    )
    parser.repos = {"testrepo": Repository(name="testrepo", path="/backups/test")}
    parser.global_settings = {}
    jobs = parser.parse_jobs()
    assert len(jobs) == 1
    job = jobs[0]
    assert isinstance(job.repo, Repository)

def test_parser_full():
    conf = {
        "repos": {"host": "/backups/host"},
        "global": {
            "repo": "host",
            "ignore": {
                "log": True,
                "caches": True,
                "paths": [
                    ".bash_history"
                ]
            }
        },
        "jobs": {
            "gitlab": ["/var/lib/gitlab", "/home/git"],
            "etc": "/etc",
            "postgresql": ""
        }
    }
