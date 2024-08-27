from argparse import ArgumentParser
from collections.abc import Sequence
import json
from logging import getLogger
from pprint import PrettyPrinter
from time import sleep

from monitorboss import MonitorBossError
from monitorboss.config import Config, get_config
from monitorboss.impl import Attribute
from monitorboss.impl import list_monitors, get_attribute, set_attribute, toggle_attribute, get_vcp_capabilities
from pyddc import parse_capabilities, get_vcp_com, VCPIOError
from pyddc.vcp_codes import VCPCodes, VCPCommand
from pyddc.vcp_abc import Capability, Capabilities

_log = getLogger(__name__)


def __check_attr(attr: str) -> Attribute:
    _log.debug(f"check attribute: {attr!r}")
    try:
        return Attribute[attr]
    except KeyError as err:
        raise MonitorBossError(
            f"{attr} is not a valid attribute.\n"
            "Valid attributes are: {', '.join(Attribute.__members__)}."
        ) from err


def __check_mon(mon: str, cfg: Config) -> int:
    _log.debug(f"check monitor: {mon!r}")
    mon = cfg.monitor_names.get(mon, mon)
    try:
        return int(mon)
    except ValueError as err:
        raise MonitorBossError(
            f"{mon} is not a valid monitor.\n"
            "Valid monitors are: {', '.join(cfg.monitor_names)}, or an ID number."
        ) from err


def __check_val(attr: Attribute, val: str, cfg: Config) -> int:
    _log.debug(f"check attribute value: attr {attr}, value {val}")
    match attr:
        case Attribute.src:
            if val in cfg.input_source_names:
                return cfg.input_source_names[val]
            elif val in attr.value.com.param_names:
                return attr.value.com.param_names[val]
            try:
                return int(val)
            except ValueError as err:
                raise MonitorBossError(
                    f"{val} is not a valid input source.\n"
                    f"""Valid input sources are: {
                        ', '.join(list(attr.value.com.param_names.keys()) + list(cfg.input_source_names))
                    }, or a code number (non-negative integer).\n"""
                    "NOTE: A particular monitor will probably support only some of these values. "
                    "Check your monitor's specs for the inputs it accepts."
                ) from err

        case Attribute.cnt:
            try:
                return int(val)
            except ValueError as err:
                raise MonitorBossError(
                    f"{val} is not a valid contrast value.\n"
                    "Valid contrast values are non-negative integers."
                ) from err

        case Attribute.lum:
            try:
                return int(val)
            except ValueError as err:
                raise MonitorBossError(
                    f"{val} is not a valid luminance value.\n"
                    "Valid luminance values are non-negative integers"
                ) from err

        case Attribute.pwr:
            if val in attr.value.com.param_names:
                return attr.value.com.param_names[val]
            try:
                return int(val)
            except ValueError as err:
                raise MonitorBossError(
                    f"{val} is not a valid power mode.\n"
                    f"""Valid power modes are: {
                        ', '.join(list(attr.value.com.param_names.keys()))
                    }, or a code number (non-negative integer).\n"""
                    "NOTE: A particular monitor will probably support only some of these values. "
                    "Check your monitor's specs for the inputs it accepts."
                ) from err

        case Attribute.clr:
            if val in attr.value.com.param_names:
                return attr.value.com.param_names[val]
            try:
                return int(val)
            except ValueError as err:
                raise MonitorBossError(
                    f"{val} is not a valid color preset.\n"
                    f"""Valid color presets are: {
                        ', '.join(list(attr.value.com.param_names.keys()))
                    }, or a code number (non-negative integer).\n"""
                    "NOTE: A particular monitor will probably support only some of these values. "
                    "Check your monitor's specs for the inputs it accepts."
                ) from err


# Config is not currently used, but it will be when we allow feature aliases, so just including it
def __feature_str(com: VCPCommand, cfg: Config) -> str:
    return f"{com.desc} ({com.value})"


def __monitor_str(mon: int, cfg: Config) -> str:
    monstr = f"monitor #{mon} "
    aliases = ""
    for v, k in cfg.monitor_names.items():
        if mon == k:
            aliases += v+", "
    if aliases:
        monstr += f"({aliases[:-2]})"

    return monstr.strip()


