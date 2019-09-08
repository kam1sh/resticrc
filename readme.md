# Overview
Resticrc is a configuration interface to a restic backup tool.
Basically, it converts YAML file to a restic command line arguments,
but resticrc does it really well and in some cases it can completely replace shell scripts.

Just look at the example configuration:
```yaml
# ~/.config/resticrc
repos: 
  host: /backups/host
  db: /backups/db

global:
  ignore:
    log: true # *.log
    caches: true # .cache, *Cache*, *cache*

jobs:
  gitea:
    paths:
      - /var/lib/gitea
      - /home/git
  etc: /etc
  data:
    path: /alive/protected
    ignore: vms
  postgresql:
    repo: db
    cmd: sudo -u postgres pg_dumpall
  home:
    path: /home
    ignore:
      dev-caches: true # includes python, npm, java, golang, rust, qt and .PyCharm*
      # python: true # .pyenv, __pycache__, venv, .venv, .virtualenvs
      # npm: true # node_modules .npm/_cacache
      # java: true # .m2
      # golang: true # ~/go
      # rust: true # .rustup .cargo
      # qt: true # .local/Qt
      trash: true # .local/share/Trash
      telegram: true # .local/share/TelegramDesktop
      paths:
        - ~/share
    keep:
      paths: .virtualenvs
```
It's beautiful, isn't it?

No?

Then look at the Python syntax!
```python
from resticrc.models import Repository, Job, Action
from resticrc import main

repo = Repository(name="host", path="/backups/host")
db = Repository("db", path="/backups/db")

jobs = [
    Job(
        repo=repo, tag="gitea", action=Action(backup=["/var/lib/gitea", "/home/git"])
    )
]

main(repos=[repo, db], jobs=jobs)

```