#!/usr/bin/env python3

from logging import basicConfig, DEBUG, INFO
from sys import stdout

from monitorboss.cli import run

def main():
    basicConfig(level=INFO, stream=stdout)
    run()

if __name__ == "__main__":
    main()
