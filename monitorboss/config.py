import configparser
import os

from impl import MonitorBossError

CONF_FILE_LOC = "./conf/MonitorBoss.conf"

DEFAULT_CONF_CONTENT = \
"""###########
# stores a list of aliases
# corresponding to monitor IDs
###########
[MONITOR_NAMES]
RIGHT = 0
MIDDLE = 1
LEFT = 2

###########
# stores a list of aliases
# corresponding to non-spec source codes
###########
[INPUT_NAMES]
USBC = 27 # 27 seems to be the "standard non-standard" ID for USB-C among manufacturers"""

# these get populated by the config parser
monitor_names = {}
input_source_names = {}

config = configparser.ConfigParser(inline_comment_prefixes="#")
config.optionxform = str  # stop changing the case of our keys, you bastards

config.read_file(open(CONF_FILE_LOC))

# populate monitor names
for k in config['MONITOR_NAMES'].keys():
    monitor_names[k] = int(config['MONITOR_NAMES'][k])

# populate input source names
for k in config['INPUT_NAMES'].keys():
    input_source_names[k] = int(config['INPUT_NAMES'][k])


def reset_conf():
    if os.path.exists(CONF_FILE_LOC):
        try:
            os.remove(CONF_FILE_LOC)
        except:
            raise MonitorBossError(f"{CONF_FILE_LOC} is not a file. Aborting. Please investigate manually and delete"
                                   f"the item so that MonitorBoss can rebuild the conf")

        conf = open(CONF_FILE_LOC, "x")

        conf.write(DEFAULT_CONF_CONTENT)

        conf.close()
