#!/usr/bin/env python3

from logging import basicConfig, DEBUG
from sys import stdout

from monitorboss.cli import run

if __name__ == "__main__":
    basicConfig(level=DEBUG, stream=stdout)
    run()
