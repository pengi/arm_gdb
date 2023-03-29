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


class ArmToolsNVIC (gdb.Command):
    """Dump of ARM NVIC"""

    # Numbers represents bit numbers in control regiters for:
    # (enabled, active, pedning)
    # Bit numbers   0- 31 represents SHCRS    (System Handler Control and State Register)
    # Bit numbers 100-131 represents SYST_CSR (SysTick)
    # If a static value, either False or True can be used instead.
    # followed by name of the interrupt
    nonmask_map = [
        (True,  False, False, "Reset"),
        (True,  False, False, "NMI"),
        (True,  False, False, "HardFault"),
        (16, 0, 13, "MemManage"),
        (17, 1, 14, "BusFault"),
        (18, 3, 12, "UsageFault"),
        (False, False, False, ""),
        (False, False, False, ""),
        (False, False, False, ""),
        (False, False, False, ""),
        (True,  7, 15, "SVC"),
        (False,  8, False, "DebugMon"),
        (False, False, False, ""),
        (True,  10, False, "PendSV"),
        (100,  11, False, "SysTick"),
    ]

    # https://developer.arm.com/documentation/dui0552/a/cortex-m3-peripherals/nested-vectored-interrupt-controller

    def __init__(self):
        super().__init__('arm nvic', gdb.COMMAND_USER)

        self.parser = argparse.ArgumentParser(
            description="Get NVIC parameters"
        )
        self.parser.add_argument('-a', '--all',
                                 action='store_const',
                                 const=True,
                                 default=False,
                                 dest='all',
                                 help='Show all, and not only enabled'
                                 )

        self.parser.add_argument('-N', '--count',
                                 action='store',
                                 dest='count',
                                 metavar='N',
                                 help='Number of ISR vectors',
                                 default=240,
                                 type=lambda s: int(s, 0)
                                 )

        self.parser.add_argument('-V', '--vtor',
                                 action='store',
                                 dest='vtor',
                                 metavar='ADDR',
                                 help='Alternative interrupt vector address',
                                 default=None,
                                 type=gdb.parse_and_eval
                                 )

    def get_bit(self, IRQn, REG):
        return (REG[IRQn // 32] & (1 << (IRQn % 32))) != 0

    def invoke(self, argument, from_tty):
        argv = gdb.string_to_argv(argument)
        try:
            args = self.parser.parse_args(argv)
        except SystemExit:
            # We're running argparse in gdb, don't exit just return
            return

        inf = gdb.selected_inferior()

        if args.vtor:
            VTOR = args.vtor
        else:
            # Vector Table Offset Register
            VTOR = read_reg(inf, 0xE000ED08, 4)
            STIR = read_reg(inf, 0xE000E010, 4)

        # Maskable handlers
        SHPR = [read_reg(inf, 0xE000ED18 + 4*i, 4) for i in range(3)]

        # Status registers
        status_regs = [
            read_reg(inf, 0xE000ED24, 4),  # SHCRS
            read_reg(inf, 0xE000E010, 4),  # SYST_CSR
        ]

        NVIC_ISER = [read_reg(inf, 0xE000E100 + 4*i, 4) for i in range(8)]
        # NVIC_ICER = [read_reg(inf, 0XE000E180 + 4*i, 4) for i in range(8)]
        NVIC_ISPR = [read_reg(inf, 0XE000E200 + 4*i, 4) for i in range(8)]
        # NVIC_ICPR = [read_reg(inf, 0XE000E280 + 4*i, 4) for i in range(8)]
        NVIC_IABR = [read_reg(inf, 0xE000E300 + 4*i, 4) for i in range(8)]
        NVIC_IPR = [read_reg(inf, 0xE000E400 + 4*i, 4) for i in range(60)]

        print("IRQn Prio          Handler")

        for IRQn in range(-15, args.count):
            handler_addr = read_reg(inf, VTOR + 4*(16+IRQn), 4)
            handler_func = gdb.block_for_pc(handler_addr)
            if handler_func is None:
                handler_name = ""
            elif handler_func.function is None:
                handler_name = "-"
            else:
                handler_name = str(handler_func.function)

            if IRQn < 0:
                # Maskable
                (enabled, active, pending, name) = self.nonmask_map[IRQn+15]
                if type(enabled) == int:
                    enabled = (status_regs[enabled//100]
                               & (1 << (enabled % 100))) != 0
                if type(active) == int:
                    active = (status_regs[active//100]
                              & (1 << (active % 100))) != 0
                if type(pending) == int:
                    pending = (status_regs[pending//100]
                               & (1 << (pending % 100))) != 0

                # Names are only defined for IRQn < 0, so make sure they align here
                name = "%-11s" % (name,)

                if IRQn < -12:
                    prio = 0
                else:
                    prio = (SHPR[(IRQn+12)//4] >>
                            (8*((IRQn+12) % 4))) & 0xff
            else:
                # IRQ
                enabled = self.get_bit(IRQn, NVIC_ISER)
                # active = self.get_bit(IRQn, NVIC_ICER)
                pending = self.get_bit(IRQn, NVIC_ISPR)
                # active = self.get_bit(IRQn, NVIC_ICPR)
                active = self.get_bit(IRQn, NVIC_IABR)
                name = ""
                prio = (NVIC_IPR[IRQn//4] >> (8*(IRQn % 4))) & 0xff

            if enabled or args.all:
                print("%4d %4x %s %s %s %08x %s%s" % (
                    IRQn,
                    prio,
                    "en" if enabled else "  ",
                    "pend" if pending else "    ",
                    "act" if active else "   ",
                    handler_addr,
                    name,
                    handler_name
                ))
