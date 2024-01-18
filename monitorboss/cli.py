from argparse import ArgumentParser
from pprint import PrettyPrinter

from config import *
from impl import *


def __check_attr(attr: str) -> Attribute:
    try:
        return Attribute[attr]
    except KeyError:
        raise MonitorBossError(
            f"{attr} is not a valid attribute.\nValid attributes are: {', '.join(Attribute.__members__)}."
        )


def __check_mon(mon: str, cfg: Config) -> int:
    mon = cfg.monitor_names.get(mon, mon)
    try:
        return int(mon)
    except ValueError:
        raise MonitorBossError(
            f"{mon} is not a valid monitor.\nValid monitors are: {', '.join(cfg.monitor_names)}, or an ID number."
        )


def __check_val(attr: Attribute, val: str, cfg: Config) -> ColorPreset | InputSource | PowerMode | int:
    match attr:
        case Attribute.SRC:
            if val in cfg.input_source_names:
                val = cfg.input_source_names[val]
            try:
                return InputSource[val]
            except KeyError:
                try:
                    return int(val)
                except ValueError:
                    raise MonitorBossError(
                        f"""{val} is not a valid input source.\nValid input sources are: {
                            ', '.join(list(InputSource.__members__) + list(cfg.input_source_names))
                        }, or a code number."""
                        "\nNOTE: A particular monitor will probably support only some of these values,"
                        " if any. Check your monitor's specs for the inputs it accepts."
                    )

        case Attribute.CNT:
            try:
                return int(val)
            except ValueError:
                raise MonitorBossError(
                    f"{val} is not a valid contrast value.\nValid contrast values are typically 0-100."
                )

        case Attribute.LUM:
            try:
                return int(val)
            except ValueError:
                raise MonitorBossError(
                    f"{val} is not a valid luminance value.\nValid luminance values are typically 0-100."
                )

        case Attribute.PWR:
            # PowerMode values are lowercase; other enums are uppercase.
            try:
                return PowerMode[val.lower()]
            except KeyError:
                raise MonitorBossError(
                    f"""{val} is not a valid power mode.\nValid power modes are: {
                        ", ".join(map(str.upper, PowerMode.__members__))
                    }."""
                )

        case Attribute.CLR:
            # ColorPreset values all start with "COLOR_TEMP_".
            try:
                return ColorPreset[f"COLOR_TEMP_{val}"]
            except KeyError:
                raise MonitorBossError(
                    f"""{val} is not a valid color preset.\nValid color presets are: {
                        ", ".join(m.removeprefix("COLOR_TEMP_") for m in ColorPreset.__members__)
                    }."""
                )


def __list_mons(args, cfg):
    def input_source_name(src):
        if isinstance(src, Enum):
            return src.name
        for name, value in cfg.input_source_names.items():
            if value == src:
                return f"{src} ({name})"
        return str(src)

    def color_preset_name(clr):
        return clr.name.removeprefix("COLOR_TEMP_") if isinstance(clr, Enum) else str(clr)

    for index, monitor in enumerate(list_monitors()):
        with monitor:
            try:
                caps = monitor.get_vcp_capabilities()
            except:
                raise MonitorBossError("could not list information for monitor #{index}.")
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


def __get_attr(args, cfg):
    attr = __check_attr(args.attr)
    mon = __check_mon(args.mon)

    val = get_attribute(mon, attr)

    if isinstance(val, Enum):
        val = val.name.upper().removeprefix("COLOR_TEMP_")

    pprinter = PrettyPrinter(indent=4)
    pprinter.pprint(val)


def __set_attr(args, cfg):
    attr = __check_attr(args.attr)
    mons = [__check_mon(m) for m in args.mon]

    val = __check_val(attr, args.val)

    set_attribute(mons, attr, val)


def __tog_attr(args, cfg):
    attr = __check_attr(args.attr)
    mons = [__check_mon(m) for m in args.mon]

    val1 = __check_val(attr, args.val1)
    val2 = __check_val(attr, args.val2)

    toggle_attribute(mons, attr, val1, val2)


def __make_parser():
    parser = ArgumentParser(description="Boss your monitors around.")
    subparsers = parser.add_subparsers(title="subcommands", help="basic commands", dest="subcommand", required=True)

    list_parser = subparsers.add_parser("list", help="list all the monitors and their possible attributes")
    list_parser.set_defaults(func=__list_mons)

    get_parser = subparsers.add_parser("get", help="return the value of a given attribute")
    get_parser.set_defaults(func=__get_attr)
    get_parser.add_argument("attr", type=str.upper, help="the attribute to return")
    get_parser.add_argument("mon", type=str.upper, help="the monitor to control")

    set_parser = subparsers.add_parser("set", help="sets a given attribute to a given value")
    set_parser.set_defaults(func=__set_attr)
    set_parser.add_argument("attr", type=str.upper, help="the attribute to set")
    set_parser.add_argument("val", type=str.upper, help="the value to set the attribute to")
    set_parser.add_argument("mon", type=str.upper, nargs="+", help="the monitor(s) to control")

    tog_parser = subparsers.add_parser("tog", help="toggles a given attribute between two given values")
    tog_parser.set_defaults(func=__tog_attr)
    tog_parser.add_argument("attr", type=str.upper, help="the attribute to toggle")
    tog_parser.add_argument("val1", type=str.upper, help="the first value to toggle between")
    tog_parser.add_argument("val2", type=str.upper, help="the second value to toggle between")
    tog_parser.add_argument("mon", type=str.upper, nargs="+", help="the monitor(s) to control")

    return parser


def run(args=None):
    parser = __make_parser()
    args = parser.parse_args(args)

    cfg = read_config()

    try:
        args.func(args, cfg)
    except MonitorBossError as err:
        parser.error(err)
