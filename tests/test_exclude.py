import logging
from pathlib import Path

import pytest
from resticrc.filtering import process_filters


@pytest.fixture(scope="session", autouse=True)
def debuglog():
    logging.getLogger("resticrc").setLevel(logging.DEBUG)


def test_ignore_simple():
    config = dict(logs=True, caches=True)
    result = process_filters(config)
    assert len(result.pluginmap) >= 2
    assert result.pluginmap["caches"][0] == ".cache"
    assert result.pluginmap["logs"] == ("*.log",)


def test_ignore_devcaches():
    config = {"dev-caches": True}
    result = process_filters(config)
    assert len(result.pluginmap) >= 6


def test_render_glob():
    config = {"golang": True}
    result = process_filters(config)
    expected = "/home/*/go"
    assert result.render() == expected


def test_ignore_override_defaults():
    config = {"dev-caches": True, "golang": False}
    result = process_filters(config)
    assert result.render() == (
        ".pyenv\n__pycache__\n.venv\n.virtualenvs\n"
        "node_modules\n.npm/_cacache\n.m2\n.rustup\n.cargo\n.local/Qt\n"
        ".PyCharm*\n.vscode/extensions\n"
        ".config/Code/User/workspaceStorage\n.config/Code/Cache\n"
        ".config/Code/GPUCache\n.config/Code/CachedData"
    )


def test_as_args():
    config = {"caches": True, "java": True}
    result = process_filters(config)
    assert (
        result.as_args()
        == (
            "--exclude .m2 --exclude .cache"
            " --exclude .config/*/Cache --exclude .config/*/GPUCache --exclude .config/*/CachedData"
        ).split()
    )
