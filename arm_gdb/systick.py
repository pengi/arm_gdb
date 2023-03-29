# SPDX-FileCopyrightText: 2023 Max Sikström
# SPDX-License-Identifier: MIT

# Copyright © 2023 Max Sikström
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the “Software”), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import gdb
import argparse
from .common import *


class ArmToolsSysTick (gdb.Command):
    """Dump of ARM SysTick"""

    # https://developer.arm.com/documentation/dui0552/a/cortex-m3-peripherals/system-timer--systick
    regs = [
        RegisterDef("SYST_CSR", "SysTick Control and Status Register", 0xE000E010, 4, [
            FieldBitfield("ENABLE", 0, 1),
            FieldBitfield("TICKINT", 1, 1),
            FieldBitfield("CLKSOURCE", 2, 1),
            FieldBitfield("COUNTFLAG", 16, 1)
        ]),
        RegisterDef("SYST_RVR", "SysTick Reload Value Register", 0xE000E014, 4, [
            FieldBitfield("RELOAD", 0, 24)
        ]),
        RegisterDef("SYST_CVR", "SysTick Current Value Register", 0xE000E018, 4, [
            FieldBitfield("CURRENT", 0, 24)
        ]),
        RegisterDef("SYST_CALIB", "SysTick Calibration Value Register", 0xE000E01C, 4, [
            FieldBitfield("TENMS", 0, 25),
            FieldBitfield("SKEW", 30, 1),
            FieldBitfield("NOREF", 31, 1)
        ]),
    ]

    def __init__(self):
        super().__init__('arm systick', gdb.COMMAND_USER)
        self.parser = argparse.ArgumentParser(
            description="Inspect SysTick"
        )
        self.parser.add_argument(
            '-d', '--descr',
            dest='descr',
            action='store_const',
            const=True,
            default=False,
            help="Include description"
        )

    def invoke(self, argument, from_tty):
        argv = gdb.string_to_argv(argument)
        try:
            args = self.parser.parse_args(argv)
        except SystemExit:
            # We're running argparse in gdb, don't exit just return
            return

        inf = gdb.selected_inferior()
        for reg in self.regs:
            reg.dump(inf, args.descr)
