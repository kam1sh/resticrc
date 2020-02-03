import logging
import glob
import subprocess

import pytest

from resticrc.executor import executor


@pytest.fixture(scope="session", autouse=True)
def logger():
    logging.getLogger("resticrc").setLevel(logging.DEBUG)


class Helpers:
    def __init__(self, mocker):
        self.mocker = mocker
        self.exec = mocker.patch.object(executor, "run")
        self.sp_call = mocker.patch.object(subprocess, "check_call")
        self.sp_popen = mocker.patch("subprocess.Popen")
        self.glob = mocker.patch.object(glob, "glob")


@pytest.fixture
def helpers(mocker):
    return Helpers(mocker=mocker)
