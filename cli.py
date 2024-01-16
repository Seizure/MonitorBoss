import argparse

from softmon import *


MONITOR_NAMES = {"LEFT": 2, "MIDDLE": 1, "RIGHT": 0}


def __name_to_index(s: str):
    return MONITOR_NAMES[s.upper()]


def __check_attr(a: str) -> Attribute:
    a = a.upper()
    if hasattr(Attribute, a):
        a = Attribute[a]
    else:
        warning = f"{a} is not a valid attribute. Valid attributes are:\n"
        for e in Attribute:
            warning += f"{e.name},"
        warning = warning[0:-1]
        raise global_parser.error(warning)

    return a


def __check_mon(m: str) -> int:
    m = m.upper()
    if m in MONITOR_NAMES:
        m = MONITOR_NAMES[m]
    elif m.isdigit() and int(m) <= len(get_monitors()):
        m = int(m)
    else:
        warning = f"{m} is not a valid monitor. Valid monitors are:\n"
        for m in MONITOR_NAMES:
            warning += f"{m},"
        warning = warning[0:-1]
        global_parser.error(warning)

    return m


def __check_value(attr: Attribute, val) -> InputSource | PowerMode | int:
    val = val.upper()
    match attr:
        case Attribute.SRC:
            if hasattr(InputSource, val):
                val = InputSource[val]
            else:
                warning = f"{val} is an invalid SRC (Input Source). Valid sources are:\n"
                for s in InputSource:
                    s = s.__str__().replace('InputSource.', '')
                    warning += f"{s},"
                warning = (warning[0:-1] +
                           "\n\nNOTE: These are just the potential inputs an arbitrary monitor can accept. None of "
                           "these inputs are guaranteed to be supported by a particular monitor, and most probably "
                           "aren't. Cross-check with your monitor's specs.")
                global_parser.error(warning)

        case Attribute.CNT:
            if not val.isdigit() or int(val) > 100:
                global_parser.error(f"{val} is an invalid CNT (Contrast). Must be an int.")

        case Attribute.LUM:
            if not val.isdigit():
                global_parser.error(f"{val} is an invalid LUM (luminance). Must be an int.")

        case Attribute.PWR:
            if hasattr(PowerMode, val):
                val = PowerMode[val]
            else:
                global_parser.error(f"{val} is an invalid power mode")

    return val


def __get_attr(args):
    attr = __check_attr(args.attr)
    mon = __check_mon(args.monitor)

    args.out = get_attribute(mon, attr)


def __set_attr(args):
    attr = __check_attr(args.attr)
    mon = __check_mon(args.monitor)

    val = __check_value(attr, args.val)

    args.out = set_attribute(mon, attr, val)


def __toggle_attr(args):
    attr = __check_attr(args.attr)
    mon = __check_mon(args.monitor)

    val1 = __check_value(attr, args.val1)
    val2 = __check_value(attr, args.val2)

    args.out = toggle_attribute(mon, attr, val1, val2)


global_parser = argparse.ArgumentParser(description="Manage monitor states")
subparsers = global_parser.add_subparsers(title="softmon", help="Basic commands", dest='subcommand', required=True)

get_parser = subparsers.add_parser('get', help='returns the value of the desired attribute')
get_parser.set_defaults(func=__get_attr)
get_parser.add_argument('attr', type=str, help='The attribute to return')

set_parser = subparsers.add_parser('set', help='sets a value to the desired attribute')
set_parser.set_defaults(func=__set_attr)
set_parser.add_argument('attr', type=str, help='The attribute to set')
set_parser.add_argument('val', type=str, help='the value to set the attribute to')

toggle_parser = subparsers.add_parser('tog', help='toggles the value of a desired attribute between two states')
toggle_parser.set_defaults(func=__toggle_attr)
toggle_parser.add_argument('attr', type=str, help='The attribute to toggle')
toggle_parser.add_argument('val1', type=str, help='the first value to toggle between')
toggle_parser.add_argument('val2', type=str, help='the second value to toggle between')

global_parser.add_argument('monitor', type=str, help='The name of the monitor to control')


def run(args):
    args = global_parser.parse_args(args)
    args.func(args)

    return args.out
