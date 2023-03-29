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


class ArmToolsSCB (gdb.Command):
    """Dump of ARM SCB"""

    # https://developer.arm.com/documentation/dui0552/a/cortex-m3-peripherals/system-control-block
    regs = [
        RegisterDef("ACTLR", "Auxiliary Control Register", 0xE000E008, 4, [
            FieldBitfield("DISMCYCINT", 0, 1),
            FieldBitfield("DISDEFWBUF", 1, 1),
            FieldBitfield("DISFOLD", 2, 1)
        ]),
        RegisterDef("CPUID", "CPUID Base Register", 0xE000ED00, 4, [
            FieldBitfield("Revision", 0, 4),
            FieldBitfield("PartNo", 4, 12),
            FieldBitfield("Constant", 16, 4),
            FieldBitfield("Variant", 20, 4),
            FieldBitfield("Implementer", 24, 8)
        ]),
        RegisterDef("ICSR", "Interrupt Control and State Register", 0xE000ED04, 4, [
            FieldBitfield("VECTACTIVE", 0, 8),
            FieldBitfield("RETTOBASE", 11, 1),
            FieldBitfield("VECTPENDING", 12, 6),
            FieldBitfield("ISRPENDING", 22, 1),
            FieldBitfield("Reserved for Debug use", 23, 1),
            FieldBitfield("PENDSTCLR", 25, 1),
            FieldBitfield("PENDSTSET", 26, 1),
            FieldBitfield("PENDSVSET", 28, 1),
            FieldBitfield("NMIPENDSET", 31, 1)
        ]),
        RegisterDef("VTOR", "Vector Table Offset Register", 0xE000ED08, 4, [
            FieldBitfield("TBLOFF", 7, 25)
        ]),
        RegisterDef("AIRCR", "Application Interrupt and Reset Control Register", 0xE000ED0C, 4, [
            FieldBitfield("VECTRESET", 0, 1),
            FieldBitfield("VECTCLRACTIVE", 1, 1),
            FieldBitfield("SYSRESETREQ", 2, 1),
            FieldBitfield("PRIGROUP", 8, 3),
            FieldBitfield("ENDIANNESS", 15, 1),
            FieldBitfield("VECTKEY", 16, 16)
        ]),
        RegisterDef("SCR", "System Control Register", 0xE000ED10, 4, [
            FieldBitfield("SLEEPONEXIT", 1, 1),
            FieldBitfield("SLEEPDEEP", 2, 1),
            FieldBitfield("SEVONPEND", 4, 1)
        ]),
        RegisterDef("CCR", "Configuration and Control Register", 0xE000ED14, 4, [
            FieldBitfield("NONBASETHRDENA", 0, 1),
            FieldBitfield("USERSETMPEND", 1, 1),
            FieldBitfield("UNALIGN_TRP", 3, 1),
            FieldBitfield("DIV_0_TRP", 4, 1),
            FieldBitfield("BFHFNMIGN", 8, 1),
            FieldBitfield("STKALIGN", 9, 1)
        ]),
        RegisterDef("SHPR1", "System Handler Priority Register 1", 0xE000ED18, 4, [
            FieldBitfield("PRI_4 - MemManage", 0, 8),
            FieldBitfield("PRI_5 - BusFault", 8, 8),
            FieldBitfield("PRI_6 - UsageFault", 16, 8),
            FieldBitfield("PRI_7", 24, 8)
        ]),
        RegisterDef("SHPR2", "System Handler Priority Register 2", 0xE000ED1C, 4, [
            FieldBitfield("PRI_8", 0, 8),
            FieldBitfield("PRI_9", 8, 8),
            FieldBitfield("PRI_10", 16, 8),
            FieldBitfield("PRI_11 - SVCall", 24, 8)
        ]),
        RegisterDef("SHPR3", "System Handler Priority Register 3", 0xE000ED20, 4, [
            FieldBitfield("PRI_12", 0, 8),
            FieldBitfield("PRI_13", 8, 8),
            FieldBitfield("PRI_14 - PendSV", 16, 8),
            FieldBitfield("PRI_15 - SysTick", 24, 8)
        ]),
        RegisterDef("SHCRS", "System Handler Control and State Register", 0xE000ED24, 4, [
            FieldBitfield("MEMFAULTACT", 0, 1),
            FieldBitfield("BUSFAULTACT", 1, 1),
            FieldBitfield("USGFAULTACT", 3, 1),
            FieldBitfield("SVCALLACT", 7, 1),
            FieldBitfield("MONITORACT", 8, 1),
            FieldBitfield("PENDSVACT", 10, 1),
            FieldBitfield("SYSTICKACT", 11, 1),
            FieldBitfield("USGFAULTPENDED", 12, 1),
            FieldBitfield("MEMFAULTPENDED", 13, 1),
            FieldBitfield("BUSFAULTPENDED", 14, 1),
            FieldBitfield("SVCALLPENDED", 15, 1),
            FieldBitfield("MEMFAULTENA", 16, 1),
            FieldBitfield("BUSFAULTENA", 17, 1),
            FieldBitfield("USGFAULTENA", 18, 1),
        ]),
        RegisterDef("CFSR", "Configurable Fault Status Register", 0xE000ED28, 4),
        RegisterDef("MMFSR", "MemManage Fault Status Register", 0xE000ED28, 1, [
            FieldBitfield("IACCVIOL", 0, 1),
            FieldBitfield("DACCVIOL", 1, 1),
            FieldBitfield("MUNSTKERR", 3, 1),
            FieldBitfield("MSTKERR", 4, 1),
            FieldBitfield("MLSPERR", 5, 1),
            FieldBitfield("MMARVALID", 7, 1)
        ]),
        RegisterDef("MMFAR", "MemManage Fault Address Register",
                    0xE000ED34, 4),
        RegisterDef("BFSR", "BusFault Status Register", 0xE000ED29, 1, [
            FieldBitfield("IBUSERR", 0, 1),
            FieldBitfield("PRECISERR", 1, 1),
            FieldBitfield("IMPRECISERR", 2, 1),
            FieldBitfield("UNSTKERR", 3, 1),
            FieldBitfield("STKERR", 4, 1),
            FieldBitfield("LSPERR", 5, 1),
            FieldBitfield("BFARVALID", 7, 1)
        ]),
        RegisterDef("BFAR", "BusFault Address Register", 0xE000ED38, 4),
        RegisterDef("UFSR", "UsageFault Status Register", 0xE000ED2A, 2, [
            FieldBitfield("UNDEFINSTR", 0, 1),
            FieldBitfield("INVSTATE", 1, 1),
            FieldBitfield("INVPC", 2, 1),
            FieldBitfield("NOCP", 3, 1),
            FieldBitfield("UNALIGNED", 8, 1),
            FieldBitfield("DIVBYZERO", 9, 1)
        ]),
        RegisterDef("HFSR", "HardFault Status Register", 0xE000ED2C, 4, [
            FieldBitfield("VECTTBL", 1, 1),
            FieldBitfield("FORCED", 30, 1),
            FieldBitfield("DEBUGEVT", 31, 1)
        ]),
        RegisterDef("AFSR", "Auxiliary Fault Status Register", 0xE000ED3C, 4)
    ]

    def __init__(self):
        super().__init__('arm scb', gdb.COMMAND_USER)
        self.parser = argparse.ArgumentParser(
            description="Inspect SCB - System Control Block"
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
