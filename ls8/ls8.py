#!/usr/bin/env python3

"""Main."""

import sys
from cpu import *

cpu = CPU()

print(sys.argv[1])

# Load filename into CPU
cpu.load()
cpu.run()