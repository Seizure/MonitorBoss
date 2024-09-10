from argparse import ArgumentParser
from collections.abc import Sequence
from logging import getLogger
from pprint import PrettyPrinter
from time import sleep

from monitorboss import MonitorBossError
from monitorboss.config import Config, get_config
from monitorboss.impl import Feature, FeatureData
from monitorboss.impl import list_monitors, get_feature, set_feature, toggle_feature, get_vcp_capabilities
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


# TODO: originally included cfg in expectation of including feature aliases, but now I'm not sure we should?
#   maybe this should return a tuple of strings with varying degrees of extra information,
#   and you can determine how much of said information to use depending on verbosity?
#   Alternatively, might be time to entirely change the general formatting of the return texts to be multiline
#   so that including all the aliases won't be cumbersome to visually parse by a human
def _feature_str(com: VCPCommand, cfg: Config) -> str:
    return f"{com.name} ({com.value})"


def _monitor_str(mon: int, cfg: Config) -> str:
    monstr = f"monitor #{mon} "
    aliases = ""
    for v, k in cfg.monitor_names.items():
        if mon == k:
            aliases += v+", "
    if aliases:
        monstr += f"({aliases[:-2]})"

    return monstr.strip()


def _value_str(com: VCPCommand, value: int, cfg: Config) -> str:
    valstr = f"{value}"
    param = ""
    aliases = ""
    for v, k in com.param_names.items():
        if value == k:
            param = v
    # TODO: This will need to be generalized when we allow for arbitrary value aliases
    if com.value == VCPCodes.input_source:
        for v, k in cfg.input_source_names.items():
            if value == k:
                aliases += v+", "
    if aliases:
        aliases = aliases[:-2]
    if param or aliases:
        valstr += " ("
        valstr += f"{'PARAM: ' + param if param else ''}"
        valstr += f"{' | ' if param and aliases else ''}"
        valstr += f"{('ALIASES: ' + aliases) if aliases else ''}"
        valstr += ")"
    return valstr


def _list_mons(args, cfg: Config):
    _log.debug(f"list monitors: {args}")
    for index, monitor in enumerate(list_monitors()):
        print(f"{_monitor_str(index, cfg)}")


def _get_caps(args, cfg: Config):
    _log.debug(f"get capabilities: {args}")
    mon = _check_mon(args.mon, cfg)
    caps_raw = get_vcp_capabilities(mon)

    if args.raw:
        print(caps_raw)
        return

    caps_dict = parse_capabilities(caps_raw)
    for s in caps_dict:
        if s.lower().startswith("cmd") or s.lower().startswith("vcp"):
            for i, c in enumerate(caps_dict[s]):
                cap = caps_dict[s][i]
                com = get_vcp_com(int(cap.cap))
                if com is not None:
                    cap.cap = _feature_str(com, cfg)
                    if cap.values is not None:
                        for x, p in enumerate(cap.values):
                            cap.values[x] = _value_str(com, p, cfg)

    if args.summary:
        summary = _monitor_str(mon, cfg)
        summary += ":"

        if caps_dict["type"]:
            summary += f" {caps_dict['type']}"
        if caps_dict["type"] and caps_dict["model"]:
            summary += ","
        if caps_dict["model"]:
            summary += f" model {caps_dict['model']}"
        summary += '\n'
        for s in caps_dict:
            if s.lower().startswith("vcp"):
                for c in caps_dict[s]:
                    if isinstance(c.cap, str) and (str(VCPCodes.input_source) in c.cap or str(VCPCodes.image_color_preset) in c.cap):
                        summary += f"  - {c.cap}: {', '.join(map(str, c.values))}\n"
        print(summary)
        return

    pprinter = PrettyPrinter(indent=4, sort_dicts=True)
    pprinter.pprint(caps_dict)


