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


class ArmToolsSCB (gdb.Command):
    """Dump of ARM SCB"""

    # https://developer.arm.com/documentation/dui0552/a/cortex-m3-peripherals/system-control-block
    regs = [
        RegisterDefBitfield("ACTLR", "Auxiliary Control Register", 0xE000E008, 4, [
            (0, 1, "DISMCYCINT"),
            (1, 1, "DISDEFWBUF"),
            (2, 1, "DISFOLD")
        ]),
        RegisterDefBitfield("CPUID", "CPUID Base Register", 0xE000ED00, 4, [
            (0, 4, "Revision"),
            (4, 12, "PartNo"),
            (16, 4, "Constant"),
            (20, 4, "Variant"),
            (24, 8, "Implementer")
        ]),
        RegisterDefBitfield("ICSR", "Interrupt Control and State Register", 0xE000ED04, 4, [
            (0, 8, "VECTACTIVE"),
            (11, 1, "RETTOBASE"),
            (12, 6, "VECTPENDING"),
            (22, 1, "ISRPENDING"),
            (23, 1, "Reserved for Debug use"),
            (25, 1, "PENDSTCLR"),
            (26, 1, "PENDSTSET"),
            (28, 1, "PENDSVSET"),
            (31, 1, "NMIPENDSET")
        ]),
        RegisterDefBitfield("VTOR", "Vector Table Offset Register", 0xE000ED08, 4, [
            (7, 25, "TBLOFF")
        ]),
        RegisterDefBitfield("AIRCR", "Application Interrupt and Reset Control Register", 0xE000ED0C, 4, [
            (0, 1, "VECTRESET"),
            (1, 1, "VECTCLRACTIVE"),
            (2, 1, "SYSRESETREQ"),
            (8, 3, "PRIGROUP"),
            (15, 1, "ENDIANNESS"),
            (16, 16, "VECTKEY")
        ]),
        RegisterDefBitfield("SCR", "System Control Register", 0xE000ED10, 4, [
            (1, 1, "SLEEPONEXIT"),
            (2, 1, "SLEEPDEEP"),
            (4, 1, "SEVONPEND")
        ]),
        RegisterDefBitfield("CCR", "Configuration and Control Register", 0xE000ED14, 4, [
            (0, 1, "NONBASETHRDENA"),
            (1, 1, "USERSETMPEND"),
            (3, 1, "UNALIGN_TRP"),
            (4, 1, "DIV_0_TRP"),
            (8, 1, "BFHFNMIGN"),
            (9, 1, "STKALIGN")
        ]),
        RegisterDefBitfield("SHPR1", "System Handler Priority Register 1", 0xE000ED18, 4, [
            (0, 8, "PRI_4 - MemManage"),
            (8, 8, "PRI_5 - BusFault"),
            (16, 8, "PRI_6 - UsageFault"),
            (24, 8, "PRI_7")
        ]),
        RegisterDefBitfield("SHPR2", "System Handler Priority Register 2", 0xE000ED1C, 4, [
            (0, 8, "PRI_8"),
            (8, 8, "PRI_9"),
            (16, 8, "PRI_10"),
            (24, 8, "PRI_11 - SVCall")
        ]),
        RegisterDefBitfield("SHPR3", "System Handler Priority Register 3", 0xE000ED20, 4, [
            (0, 8, "PRI_12"),
            (8, 8, "PRI_13"),
            (16, 8, "PRI_14 - PendSV"),
            (24, 8, "PRI_15 - SysTick")
        ]),
        RegisterDefBitfield("SHCRS", "System Handler Control and State Register", 0xE000ED24, 4, [
            (0, 1, "MEMFAULTACT"),
            (1, 1, "BUSFAULTACT"),
            (3, 1, "USGFAULTACT"),
            (7, 1, "SVCALLACT"),
            (8, 1, "MONITORACT"),
            (10, 1, "PENDSVACT"),
            (11, 1, "SYSTICKACT"),
            (12, 1, "USGFAULTPENDED"),
            (13, 1, "MEMFAULTPENDED"),
            (14, 1, "BUSFAULTPENDED"),
            (15, 1, "SVCALLPENDED"),
            (16, 1, "MEMFAULTENA"),
            (17, 1, "BUSFAULTENA"),
            (18, 1, "USGFAULTENA"),
        ]),
        RegisterDef("CFSR", "Configurable Fault Status Register",
                    0xE000ED28, 4),
        RegisterDefBitfield("MMFSR", "MemManage Fault Status Register", 0xE000ED28, 1, [
            (0, 1, "IACCVIOL"),
            (1, 1, "DACCVIOL"),
            (3, 1, "MUNSTKERR"),
            (4, 1, "MSTKERR"),
            (5, 1, "MLSPERR"),
            (7, 1, "MMARVALID")
        ]),
        RegisterDef("MMFAR", "MemManage Fault Address Register",
                    0xE000ED34, 4),
        RegisterDefBitfield("BFSR", "BusFault Status Register", 0xE000ED29, 1, [
            (0, 1, "IBUSERR"),
            (1, 1, "PRECISERR"),
            (2, 1, "IMPRECISERR"),
            (3, 1, "UNSTKERR"),
            (4, 1, "STKERR"),
            (5, 1, "LSPERR"),
            (7, 1, "BFARVALID")
        ]),
        RegisterDef("BFAR", "BusFault Address Register", 0xE000ED38, 4),
        RegisterDefBitfield("UFSR", "UsageFault Status Register", 0xE000ED2A, 2, [
            (0, 1, "UNDEFINSTR"),
            (1, 1, "INVSTATE"),
            (2, 1, "INVPC"),
            (3, 1, "NOCP"),
            (8, 1, "UNALIGNED"),
            (9, 1, "DIVBYZERO")
        ]),
        RegisterDefBitfield("HFSR", "HardFault Status Register", 0xE000ED2C, 4, [
            (1, 1, "VECTTBL"),
            (30, 1, "FORCED"),
            (31, 1, "DEBUGEVT")
        ]),
        RegisterDef("AFSR", "Auxiliary Fault Status Register", 0xE000ED3C, 4)
    ]

    def __init__(self):
        super().__init__('arm scb', gdb.COMMAND_USER)

    def invoke(self, argument, from_tty):
        inf = gdb.selected_inferior()
        for reg in self.regs:
            reg.dump(inf)
