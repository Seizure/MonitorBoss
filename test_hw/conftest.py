import os

import pytest

from pyddc import VCP

hw_results_key = pytest.StashKey[dict[str, str]]()


@pytest.fixture(scope="session")
def hw_results(request: pytest.FixtureRequest) -> dict[str, str]:
    store: dict[str, str] = {}
    request.config.stash[hw_results_key] = store
    return store


@pytest.fixture(scope="session")
def vcp() -> VCP:
    index_str = os.environ.get("PYDDC_TEST_MONITOR_INDEX")
    if index_str is None:
        pytest.skip("PYDDC_TEST_MONITOR_INDEX is not set")

    try:
        index = int(index_str)
    except ValueError:
        pytest.fail(f"PYDDC_TEST_MONITOR_INDEX must be an integer, got: {index_str!r}")

    vcps = VCP.get_vcps()
    if index < 0 or index >= len(vcps):
        pytest.fail(
            f"PYDDC_TEST_MONITOR_INDEX={index} is out of range; found {len(vcps)} monitor(s)"
        )

    return vcps[index]


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    store = config.stash.get(hw_results_key, {})
    terminalreporter.write_sep("=", "Hardware Test Results")
    if not store:
        terminalreporter.write_line(
            "WARNING: No hardware tests were run — PYDDC_TEST_MONITOR_INDEX is not set."
        )
    else:
        for key, value in store.items():
            terminalreporter.write_line(f"{key:<20} : {value}")
    terminalreporter.write_sep("=")

