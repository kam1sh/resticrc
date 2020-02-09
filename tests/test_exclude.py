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
    assert len(result.render().split("\n")) == 16


def test_as_args():
    config = {"caches": True, "java": True}
    result = process_filters(config)
    result.add_results()
    args = result.as_args()
    assert len(args) == 18
    args = " ".join(args)
    assert "--exclude .m2" in args
    assert "--exclude .cache" in args
    assert "--exclude .config/*/Cache"
    assert "--exclude .config/*/GPUCache"
    assert "--exclude .config/*/CachedData"
