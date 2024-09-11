from dataclasses import dataclass

from monitorboss.config import Config
from pyddc import VCPCommand
from pyddc.vcp_codes import VCPCodes


@dataclass
class FeatureData:
    com: VCPCommand
    aliases: [str]


def feature_data(com: VCPCommand, cfg: Config) -> FeatureData:
    return FeatureData(com, [alias for alias, val in cfg.feature_aliases.items() if val == com.value])


def feature_str(data: FeatureData) -> str:
    return f"{data.com.name} ({data.com.value})"


@dataclass
class MonitorData:
    id: int
    aliases: [str]


def monitor_data(mon: int, cfg: Config) -> MonitorData:
    data = MonitorData(mon, [])
    for v, k in cfg.monitor_names.items():
        if mon == k:
            data.aliases.append(v)

    return data


def monitor_str(data: MonitorData) -> str:
    return f"monitor #{data.id}" + (f" ({', '.join(map(str, data.aliases))})" if data.aliases else "")


@dataclass
class ValueData:
    value: int
    param: str
    aliases: [str]


def value_data(com: VCPCommand, value: int, cfg: Config) -> ValueData:
    data = ValueData(value, "", [])
    for v, k in com.param_names.items():
        if value == k:
            data.param = v
            break
    # TODO: This will need to be generalized when we allow for arbitrary value aliases
    if com.value == VCPCodes.input_source:
        for v, k in cfg.input_source_names.items():
            if value == k:
                data.aliases.append(v)

    return data


def value_str(data: ValueData) -> str:
    valstr = f"{data.value}"
    if data.param or data.aliases:
        valstr += " ("
        valstr += f"{'PARAM: ' + data.param if data.param else ''}"
        valstr += f"{' | ' if data.param and data.aliases else ''}"
        valstr += f"{('ALIASES: ' + ', '.join(map(str, data.aliases))) if data.aliases else ''}"
        valstr += ")"
    return valstr
