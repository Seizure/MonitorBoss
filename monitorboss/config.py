import configparser

config = configparser.ConfigParser()

print(os.getcwd())

# TODO: make the monitor setup configurable.
# Seizure's three monitors are hard-coded.

monitor_names = {"LEFT": 2, "MIDDLE": 1, "RIGHT": 0}

# TODO: make input source codes configurable.
# Seizure's Dell monitor's USB-C source has code 27. No idea how consistent this is.
input_source_names = {"USBC": 27}
