import traceback
from dataclasses import dataclass
from typing import ItemsView

from frozendict import frozendict

from monitorboss.config import Config
from pyddc import VCPCommand, get_vcp_com
from pyddc.vcp_abc import Capabilities
from pyddc.vcp_codes import VCPCodes


@dataclass(frozen=True)
class FeatureData:
    name: str
    code: int
    aliases: tuple[str, ...]

    def serialize(self) -> dict:
        data = {"name": self.name, "code": self.code}
        if self.aliases:
            data["aliases"] = self.aliases
        return data


def feature_data(code: int, cfg: Config) -> FeatureData:
    com = get_vcp_com(code)
    name = ""
    aliases = []
    if com:
        name = com.name
        aliases = [alias for alias, val in cfg.feature_aliases.items() if val == com.code.value]
    return FeatureData(name, code, tuple(aliases))


def feature_str(data: FeatureData) -> str:
    return f"{data.name} ({data.code})"


@dataclass(frozen=True)
class MonitorData:
    id: int
    aliases: tuple[str, ...]

    def serialize(self) -> dict:
        data = {"id": self.id}
        if self.aliases:
            data["aliases"] = self.aliases
        return data


def monitor_data(mon: int, cfg: Config) -> MonitorData:
    return MonitorData(mon, tuple([alias for alias, val in cfg.monitor_names.items() if mon == val]))


def monitor_str(data: MonitorData) -> str:
    return f"monitor #{data.id}" + (f" ({', '.join(map(str, data.aliases))})" if data.aliases else "")


@dataclass(frozen=True)
class ValueData:
    value: int
    param: str
    aliases: tuple[str, ...]

    def serialize(self) -> dict:
        data = {"value": self.value}
        if self.param:
            data["param"] = self.param
        if self.aliases:
            data["aliases"] = self.aliases
        return data


def value_data(code: int, value: int, cfg: Config) -> ValueData:
    com = get_vcp_com(code)
    param = ""
    aliases = []
    if com:
        for v, k in com.param_names.items():
            if value == k:
                param = v
                break
        # TODO: This will need to be generalized when we allow for arbitrary value aliases
        if com.code == VCPCodes.input_source:
            aliases = [alias for alias, val in cfg.input_source_names.items() if value == val]

    data = ValueData(value, param, tuple(aliases))

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


# TODO: do we want PYDDC to be the one to format things in a structure like this, rather than a dict?
@dataclass(frozen=True)
class CapabilityData:
    attributes: frozendict[str, str]
    cmds: frozendict[str, tuple[int | FeatureData, ...]]
    vcps: frozendict[str, frozendict[int | FeatureData, tuple[int | ValueData, ...]]]
    errata: frozendict[str, tuple[str, ...]]  # TODO: not sure how to find/parse out errata rn

    def serialize(self) -> dict:
        return {
            **self.attributes,
            "cmds": {
                cmd: [
                    feature.serialize() if isinstance(feature, FeatureData) else feature
                    for feature in features
                ]
                for cmd, features in self.cmds.items()
            },
            "vcps": {
                vcp: [
                    {
                        "feature": feature.serialize() if isinstance(feature, FeatureData) else {"code": feature},
                        **(
                            {"params": [
                                value.serialize() if isinstance(value, ValueData) else value
                                for value in values
                            ]}
                            if values else {}
                        )
                    }
                    for feature, values in vcp_dict.items()
                ]
                for vcp, vcp_dict in self.vcps.items()
            },
            **(
                {"errata": dict(self.errata)}
                if self.errata else {}
            ),
        }


def capability_data(caps: dict[str, Capabilities], cfg) -> CapabilityData:
    info_fields: dict[str, int] = {}
    cmds: dict[str, list[int | FeatureData]] = {}
    vcps: dict[str, dict[int | FeatureData, list[int | ValueData]]] = {}
    errata: dict[str, list[str]] = {}  # TODO: not sure how to find/parse out errata rn

    # TODO: PYDDC definition of Capabilities currently allows for:
    #   - indefinitely nested caps.
    #   - non-int feature codes and values (passing cap.cap and cap.values data without checking)
    #   We do not account for this here, but that should change in PYDDC anyways
    for s in caps:
        if s.lower().startswith("cmd") and caps[s]:
            features = caps[s]
            for i, f in enumerate(features):
                features[i] = feature_data(f.cap, cfg)
            cmds[s] = features
        elif s.lower().startswith("vcp") and caps[s]:
            features_values = {}
            for i, f in enumerate(caps[s]):
                com = get_vcp_com(f.cap)
                values = f.values if f.values else []
                if com:
                    for j, v in enumerate(values):
                        values[j] = value_data(com.code, v, cfg)
                features_values[feature_data(f.cap, cfg)] = values

            vcps[s] = features_values
        else:
            info_fields[s] = caps[s]

    info_fields = frozendict(info_fields.items())
    for k, l in cmds.items():
        cmds[k] = tuple(l)
    cmds = frozendict(cmds)
    for k, d in vcps.items():
        for j, l in vcps[k].items():
            vcps[k][j] = tuple(l)
        vcps[k] = frozendict(d)
    vcps = frozendict(vcps)
    for k, l in errata.items():
        errata[k] = tuple(l)
    errata = frozendict(errata)

    return CapabilityData(info_fields, cmds, vcps, errata)


def capability_str(data: CapabilityData) -> str:
    # TODO: move the code from CLI to here
    pass
