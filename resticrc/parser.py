import logging
import typing as ty
from pathlib import Path

try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader
import yaml

from .models import Repository, Job
from .runner import Runner


log = logging.getLogger(__name__)


class Parser:
    """ Configuration parser. """

    def __init__(self, conf, read=True):
        self.conf = self.try_load(conf)
        self.global_settings: ty.Dict[str, ty.Any] = {}
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
            passwd = repo.get("password-file")
            out[name] = Repository(name=name, path=repo["path"], password_file=passwd)
        return out

    def parse_jobs(self) -> dict:
        return {
            name: self.parse_job(name, x)
            for name, x in self.conf.get("jobs", {}).items()
        }

    def parse_job(self, name, conf):
        log.debug("Processing job %s", name)
        conf = self.parse_paths(conf)
        for k, v in self.global_settings.items():
            if k == "exclude":
                conf[k] = self.parse_exclude(conf.get("exclude", {}))
            else:
                conf.setdefault(k, v)
        repo_name = conf["repo"]
        repo = self.repos[repo_name]
        try:
            runner = Runner.from_dict(conf)
        except Exception as e:
            raise ValueError(f"[job {name!r}] {e}")
        return Job(repo=repo, tags=[conf.get("tag", name)], runner=runner, conf=conf)

    def parse_paths(self, conf) -> dict:
        """ Parses paths section of job, returns config. """
        if isinstance(conf, str):
            conf = dict(paths=[conf])
        elif isinstance(conf, list):
            conf = {"paths": conf}
        paths = conf.pop("path", None)
        if isinstance(paths, str):
            paths = [paths]
        conf.setdefault("paths", paths)
        return conf

    def parse_exclude(self, exclude):
        if isinstance(exclude, str):
            exclude = {"paths": [exclude]}
        elif isinstance(exclude, list):
            exclude = {"paths": exclude}
        self.merge_exclusions(exclude)
        return exclude

    def merge_exclusions(self, jobexclude: dict):
        """ Merges global and job dictionaries. """
        for key, val in self.global_settings.get("exclude", {}).items():
            if isinstance(val, list):
                val = jobexclude.get(key, []) + val
            jobexclude.setdefault(key, val)

    def cleanup(self, dry_run=False):
        for repo in self.repos.values():
            repo.cleanup(
                keep_daily=self.conf.get("keep-daily"),
                prune=self.conf.get("prune-after"),
            )

def getlist(value) -> list:
    if isinstance(value, str):
        return [value]
    if hasattr(value, "__iter__"):
        return list(value)
    raise ValueError(f"Failed to convert {value} to list.")
