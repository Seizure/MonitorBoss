import json
import textwrap
from logging import getLogger, DEBUG

from monitorboss import indentation
from monitorboss.info import CapabilityData, FeatureData, ValueData, MonitorData

_log = getLogger(__name__)
_INDENT_LEVEL = 4 if _log.level >= DEBUG else None


def list_mons_output(mons: list[MonitorData], json_output: bool) -> str:
    if json_output:
        monlist = []
        for mon in mons:
            monlist.append({"monitor": mon.serialize()})
        return json.dumps({"list": monlist}, indent=_INDENT_LEVEL)

    return "\n".join(map(str, mons))

GetFeatureInputList = list[tuple[MonitorData | None, ValueData | None, int | None, Exception | None]]

def get_feature_output(feature: FeatureData, monvalues: GetFeatureInputList, json_output: bool) -> str:
    if json_output:
        monvalue_list = []
        for mon, value, maximum, e in monvalues:
            item = {}
            if mon:
                item["monitor"] = mon.serialize()
            if value:
                item["value"] = value.serialize()
            if maximum:
                item["max_value"] = maximum
            if e:
                item["error"] = str(e)
            monvalue_list.append(item)
        return json.dumps({"get": {"feature": feature.serialize(), "values": monvalue_list}}, indent=_INDENT_LEVEL)

    return "\n".join(map(str, [f"{feature} for {mon} is {value if not e else 'ERROR: ' + str(e)}" + (f" (Maximum: {maximum})" if maximum else "") for mon, value, maximum, e in monvalues]))

SetFeatureInputList = list[tuple[MonitorData | None, ValueData | None, Exception | None]]

def set_feature_output(feature: FeatureData, monvalues: SetFeatureInputList, json_output: bool) -> str:
    if json_output:
        monvalue_list = []
        for mon, value, e in monvalues:
            item = {}
            if mon:
                item["monitor"] = mon.serialize()
            if value:
                item["value"] = value.serialize()
            if e:
                item["error"] = str(e)
            monvalue_list.append(item)
        return json.dumps({"set": {"feature": feature.serialize(), "values": monvalue_list}}, indent=_INDENT_LEVEL)

    return "\n".join(map(str, [f"set {feature} for {mon} to {value if not e else 'ERROR: ' + str(e)}" for mon, value, e in monvalues]))

TogFeatureInputList = list[tuple[MonitorData | None, ValueData | None, ValueData | None, Exception | None]]

def tog_feature_output(feature: FeatureData, monvalues: TogFeatureInputList, json_output) -> str:
    if json_output:
        monvalue_list = []
        for mon, original, new, e in monvalues:
            item = {}
            if mon:
                item["monitor"] = mon.serialize()
            if original:
                item["original_value"] = original.serialize()
            if new:
                item["new_value"] = new.serialize()
            if e:
                item["error"] = str(e)
            monvalue_list.append(item)
        return json.dumps({"toggle": {"feature": feature.serialize(), "values": monvalue_list}}, indent=_INDENT_LEVEL)

    return "\n".join(map(str, [f"toggled {feature} for {mon} from {original} to {new}" for mon, original, new in monvalues]))


def caps_raw_output(moncaps: list[tuple[MonitorData, str]], json_output: bool) -> str:
    if json_output:
        moncaps_list = [{"monitor": mon.serialize(), "data": caps} for mon, caps in moncaps]
        return json.dumps({"caps": moncaps_list, "type": "raw"}, indent=_INDENT_LEVEL)

    return "\n".join(map(str, [f"Capability string for {mon}:\n{indentation}{caps}" for mon, caps in moncaps]))


def caps_parsed_output(moncaps: list[tuple[MonitorData, CapabilityData]], json_output: bool) -> str:
    if json_output:
        moncaps_list = [{"monitor": mon.serialize(), "data": caps.serialize()} for mon, caps in moncaps]
        return json.dumps({"caps": moncaps_list, "type": "full"}, indent=_INDENT_LEVEL)

    return "\n".join(map(str, [f"{mon}:\n{textwrap.indent(str(caps), indentation)}" for mon, caps in moncaps]))