# TODO: this will need to radically change when we allow aliases for arbitrary/all features
def __value_str(attr: Attribute, value: int, cfg: Config) -> str:
    valstr = f"{value}"
    param = ""
    aliases = ""
    for v, k in attr.value.com.param_names.items():
        if value == k:
            param = v
    if attr is Attribute.src:
        for v, k in cfg.input_source_names.items():
            if value == k:
                aliases += v+", "
    if aliases:
        aliases = aliases[:-2]
    valstr += f" ({param + (' | ' if param and aliases else '') + aliases})" if param or aliases else ""
    return valstr


def __list_mons(args, cfg: Config):
    _log.debug(f"list monitors: {args}")
    for index, monitor in enumerate(list_monitors()):
        print(f"{__monitor_str(index, cfg)}")


# TODO: this is kind of broken (see IDE warnings) and will change when VCP caps parsing changes anyways
def __translate_vcp_entry(cap: Capability) -> Capability:
    _log.debug(f"translate VCP entry: {cap}")
    com = get_vcp_com(cap.cap)
    if com is None:
        return cap
    cap.cap = f"{com.name} ({com.value})"
    if cap.values is not None:
        def translate_vcp_value(value: int | str | Capability) -> int | str:
            if isinstance(value, Capability):
                if value.values is not None:
                    return value
                value = value.cap
            for param_name in com.param_names:
                if value == com.param_names[param_name].value:
                    return f"{param_name}={value}"
            return value
        cap.values = [translate_vcp_value(value) for value in cap.values]
    return cap


def __translate_caps(caps: dict[str, Capabilities]):
    _log.debug(f"translate capabilities: {caps}")
    if 'cmds' in caps:
        for i, c in enumerate(caps['cmds']):
            caps['cmds'][i] = __translate_vcp_entry(c)
    if 'vcp' in caps:
        for i, c in enumerate(caps['vcp']):
            c = __translate_vcp_entry(c)
            caps['vcp'][i] = c





# TODO: waiting for VCP caps parsing to be fixed to use only ints; do proper alias parsing
def __get_caps(args, cfg: Config) -> str | dict:
    _log.debug(f"get capabilities: {args}")
    mon = __check_mon(args.mon, cfg)
    caps = get_vcp_capabilities(mon)

    if args.raw:
        print(caps)
        return caps
    caps = parse_capabilities(caps)
    if args.summary:
        summary = __monitor_str(mon, cfg)
        summary += ":"
        if caps["type"]:
            summary += f" {caps['type']}"
        if caps["type"] and caps["model"]:
            summary += ","
        if caps["model"]:
            summary += f" model {caps['model']}"
        summary += '\n'
        if caps["vcp"]:
            for c in caps["vcp"]:
                if c.cap == VCPCodes.input_source and c.values is not None:
                    c = __translate_vcp_entry(c)
                    summary += f"  - input sources: {', '.join(map(str, c.values))}\n"
                elif c.cap == VCPCodes.image_color_preset and c.values is not None:
                    c = __translate_vcp_entry(c)
                    summary += f"  - color presets: {', '.join(map(str, c.values))}\n"
        print(summary)
        return summary
    __translate_caps(caps)
    pprinter = PrettyPrinter(indent=4, sort_dicts=True)
    pprinter.pprint(caps)


def __get_attr(args, cfg: Config):
    _log.debug(f"get attribute: {args}")
    attr = __check_attr(args.attr)
    mons = [__check_mon(m, cfg) for m in args.mon]
    cur_vals = []
    max_vals = []
    for i, m in enumerate(mons):
        ret = get_attribute(m, attr, cfg.wait_internal_time)
        cur_vals.append(ret.value)
        max_vals.append(None if attr.value.com.discrete else ret.max)
        if i+1 < len(mons):
            sleep(cfg.wait_get_time)
    for mon, val, maximum in zip(mons, cur_vals, max_vals):
        print(f"{__feature_str(attr.value.com, args)} for {__monitor_str(mon, cfg)} is {__value_str(attr, val, cfg)}" + (f" (Maximum: {__value_str(attr, maximum, cfg)})" if maximum is not None else ""))


