from monitorboss.config import Config
from pyddc import VCPCommand
from pyddc.vcp_codes import VCPCodes


# TODO: originally included cfg in expectation of including feature aliases, but now I'm not sure we should?
#   maybe this should return a tuple of strings with varying degrees of extra information,
#   and you can determine how much of said information to use depending on verbosity?
#   Alternatively, might be time to entirely change the general formatting of the return texts to be multiline
#   so that including all the aliases won't be cumbersome to visually parse by a human
def feature_str(com: VCPCommand, cfg: Config) -> str:
    return f"{com.name} ({com.value})"


def monitor_str(mon: int, cfg: Config) -> str:
    monstr = f"monitor #{mon} "
    aliases = ""
    for v, k in cfg.monitor_names.items():
        if mon == k:
            aliases += v+", "
    if aliases:
        monstr += f"({aliases[:-2]})"

    return monstr.strip()


def value_str(com: VCPCommand, value: int, cfg: Config) -> str:
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
