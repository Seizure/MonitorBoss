import json
import textwrap
from logging import getLogger, DEBUG

from monitorboss import indentation
from monitorboss.info import (
    FeatureData,
    MonitorGetResponseData,
    MonitorSetResponseData,
    MonitorToggleResponseData,
    MonitorCapsResponseData,
    MonitorData,
)

_log = getLogger(__name__)
_INDENT_LEVEL = 4 if _log.level >= DEBUG else None


def list_mons_output(mons: list[MonitorData], json_output: bool) -> str:
    if json_output:
        monlist = []
        for mon in mons:
            monlist.append({"monitor": mon.serialize()})
        return json.dumps({"list": monlist}, indent=_INDENT_LEVEL)

    return "\n".join(map(str, mons))


def get_feature_output(
    feature: FeatureData,
    responses: list[MonitorGetResponseData],
    json_output: bool
) -> str:
    if json_output:
        response_list = [resp.serialize() for resp in responses]
        return json.dumps(
            {"get": {"feature": feature.serialize(), "responses": response_list}},
            indent=_INDENT_LEVEL
        )

    header = f"Getting {feature}:"
    response_lines = [f"{indentation}{resp}" for resp in responses]
    return header + "\n" + "\n".join(response_lines)


def set_feature_output(
    feature: FeatureData,
    responses: list[MonitorSetResponseData],
    json_output: bool
) -> str:
    if json_output:
        response_list = [resp.serialize() for resp in responses]
        return json.dumps(
            {"set": {"feature": feature.serialize(), "responses": response_list}},
            indent=_INDENT_LEVEL
        )

    header = f"Setting {feature}:"
    response_lines = [f"{indentation}{resp}" for resp in responses]
    return header + "\n" + "\n".join(response_lines)


def tog_feature_output(
    feature: FeatureData,
    responses: list[MonitorToggleResponseData],
    json_output: bool
) -> str:
    if json_output:
        response_list = [resp.serialize() for resp in responses]
        return json.dumps(
            {"toggle": {"feature": feature.serialize(), "responses": response_list}},
            indent=_INDENT_LEVEL
        )

    header = f"Toggling {feature}:"
    response_lines = [f"{indentation}{resp}" for resp in responses]
    return header + "\n" + "\n".join(response_lines)


def caps_raw_output(
        responses: list[MonitorCapsResponseData],
        json_output: bool) -> str:
    if json_output:
        response_list = [resp.serialize() for resp in responses]
        return json.dumps(
            {"caps": response_list, "type": "raw"},
            indent=_INDENT_LEVEL
        )

    header = "Capabilities:"
    response_lines = [textwrap.indent(str(resp), indentation) for resp in responses]
    return header + "\n" + "\n".join(response_lines)


def caps_parsed_output(responses: list[MonitorCapsResponseData], json_output: bool) -> str:
    if json_output:
        response_list = [resp.serialize() for resp in responses]
        return json.dumps(
            {"caps": response_list, "type": "parsed"},
            indent=_INDENT_LEVEL
        )

    header = "Capabilities:"
    response_lines = [textwrap.indent(str(resp), indentation) for resp in responses]
    return header + "\n" + "\n".join(response_lines)

