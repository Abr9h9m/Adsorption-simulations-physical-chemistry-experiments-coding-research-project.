import os

import pytest

from phslope.common import resolve_data_file


@pytest.fixture(scope="session")
def real_file():
    path = resolve_data_file()
    if not os.path.exists(path):
        pytest.skip(f"real data file not found: {path}")
    return path
