#!/usr/bin/env python3

from cli import run

from config import reset_config

reset_config()

# line = "tog src DP1 USBC right"
# line = "get vcp 2"
# line = "set vcp shit 0"
line = "list -h"

args = line.split()
run(args)
