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
from .common import *


class ArmToolsSysTick (gdb.Command):
    """Dump of ARM SysTick"""

    # https://developer.arm.com/documentation/dui0552/a/cortex-m3-peripherals/system-timer--systick
    regs = [
        RegisterDefBitfield("SYST_CSR", "SysTick Control and Status Register", 0xE000E010, 4, [
            (0, 1, "ENABLE"),
            (1, 1, "TICKINT"),
            (2, 1, "CLKSOURCE"),
            (16, 1, "COUNTFLAG")
        ]),
        RegisterDefBitfield("SYST_RVR", "SysTick Reload Value Register", 0xE000E014, 4, [
            (0, 24, "RELOAD")
        ]),
        RegisterDefBitfield("SYST_CVR", "SysTick Current Value Register", 0xE000E018, 4, [
            (0, 24, "CURRENT")
        ]),
        RegisterDefBitfield("SYST_CALIB", "SysTick Calibration Value Register", 0xE000E01C, 4, [
            (0, 25, "TENMS"),
            (30, 1, "SKEW"),
            (31, 1, "NOREF")
        ]),
    ]

    def __init__(self):
        super().__init__('arm systick', gdb.COMMAND_USER)

    def invoke(self, argument, from_tty):
        inf = gdb.selected_inferior()
        for reg in self.regs:
            reg.dump(inf)
