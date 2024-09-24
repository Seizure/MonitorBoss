import json
from argparse import ArgumentParser
from collections.abc import Sequence
from logging import getLogger, DEBUG
from pprint import PrettyPrinter
from time import sleep

from monitorboss import MonitorBossError
from monitorboss.config import Config, get_config
from monitorboss.impl import list_monitors, get_feature, set_feature, toggle_feature, get_vcp_capabilities
from monitorboss.info import feature_str, monitor_str, value_str, feature_data, monitor_data, value_data, capability_data
from pyddc import parse_capabilities, get_vcp_com
from pyddc.vcp_codes import VCPCodes, VCPCommand

_log = getLogger(__name__)


# TODO: This does not allow for custom/OEM codes as is (for when we add such)
def _check_feature(feature: str, cfg: Config) -> VCPCommand:
    _log.debug(f"check feature: {feature!r}")
    if feature.isdigit():
        for code in VCPCodes:
            if int(feature) == code.value:
                return get_vcp_com(code.value)
        raise MonitorBossError(
            f"{feature} is not a valid feature code."
        )
    else:
        for alias, code in cfg.feature_aliases.items():
            if alias == feature:
                return get_vcp_com(code)
        for code in VCPCodes:
            com = get_vcp_com(code.value)
            if com.name == feature:
                return com
        raise MonitorBossError(
            f"{feature} is not a valid feature alias."
        )


def _check_mon(mon: str, cfg: Config) -> int:
    _log.debug(f"check monitor: {mon!r}")
    mon = cfg.monitor_names.get(mon, mon)
    try:
        return int(mon)
    except ValueError as err:
        raise MonitorBossError(
            f"{mon} is not a valid monitor.\n"
            f"Valid monitors are: {', '.join(cfg.monitor_names)}, or an ID number."
        ) from err


def _check_val(com: VCPCommand, val: str, cfg: Config) -> int:
    _log.debug(f"check feature value: ftr {com.name}, value {val}")
    # Check if input is a positive integer, and if so, just return it.
    if val.isdigit():
        return int(val)
    # if not, we need to check for valid params and aliases...
    else:
        # ...so first check if there is a param name...
        if val in com.param_names:
            return com.param_names[val]
        # ... and if not, check if the command is input_source, and if so, check the aliases
        if com.value == VCPCodes.input_source:
            # TODO: This will need to be generalized when we allow for arbitrary value aliases
            if val in cfg.input_source_names:
                return cfg.input_source_names[val]

    # If we got here, an invalid value was provided
    error_text = f"{val} is not a valid value for feature \"{com.name}\".\nValid values are:\n"
    if com.param_names:
        error_text += f"\t- [PARAM NAMES]: {', '.join(list(com.param_names.keys()))}\n"
    # TODO: This will need to be generalized when we allow for arbitrary value aliases
    if com.value == VCPCodes.input_source and cfg.input_source_names:
        error_text += f"\t- [CONFIG ALIASES]: {', '.join(list(cfg.input_source_names))}\n"
    error_text += """\t- a code number (non-negative integer).\n
    NOTE: A particular monitor may only support some of these values. Check your monitor's specs for the inputs it accepts."""

    raise MonitorBossError(error_text)


def _list_mons(args, cfg: Config):
    _log.debug(f"list monitors: {args}")
    for index, monitor in enumerate(list_monitors()):
        mdata = monitor_data(index, cfg)
        if args.json:
            print(json.dumps({"list": {"monitor": mdata.serialize()}}))
        else:
            print(monitor_str(mdata))


