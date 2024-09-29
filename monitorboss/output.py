import json
import textwrap
from logging import getLogger, DEBUG

from monitorboss import indentation
from monitorboss.info import CapabilityData, FeatureData, ValueData, MonitorData
from pyddc.vcp_codes import VCPCodes

_log = getLogger(__name__)
_INDENT_LEVEL = 4 if _log.level >= DEBUG else None


def list_mons_output(mons: list[MonitorData], json_output: bool) -> str:
    if json_output:
        monlist = []
        for mon in mons:
            monlist.append({"monitor": mon.serialize()})
        return json.dumps({"list": monlist})

    return "\n".join(map(str, mons))


def get_feature_output(feature: FeatureData, monvalues: list[tuple[MonitorData, ValueData, int | None]], json_output) -> str:
    if json_output:
        monvalue_list = []
        for mon, value, maximum in monvalues:
            item = {"monitor": mon.serialize(), "value": value.serialize()}
            if maximum:
                item["max_value"] = maximum
            monvalue_list.append(item)
        return json.dumps({"get": {"feature": feature.serialize(), "values": monvalue_list}})

    return "\n".join(map(str, [f"{feature} for {mon} is {value}" + (f" (Maximum: {maximum})" if maximum else "") for mon, value, maximum in monvalues]))


def caps_raw_output(mon: MonitorData, caps: str, json_output: bool) -> str:
    if json_output:
        return json.dumps({"caps": {"type": "raw", "monitor": mon.serialize(), "data": caps}}, indent=_INDENT_LEVEL)

    return f"Capability string for {mon}:\n{caps}"


def caps_full_output(mon: MonitorData, caps: CapabilityData, json_output: bool) -> str:
    if json_output:
        return json.dumps({"caps": {"type": "full", "monitor": mon.serialize(), "data": caps.serialize()}}, indent=_INDENT_LEVEL)

    return str(mon) + ":\n" + textwrap.indent(str(caps), indentation)


def extract_caps_summary_data(caps_data: CapabilityData) -> tuple[dict[str, str], dict[str, dict[FeatureData, tuple[ValueData, ...]]]]:
    desired_attributes = {"type", "model"}
    attributes = {attr: value for attr, value in caps_data.attributes.items() if attr in desired_attributes}
    desired_features = {VCPCodes.input_source.value, VCPCodes.image_color_preset.value}
    vcp_features = {
        vcp: {feature: params for feature, params in features.items() if feature.code in desired_features}
        for vcp, features in caps_data.vcps.items() if features
    }
    return attributes, vcp_features


def caps_summary_output(mon: MonitorData, caps_data: CapabilityData, json_output: bool) -> str:
    attributes, vcp_features = extract_caps_summary_data(caps_data)

    if json_output:
        vcps = {
            vcp: [
                {
                    "feature": feature.serialize(),
                    "params": [param.serialize() for param in params],
                }
                for feature, params in features.items()
            ]
            for vcp, features in vcp_features.items()
        }
        return json.dumps({
            "caps": {"type": "summary", "monitor": mon.serialize(), "data": {**attributes, "vcps": vcps}}
        }, indent=_INDENT_LEVEL)

    summary = f"{mon}"
    attr_str = ", ".join(f"{attr}: {value}" for attr, value in attributes.items())
    summary += f" - {attr_str}\n" if attr_str else "\n"
    for vcp, features in vcp_features.items():
        summary += vcp + (":" if features else "") + "\n"
        for feature, params in features.items():
            summary += f"{indentation}* {feature}: {', '.join(map(str, params))}\n"
    return summary
