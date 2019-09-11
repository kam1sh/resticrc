import logging

import pytest


@pytest.fixture(scope="session", autouse=True)
def logger():
    logging.getLogger("resticrc").setLevel(logging.DEBUG)
