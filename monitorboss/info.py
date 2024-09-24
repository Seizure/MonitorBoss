import traceback
from dataclasses import dataclass
from typing import ItemsView

from frozendict import frozendict

from monitorboss.config import Config
from pyddc import VCPCommand, get_vcp_com
from pyddc.vcp_abc import Capabilities
from pyddc.vcp_codes import VCPCodes

# TODO: move _str functions into classes as __str__


@dataclass(frozen=True)
class FeatureData:
    name: str
    code: int
    aliases: tuple[str, ...]

    def serialize(self) -> dict:
        data = {"code": self.code}
        if self.name:
            data["name"] = self.name
        if self.aliases:
            data["aliases"] = self.aliases
        return data

    def __str__(self):
        if self.name:
            return f"{self.name} ({self.code})"
        else:
            return str(self.code)


def feature_data(code: int, cfg: Config) -> FeatureData:
    com = get_vcp_com(code)
    name = ""
    aliases = []
    if com:
        name = com.name
        aliases = [alias for alias, val in cfg.feature_aliases.items() if val == com.code.value]
    return FeatureData(name, code, tuple(aliases))


@dataclass(frozen=True)
class MonitorData:
    id: int
    aliases: tuple[str, ...]

    def serialize(self) -> dict:
        data = {"id": self.id}
        if self.aliases:
            data["aliases"] = self.aliases
        return data

    def __str__(self):
        return f"monitor #{self.id}" + (f" ({', '.join(map(str, self.aliases))})" if self.aliases else "")


def monitor_data(mon: int, cfg: Config) -> MonitorData:
    return MonitorData(mon, tuple([alias for alias, val in cfg.monitor_names.items() if mon == val]))


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

    def __str__(self):
        valstr = f"{self.value}"
        if self.param or self.aliases:
            valstr += " ("
            valstr += f"{'PARAM: ' + self.param if self.param else ''}"
            valstr += f"{' | ' if self.param and self.aliases else ''}"
            valstr += f"{('ALIASES: ' + ', '.join(map(str, self.aliases))) if self.aliases else ''}"
            valstr += ")"
        return valstr


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


# TODO: do we want PYDDC to be the one to format things in a structure like this, rather than a dict?
@dataclass(frozen=True)
class CapabilityData:
    attributes: frozendict[str, str]
    cmds: frozendict[str, tuple[FeatureData, ...]]
    vcps: frozendict[str, frozendict[FeatureData, tuple[ValueData, ...]]]
    errata: frozendict[str, tuple[str, ...]]  # TODO: not sure how to find/parse out errata rn

    def serialize(self) -> dict:
        return {
            **self.attributes,
            "cmds": {
                cmd: [feature.serialize() for feature in features]
                for cmd, features in self.cmds.items()
            },
            "vcps": {
                vcp: [
                    {
                        "feature": feature.serialize(),
                        **(
                            {"params": [value.serialize() for value in values]}
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
    cmds: dict[str, list[FeatureData]] = {}
    vcps: dict[str, dict[FeatureData, list[ValueData]]] = {}
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
                values = f.values if f.values else []
                for j, v in enumerate(values):
                    values[j] = value_data(f.cap, v, cfg)
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
