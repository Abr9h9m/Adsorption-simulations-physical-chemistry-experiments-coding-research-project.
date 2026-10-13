import pytest

from phslope.experiments.integrate import CONFIRM, run_locked


def test_locked_evaluation_refuses_without_exact_phrase():
    with pytest.raises(SystemExit):
        run_locked("yes")
    with pytest.raises(SystemExit):
        run_locked(CONFIRM.lower())
