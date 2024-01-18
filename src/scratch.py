#!/usr/bin/env python3

from cli import run

# line = "tog vcp DP2 USBC right"
# line = "get vcp 2"
# line = "set vcp shit 0"
line = "list"

args = line.split()
run(args)