def _get_caps(args, cfg: Config):
    _log.debug(f"get capabilities: {args}")
    indent_level = 4 if _log.getEffectiveLevel() <= DEBUG else None
    mon = _check_mon(args.monitor, cfg)
    caps_raw = get_vcp_capabilities(mon)

    if args.raw:
        if args.json:
            print(json.dumps({"caps": {"raw": caps_raw}}))
        else:
            print(caps_raw)
        return

    caps_dict = parse_capabilities(caps_raw)
    caps_data = capability_data(caps_dict, cfg)

    if args.summary:
        if args.json:
            print(json.dumps({"caps": {"full": caps_data.serialize()}}, indent=indent_level))
        else:
            print(capability_str(caps_data))
        return

    print(json.dumps(caps_data.serialize(), indent=4))
    exit()
    # TODO: PYDDC definition of Capabilities currently allows for:
    #   - indefinitely nested caps.
    #   - non-int feature codes and values (see "code" and "v" variables below
    #   We do not account for this here, but that should change in PYDDC anyways
    #   When it is, this code can probably be simplified a bit (or will have to change)
    for s in caps_dict:
        if s.lower().startswith("cmd") or s.lower().startswith("vcp"):
            for i, cap in enumerate(caps_dict[s]):
                code = cap.cap
                values = cap.values  # may be None
                vdata_list = None
                feature = get_vcp_com(int(code))  # may be None
                fdata = feature_data(feature, cfg) if feature is not None else None
                if feature is not None and values is not None:
                    vdata_list = [value_data(feature, int(v), cfg) for v in values]
                if args.json:
                    vjson = [vdata.serialize() for vdata in vdata_list] if vdata_list else None
                    cap_json = [{"feature": (fdata.serialize() if fdata is not None else {"code": code})}]
                    if vjson:
                        cap_json.append({"values": vjson})
                    caps_dict[s][i] = {"capability": cap_json}
                else:
                    cap.cap = feature_str(fdata) if fdata else cap.cap
                    cap.values = [value_str(vdata) for vdata in vdata_list] if vdata_list else cap.values

    if args.summary:
        # TODO: implement --json
        mdata = monitor_data(mon, cfg)
        vcp_features = {}
        for s in (x for x in caps_dict if x.lower().startswith("vcp")):
            for c in caps_dict[s]:
                if args.json:
                    pass
                else:
                    if isinstance(c.cap, str) and ((str(VCPCodes.input_source) in c.cap or str(VCPCodes.image_color_preset) in c.cap)):
                        vcp_features[s]
                        pass

        if args.json:
            summary = {"caps": {"monitor": mdata.serialize()}}
            if caps_dict["type"]:
                summary["caps"]["type"] = caps_dict["type"]
            if caps_dict["model"]:
                summary["caps"]["model"] = caps_dict["model"]
        else:
            summary = f"{monitor_str(mdata)}: {caps_dict.get('type', '')}"
            summary += "," if caps_dict["type"] and caps_dict["model"] else ""
            summary += f" model {caps_dict.get('model', '')}\n"
            for s in caps_dict:
                if s.lower().startswith("vcp"):
                    for c in caps_dict[s]:
                        if isinstance(c.cap, str) and (str(VCPCodes.input_source) in c.cap or str(VCPCodes.image_color_preset) in c.cap):
                            summary += f"  - {c.cap}: {', '.join(map(str, c.values))}\n"
            print(summary)
    else:
        if args.json:
            print(json.dumps({"caps": caps_dict}, indent=indent_level))
        else:
            pprinter = PrettyPrinter(indent=4, sort_dicts=True)
            pprinter.pprint(caps_dict)


def _get_feature(args, cfg: Config):
    _log.debug(f"get feature: {args}")
    vcpcom = _check_feature(args.feature, cfg)
    mons = [_check_mon(m, cfg) for m in args.monitor]
    cur_vals = []
    max_vals = []
    for i, m in enumerate(mons):
        ret = get_feature(m, vcpcom, cfg.wait_internal_time)
        cur_vals.append(ret.value)
        max_vals.append(None if vcpcom.discrete else ret.max)
        if i+1 < len(mons):
            sleep(cfg.wait_get_time)
    for mon, val, maximum in zip(mons, cur_vals, max_vals):
        fdata = feature_data(vcpcom, cfg)
        mdata = monitor_data(mon, cfg)
        vdata = value_data(vcpcom, val, cfg)
        if args.json:
            print(json.dumps({"get": {"monitor": mdata.serialize(), "feature": fdata.serialize(), "value": vdata.serialize()}}))
        else:
            fstr = feature_str(fdata)
            mstr = monitor_str(mdata)
            vstr = value_str(vdata)
            print(f"{fstr} for {mstr} is {vstr}" + (f" (Maximum: {vstr})" if maximum is not None else ""))


def _set_feature(args, cfg: Config):
    _log.debug(f"set feature: {args}")
    vcpcom = _check_feature(args.feature, cfg)
    mons = [_check_mon(m, cfg) for m in args.monitor]
    val = _check_val(vcpcom, args.value, cfg)
    new_vals = []
    for i, m in enumerate(mons):
        new_vals.append(set_feature(m, vcpcom, val, cfg.wait_internal_time))
        if i + 1 < len(mons):
            sleep(cfg.wait_set_time)
    new_vals = [set_feature(m, vcpcom, val, cfg.wait_internal_time) for m in mons]
    for mon, new_val in zip(mons, new_vals):
        fdata = feature_data(vcpcom, cfg)
        mdata = monitor_data(mon, cfg)
        vdata = value_data(vcpcom, new_val, cfg)
        if args.json:
            print(json.dumps({"set": {"monitor": mdata.serialize(), "feature": fdata.serialize(), "value": vdata.serialize()}}))
        else:
            fstr = feature_str(fdata)
            mstr = monitor_str(mdata)
            vstr = value_str(vdata)
            print(f"set {fstr} for {mstr} to {vstr}")