def __set_attr(args, cfg: Config):
    _log.debug(f"set attribute: {args}")
    attr = __check_attr(args.attr)
    mons = [__check_mon(m, cfg) for m in args.mon]
    val = __check_val(attr, args.val, cfg)
    new_vals = []
    for i, m in enumerate(mons):
        new_vals.append(set_attribute(m, attr, val, cfg.wait_internal_time))
        if i + 1 < len(mons):
            sleep(cfg.wait_set_time)
    new_vals = [set_attribute(m, attr, val, cfg.wait_internal_time) for m in mons]
    for mon, new_val in zip(mons, new_vals):
        print(f"set {__feature_str(attr.value.com, args)} for {__monitor_str(mon, cfg)} to {__value_str(attr, new_val, cfg)}")


def __tog_attr(args, cfg: Config):
    _log.debug(f"toggle attribute: {args}")
    attr = __check_attr(args.attr)
    mons = [__check_mon(m, cfg) for m in args.mon]
    val1 = __check_val(attr, args.val1, cfg)
    val2 = __check_val(attr, args.val2, cfg)
    new_vals = []
    for i, m in enumerate(mons):
        new_vals.append(toggle_attribute(m, attr, val1, val2, cfg.wait_internal_time))
        if i + 1 < len(mons):
            sleep(cfg.wait_set_time)
    for mon, tog_val in zip(mons, new_vals):
        print(f"Toggled {__feature_str(attr.value.com, args)} for {__monitor_str(mon, cfg)} from {__value_str(attr, tog_val.old, cfg)} to {__value_str(attr, tog_val.new, cfg)}")


text = "Commands for manipulating and polling your monitors"
parser = ArgumentParser(description="Boss your monitors around.")
parser.add_argument("--config", type=str, help="the config file path to use")

mon_subparsers = parser.add_subparsers(title="monitor commands", help=text, dest="subcommand", required=True)

text = "List all available monitors"
list_parser = mon_subparsers.add_parser("list", help=text, description=text)
list_parser.set_defaults(func=__list_mons)

text = "Get the capabilities dictionary of a monitor"
description = ("Get the capabilities dictionary of a monitor. By default, this command parses the standard "
               "capabilities string into a structured and readable format, as well as provides human-readable names"
               "for known VCP codes and their defined options. If the --raw option is used, all other arguments will "
               "be ignored. Otherwise, if the --summary argument is used, all other arguments will be ignored.")
caps_parser = mon_subparsers.add_parser("caps", help=text, description=description)
caps_parser.set_defaults(func=__get_caps)
caps_parser.add_argument("mon", type=str, help="the monitor to retrieve capabilities from")
caps_parser.add_argument("-r", "--raw", action='store_true', help="return the original, unparsed capabilities string")
caps_parser.add_argument("-s", "--summary", action='store_true', help="return a highly formatted and abridged summary of the capabilities")

text = "return the value of a given attribute"
get_parser = mon_subparsers.add_parser("get", help=text, description=text)
get_parser.set_defaults(func=__get_attr)
get_parser.add_argument("attr", type=str, help="the attribute to return")
get_parser.add_argument("mon", type=str, nargs="+", help="the monitor to control")

text = "sets a given attribute to a given value"
set_parser = mon_subparsers.add_parser("set", help=text, description=text)
set_parser.set_defaults(func=__set_attr)
set_parser.add_argument("attr", type=str, help="the attribute to set")
set_parser.add_argument("val", type=str, help="the value to set the attribute to")
set_parser.add_argument("mon", type=str, nargs="+", help="the monitor(s) to control")

text = "toggles a given attribute between two given values"
tog_parser = mon_subparsers.add_parser("tog", help=text, description=text)
tog_parser.set_defaults(func=__tog_attr)
tog_parser.add_argument("attr", type=str, help="the attribute to toggle")
tog_parser.add_argument("val1", type=str, help="the first value to toggle between")
tog_parser.add_argument("val2", type=str, help="the second value to toggle between")
tog_parser.add_argument("mon", type=str, nargs="+", help="the monitor(s) to control")

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
