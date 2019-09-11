import logging
import typing as ty
from pathlib import Path

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader
import yaml

from .models import Repository, Job, BackupRunner, PipedRunner


log = logging.getLogger(__name__)


class Parser:
    """ Configuration parser. """

    def __init__(self, conf, read=True):
        self.conf = self.try_load(conf)
        self.global_settings = {}
        self.repos: ty.Optional[ty.Dict[str, Repository]] = None
        self.jobs: ty.Optional[ty.Dict[str, Job]] = None
        if read:
            self.read()

    def try_load(self, conf) -> dict:
        """ Tries to load conf object, if it's string or path-like object. """
        if isinstance(conf, dict):
            return conf
        pth = Path(conf)
        if not pth.exists():
            raise ValueError(f"Path {pth} does not exist.")
        with open(pth) as fd:
            return yaml.load(fd, Loader=Loader)

    def read(self):
        """ Reads configuration settings (global, repos, etc). """
        self.global_settings = self.conf.get("global", {})
        # dictionary for access to repos from parse_jobs()
        self.repos = self.parse_repos()
        self.jobs = self.parse_jobs()

    def parse_repos(self):
        value = self.conf.get("repos")
        if not value:
            raise ValueError(
                "Please define at lease one repository in mapping 'repos'."
            )
        out = {}
        for name, repo in value.items():
            if isinstance(repo, str):
                repo = {"path": repo}
            passwd = repo.get("password_file")
            out[name] = Repository(name=name, path=repo["path"], password_file=passwd)
        return out

    def parse_jobs(self) -> dict:
        return {
            name: self.parse_job(name, x)
            for name, x in self.conf.get("jobs", {}).items()
        }

    def parse_job(self, name, conf):
        log.debug("Processing job %s", name)
        if isinstance(conf, str):
            conf = dict(paths=[conf])
        elif isinstance(conf, list):
            conf = {"paths": conf}
        for k, v in self.global_settings.items():
            if k == "exclude":
                exclude = conf.get("exclude", {})
                self.merge_exclusions(exclude)
                conf["exclude"] = exclude
            else:
                conf.setdefault(k, v)
        # action = Action(backup=paths, command=conf.pop("cmd", None))
        repo_name = conf["repo"]
        conf["repo"] = self.repos[repo_name]
        runner = get_runner(conf)
        return Job(tag=conf.get("tag", name), runner=runner, **conf)

    def merge_exclusions(self, jobexclude: dict):
        """ Merges global and job dictionaries. """
        for key, val in self.global_settings.get("exclude", {}).items():
            if isinstance(val, list):
                val = jobexclude.get(key, []) + val
            jobexclude.setdefault(key, val)


def get_runner(conf: dict):
    paths = conf.pop("paths", None) or conf.pop("path", None)
    log.debug("Path: %s", paths)
    if isinstance(paths, str):
        paths = [paths]
    paths = None if paths == [] else paths
    run_cmd = conf.pop("cmd", None)
    if run_cmd:
        return PipedRunner(target=run_cmd, filename=conf.pop("save-as", None))
    return BackupRunner(paths)


def getlist(value) -> list:
    if isinstance(value, str):
        return [value]
    if hasattr(value, "__iter__"):
        return list(value)
    raise ValueError(f"Failed to convert {value} to list.")
