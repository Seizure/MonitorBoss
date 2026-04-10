import os
import sys
import time
from unittest.mock import patch

import pytest

from pyddc import VCP
from pyddc.vcp_codes import VCPCodes, get_vcp_com


def test_get_vcps(vcp: VCP, hw_results: dict[str, str]) -> None:
    vcps = VCP.get_vcps()
    assert len(vcps) > 0, "No monitors found — VCP.get_vcps() returned an empty list"

    if sys.platform == "win32":
        identifiers = ", ".join(
            f"{i}: hmonitor={v.hmonitor.value}"  # type: ignore[attr-defined]
            for i, v in enumerate(vcps)
        )
    else:
        identifiers = ", ".join(f"{i}: bus_number={v.bus_number}" for i, v in enumerate(vcps))

    hw_results["get_vcps"] = f"{len(vcps)} monitor(s): [{identifiers}]"


def test_context_manager(vcp: VCP) -> None:
    with vcp as v:
        pass


def test_get_vcp_capabilities(vcp: VCP, hw_results: dict[str, str]) -> None:
    with vcp as v:
        caps = v.get_vcp_capabilities()

    assert caps, "get_vcp_capabilities() returned an empty string"
    hw_results["get_vcp_capabilities"] = caps


def test_get_vcp_feature(vcp: VCP, hw_results: dict[str, str]) -> None:
    lum_com = get_vcp_com(VCPCodes.image_luminance.value)
    assert lum_com is not None  # always defined in vcp_codes.py

    with vcp as v:
        result = v.get_vcp_feature(lum_com)

    assert result.value >= 0, f"Luminance value is negative: {result.value}"
    assert result.max > 0, f"Luminance max is not positive: {result.max}"
    hw_results["get_vcp_feature"] = f"value={result.value}, max={result.max}"


def test_get_vcp_feature_max(vcp: VCP, hw_results: dict[str, str]) -> None:
    lum_com = get_vcp_com(VCPCodes.image_luminance.value)
    assert lum_com is not None  # always defined in vcp_codes.py

    # Precondition: test_get_vcp_feature must have run first to populate the cache.
    assert VCPCodes.image_luminance in vcp.code_maximum, (
        "Precondition failed: luminance max not in cache. "
        "Did test_get_vcp_feature run first?"
    )

    sentinel = AssertionError(
        "_get_vcp_feature was called unexpectedly — result should have been served from cache"
    )
    with patch.object(vcp, "_get_vcp_feature", side_effect=sentinel):
        with vcp as v:
            max_val = v.get_vcp_feature_max(lum_com)

    assert isinstance(max_val, int)
    assert max_val > 0
    assert max_val == vcp.code_maximum[VCPCodes.image_luminance]
    hw_results["get_vcp_feature_max"] = f"{max_val} (served from cache)"


def test_get_edid_blob(vcp: VCP, hw_results: dict[str, str]) -> None:
    with vcp as v:
        blob = v.get_edid_blob()

    assert isinstance(blob, bytes), f"Expected bytes, got {type(blob)}"
    assert len(blob) > 0, "EDID blob is empty"
    assert len(blob) % 128 == 0, (
        f"EDID blob length {len(blob)} is not a positive multiple of 128"
    )
    hw_results["get_edid_blob"] = f"{len(blob)} bytes"


def test_set_vcp_feature(vcp: VCP, hw_results: dict[str, str]) -> None:
    if os.environ.get("PYDDC_TEST_ALLOW_WRITE", "").casefold() != "true":
        hw_results["set_vcp_feature"] = "(skipped)"
        pytest.skip("PYDDC_TEST_ALLOW_WRITE not set")

    lum_com = get_vcp_com(VCPCodes.image_luminance.value)
    assert lum_com is not None  # always defined in vcp_codes.py

    with vcp as v:
        original = v.get_vcp_feature(lum_com)

    current = original.value
    max_val = original.max

    # Choose a test value distinct from the current value.
    test_value = max_val // 2
    if test_value == current:
        test_value = current + 1 if current < max_val else current - 1

    try:
        with vcp as v:
            v.set_vcp_feature(lum_com, test_value)

        time.sleep(0.5) # we need to do this or else we will get IO/OS errors, per DDC/CI specs on delays between commands

        with vcp as v:
            after = v.get_vcp_feature(lum_com)

        time.sleep(0.2) # this is probably overly cautious but that's fine, and makes the tangible results more obvious

        assert after.value == test_value, (
            f"Expected luminance {test_value} after set, got {after.value}"
        )
    finally:
        with vcp as v:
            v.set_vcp_feature(lum_com, current)

    hw_results["set_vcp_feature"] = f"original={current}, test={test_value}, restored={current}"


