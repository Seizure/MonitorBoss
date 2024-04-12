from argparse import ArgumentParser
from enum import Enum
from pprint import PrettyPrinter

from monitorboss import MonitorBossError
from monitorboss.config import Config, get_config
from monitorboss.impl import Attribute
from monitorboss.impl import list_monitors, get_attribute, set_attribute, toggle_attribute


def __check_attr(attr: str) -> Attribute:
    try:
        return Attribute[attr]
    except KeyError as err:
        raise MonitorBossError(
            f"{attr} is not a valid attribute.\nValid attributes are: {', '.join(Attribute.__members__)}."
        ) from err


def __check_mon(mon: str, cfg: Config) -> int:
    mon = cfg.monitor_names.get(mon, mon)
    try:
        return int(mon)
    except ValueError as err:
        raise MonitorBossError(
            f"{mon} is not a valid monitor.\nValid monitors are: {', '.join(cfg.monitor_names)}, or an ID number."
        ) from err


def __check_val(attr: Attribute, val: str, cfg: Config) -> int:
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
                    f"""{val} is not a valid input source.\nValid input sources are: {
                    ', '.join(list(attr.value.com.param_names.keys()) + list(cfg.input_source_names))
                    }, or a code number (non-negative integer)."""
                    "\nNOTE: A particular monitor will probably support only some of these values."
                    "Check your monitor's specs for the inputs it accepts."
                ) from err

        case Attribute.cnt:
            try:
                return int(val)
            except ValueError as err:
                raise MonitorBossError(
                    f"{val} is not a valid contrast value.\nValid contrast values are non-negative integers."
                ) from err

        case Attribute.lum:
            try:
                return int(val)
            except ValueError as err:
                raise MonitorBossError(
                    f"{val} is not a valid luminance value.\nValid luminance values are non-negative integers"
                ) from err

        case Attribute.pwr:
            if val in attr.value.com.param_names:
                return attr.value.com.param_names[val]
            try:
                return int(val)
            except ValueError as err:
                raise MonitorBossError(
                    f"""{val} is not a valid power mode.\nValid power modes are: {
                    ', '.join(list(attr.value.com.param_names.keys()))
                    }, or a code number (non-negative integer)."""
                    "\nNOTE: A particular monitor will probably support only some of these values."
                    "Check your monitor's specs for the inputs it accepts."
                ) from err

        case Attribute.clr:
            if val in attr.value.com.param_names:
                return attr.value.com.param_names[val]
            try:
                return int(val)
            except ValueError as err:
                raise MonitorBossError(
                    f"""{val} is not a valid color preset.\nValid color presets are: {
                    ', '.join(list(attr.value.com.param_names.keys()))
                    }, or a code number (non-negative integer)."""
                    "\nNOTE: A particular monitor will probably support only some of these values."
                    "Check your monitor's specs for the inputs it accepts."
                ) from err

# TODO: this is probably not working as intended after the changes, need to review
def __list_mons(args, cfg: Config):
    def input_source_name(src: int):
        if isinstance(src, Enum):
            return src.name
        for src_name, src_value in cfg.input_source_names.items():
            if src_value == src:
                return f"{src} ({src_name})"
        return str(src)

    def color_preset_name(clr: int):
        return clr.name.removeprefix("color_temp_") if isinstance(clr, Enum) else str(clr)

    for index, monitor in enumerate(list_monitors()):
        with monitor:
            try:
                caps = monitor.get_vcp_capabilities()
            except Exception as err:
                raise MonitorBossError(f"could not list information for monitor #{index}.") from err
            print(f"monitor #{index}", end="")
            for name, value in cfg.monitor_names.items():
                if value == index:
                    print(f" ({name})", end="")
                    break
            print(":", end="")
            if caps["type"]:
                print(f" {caps['type']}", end="")
            if caps["type"] and caps["model"]:
                print(",", end="")
            if caps["model"]:
                print(f" model {caps['model']}", end="")
            print()
            if caps["inputs"]:
                print(f"  - input sources: {', '.join(map(input_source_name, caps['inputs']))}")
            if caps["color_presets"]:
                print(f"  - color presets: {', '.join(map(color_preset_name, caps['color_presets']))}")


def __get_attr(args, cfg: Config) -> str:
    attr = __check_attr(args.attr)
    mon = __check_mon(args.mon, cfg)
    val = get_attribute(mon, attr)
    if isinstance(val, Enum):
        val = val.name.removeprefix("color_temp_")
    pprinter = PrettyPrinter(indent=4)
    pprinter.pprint(val)
    return str(val)


def __set_attr(args, cfg: Config) -> str:
    attr = __check_attr(args.attr)
    mons = [__check_mon(m, cfg) for m in args.mon]
    val = __check_val(attr, args.val, cfg)
    new_val = set_attribute(mons, attr, val)
    return str(new_val)


def __tog_attr(args, cfg: Config) -> str:
    attr = __check_attr(args.attr)
    mons = [__check_mon(m, cfg) for m in args.mon]
    val1 = __check_val(attr, args.val1, cfg)
    val2 = __check_val(attr, args.val2, cfg)
    new_val = toggle_attribute(mons, attr, val1, val2)
    return str(new_val)


text = "commands for manipulating and polling your monitors"
parser = ArgumentParser(description="Boss your monitors around.")
mon_subparsers = parser.add_subparsers(title="monitor commands", help=text, dest="subcommand", required=True)

text = "list all the monitors and their possible attributes"
list_parser = mon_subparsers.add_parser("list", help=text, description=text)
list_parser.set_defaults(func=__list_mons)

text = "return the value of a given attribute"
get_parser = mon_subparsers.add_parser("get", help=text, description=text)
get_parser.set_defaults(func=__get_attr)
get_parser.add_argument("attr", type=str, help="the attribute to return")
get_parser.add_argument("mon", type=str, help="the monitor to control")

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

del text  # We're done with the subparsers


def get_help_texts():
    return {'': parser.format_help()} | {name: subparser.format_help() for name, subparser in
                                         mon_subparsers.choices.items()}


def run(args=None):
    if isinstance(args, str):
        args = args.split()
    args = parser.parse_args(args)
    try:
        cfg = get_config()
        return args.func(args, cfg)
    except MonitorBossError as err:
        parser.error(str(err))