def _get_feature(args, cfg: Config):
    _log.debug(f"get feature: {args}")
    vcpcom = _check_feature(args.feature, cfg)
    mons = [_check_mon(m, cfg) for m in args.mon]
    cur_vals = []
    max_vals = []
    for i, m in enumerate(mons):
        ret = get_feature(m, vcpcom, cfg.wait_internal_time)
        cur_vals.append(ret.value)
        max_vals.append(None if vcpcom.discrete else ret.max)
        if i+1 < len(mons):
            sleep(cfg.wait_get_time)
    for mon, val, maximum in zip(mons, cur_vals, max_vals):
        print(f"{_feature_str(vcpcom, args)} for {_monitor_str(mon, cfg)} is {_value_str(vcpcom, val, cfg)}" + (f" (Maximum: {_value_str(vcpcom, maximum, cfg)})" if maximum is not None else ""))


def _set_feature(args, cfg: Config):
    _log.debug(f"set feature: {args}")
    vcpcom = _check_feature(args.feature, cfg)
    mons = [_check_mon(m, cfg) for m in args.mon]
    val = _check_val(vcpcom, args.val, cfg)
    new_vals = []
    for i, m in enumerate(mons):
        new_vals.append(set_feature(m, vcpcom, val, cfg.wait_internal_time))
        if i + 1 < len(mons):
            sleep(cfg.wait_set_time)
    new_vals = [set_feature(m, vcpcom, val, cfg.wait_internal_time) for m in mons]
    for mon, new_val in zip(mons, new_vals):
        print(f"set {_feature_str(vcpcom, args)} for {_monitor_str(mon, cfg)} to {_value_str(vcpcom, new_val, cfg)}")


def _tog_feature(args, cfg: Config):
    _log.debug(f"toggle feature: {args}")
    vcpcom = _check_feature(args.feature, cfg)
    mons = [_check_mon(m, cfg) for m in args.mon]
    val1 = _check_val(vcpcom, args.val1, cfg)
    val2 = _check_val(vcpcom, args.val2, cfg)
    new_vals = []
    for i, m in enumerate(mons):
        new_vals.append(toggle_feature(m, vcpcom, val1, val2, cfg.wait_internal_time))
        if i + 1 < len(mons):
            sleep(cfg.wait_set_time)
    for mon, tog_val in zip(mons, new_vals):
        print(f"toggled {_feature_str(vcpcom, args)} for {_monitor_str(mon, cfg)} from {_value_str(vcpcom, tog_val.old, cfg)} to {_value_str(vcpcom, tog_val.new, cfg)}")


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
caps_parser.add_argument("mon", type=str, help="the monitor to retrieve capabilities from")
caps_exclusive_flags = caps_parser.add_mutually_exclusive_group()
caps_exclusive_flags.add_argument("-r", "--raw", action='store_true', help="return the original, unparsed capabilities string")
caps_exclusive_flags.add_argument("-s", "--summary", action='store_true', help="return a highly formatted and abridged summary of the capabilities")

text = "return the value of a given feature"
get_parser = mon_subparsers.add_parser("get", help=text, description=text)
get_parser.set_defaults(func=_get_feature)
get_parser.add_argument("mon", type=str, nargs="+", help="the monitor(s) to control")
get_parser.add_argument("feature", type=str, help="the feature to return")

text = "sets a given feature to a given value"
set_parser = mon_subparsers.add_parser("set", help=text, description=text)
set_parser.set_defaults(func=_set_feature)
set_parser.add_argument("mon", type=str, nargs="+", help="the monitor(s) to control")
set_parser.add_argument("feature", type=str, help="the feature to set")
set_parser.add_argument("val", type=str, help="the value to set the feature to")

text = "toggles a given feature between two given values"
tog_parser = mon_subparsers.add_parser("tog", help=text, description=text)
tog_parser.set_defaults(func=_tog_feature)
tog_parser.add_argument("mon", type=str, nargs="+", help="the monitor(s) to control")
tog_parser.add_argument("feature", type=str, help="the feature to toggle")
tog_parser.add_argument("val1", type=str, help="the first value to toggle between")
tog_parser.add_argument("val2", type=str, help="the second value to toggle between")

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