def _tog_feature(args, cfg: Config):
    _log.debug(f"toggle feature: {args}")
    vcpcom = _check_feature(args.feature, cfg)
    mons = [_check_mon(m, cfg) for m in args.monitor]
    val1 = _check_val(vcpcom, args.value1, cfg)
    val2 = _check_val(vcpcom, args.value2, cfg)
    tog_vals = []
    for i, m in enumerate(mons):
        tog_vals.append(toggle_feature(m, vcpcom, val1, val2, cfg.wait_internal_time))
        if i + 1 < len(mons):
            sleep(cfg.wait_set_time)
    for mon, tog_val in zip(mons, tog_vals):
        fdata = feature_data(vcpcom, cfg)
        mdata = monitor_data(mon, cfg)
        vdata_new = value_data(vcpcom, tog_val.new, cfg)
        vdata_original = value_data(vcpcom, tog_val.old, cfg)
        if args.json:
            print(json.dumps({"toggle": {"monitor": mdata.serialize(), "feature": fdata.serialize(), "original_value": vdata_original.serialize(), "new_value": vdata_new.serialize()}}))
            pass
        else:
            fstr = feature_str(fdata)
            mstr = monitor_str(mdata)
            vstr_new = value_str(vdata_new)
            vstr_old = value_str(vdata_original)
            print(f"toggled {fstr} for {mstr} from {vstr_old} to {vstr_new}")


text = "Commands for manipulating and polling your monitors"
parser = ArgumentParser(description="Boss your monitors around.")
parser.add_argument("--config", type=str, help="the config file path to use")
parser.add_argument("--json", action='store_true', help="return output in json format")

mon_subparsers = parser.add_subparsers(title="monitor commands", help=text, dest="subcommand", required=True)

text = "List all available monitors"
list_parser = mon_subparsers.add_parser("list", help=text, description=text)
list_parser.set_defaults(func=_list_mons)

text = "Get the capabilities dictionary of a monitor"
description = ("Get the capabilities of a monitor. If no flags are used, the entire capabilities string is parsed into "
               "a structured format with human-readable names provided for known VCP codes and their defined options.")
caps_parser = mon_subparsers.add_parser("caps", help=text, description=description)
caps_parser.set_defaults(func=_get_caps)
caps_parser.add_argument("monitor", type=str, help="the monitor to retrieve capabilities from")
caps_exclusive_flags = caps_parser.add_mutually_exclusive_group()
caps_exclusive_flags.add_argument("-r", "--raw", action='store_true', help="return the original, unparsed capabilities string")
caps_exclusive_flags.add_argument("-s", "--summary", action='store_true', help="return a highly formatted and abridged summary of the capabilities")

text = "returns the value of a given feature"
get_parser = mon_subparsers.add_parser("get", help=text, description=text)
get_parser.set_defaults(func=_get_feature)
get_parser.add_argument("monitor", type=str, nargs="+", help="the monitor(s) to control")
get_parser.add_argument("feature", type=str, help="the feature to return")

text = "sets a given feature to a given value"
set_parser = mon_subparsers.add_parser("set", help=text, description=text)
set_parser.set_defaults(func=_set_feature)
set_parser.add_argument("monitor", type=str, nargs="+", help="the monitor(s) to control")
set_parser.add_argument("feature", type=str, help="the feature to set")
set_parser.add_argument("value", type=str, help="the value to set the feature to")

text = "toggles a given feature between two given values"
tog_parser = mon_subparsers.add_parser("tog", help=text, description=text)
tog_parser.set_defaults(func=_tog_feature)
tog_parser.add_argument("monitor", type=str, nargs="+", help="the monitor(s) to control")
tog_parser.add_argument("feature", type=str, help="the feature to toggle")
tog_parser.add_argument("value1", type=str, help="the first value to toggle between")
tog_parser.add_argument("value2", type=str, help="the second value to toggle between")

# conf set {mon_alias, input_alias} alias id<int> [-f]
# conf set wait time<float>
# conf rm {mon_alias, input_alias} alias
# command for starting guided monitor alias wizard
# command for starting guided input alias wizard (can be retrieved from VCP/"list" command)
# -f : perform set without confirmation even if alias already exists
# what should behavior be if removing an alias that doesn't exist?

# We're done with the subparsers
del text
del description


def get_help_texts():
    return {'': parser.format_help()} | {name: subparser.format_help() for name, subparser in
                                         mon_subparsers.choices.items()}


def run(args: str | Sequence[str] | None = None):
    _log.debug(f"run CLI: {args}")
    if isinstance(args, str):
        args = args.split()
    args = parser.parse_args(args)
    try:
        cfg = get_config(args.config)
        args.func(args, cfg)
    except MonitorBossError as err:
        parser.error(str(err))
