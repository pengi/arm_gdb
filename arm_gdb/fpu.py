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
import traceback

# https://developer.arm.com/documentation/ddi0403/latest/

def get_fpu_regs():
    return [
        RegisterDef("FPCCR", "Floating Point Context Control Register", 0xE000EF34, 4, [
            FieldBitfield("ASPEN",  31, 1,
                          "When this bit is set to 1, execution of a floating-point instruction sets the CONTROL.FPCA bit to 1"),
            FieldBitfield("LSPEN",  30, 1,
                          "Enables lazy context save of FP state"),
            FieldBitfield("MONRDY",  8, 1,
                          "Indicates whether the software executing when the processor allocated the FP stack frame was able to set the DebugMonitor exception to pending"),
            FieldBitfield("BFRDY",   6, 1,
                          "Indicates whether the software executing when the processor allocated the FP stack frame was able to set the BusFault exception to pending"),
            FieldBitfield("MMRDY",   5, 1,
                          "Indicates whether the software executing when the processor allocated the FP stack frame was able to set the MemManage exception to pending"),
            FieldBitfield("HFRDY",   4, 1,
                          "Indicates whether the software executing when the processor allocated the FP stack frame was able to set the HardFault exception to pending"),
            FieldBitfield("THREAD",  3, 1,
                          "Indicates the processor mode when it allocated the FP stack frame"),
            FieldBitfield("USER",    1, 1,
                          "Indicates the privilege level of the software executing when the processor allocated the FP stack frame"),
            FieldBitfield("LSPACT",  0, 1,
                          "Indicates whether Lazy preservation of the FP state is active"),
        ]),
        RegisterDef("FPCAR", "Floating Point Context Address Register", 0xE000EF38, 4, [
            FieldBitfield("FPCAR", 2, 28,
                          "The location of the unpopulated floating-point register space allocated on an exception stack frame.")
        ]),
        RegisterDef("FPDSCR", "Floating Point Default Status Control Register", 0xE000EF3C, 4, [
            FieldBitfield("AHP",   26, 1, "Default value for FPSCR.AHP"),
            FieldBitfield("DN",    25, 1, "Default value for FPSCR.DN"),
            FieldBitfield("FZ",    24, 1, "Default value for FPSCR.FZ"),
            FieldBitfield("RMode", 22, 2, "Default value for FPSCR.RMode"),
        ]),
        RegisterDef("MVFR0", "Media and FP Feature Register 0", 0xE000EF40, 4, [
            FieldBitfieldEnum("FP rounding modes", 28, 4, [
                (0b0000, True, "Not supported", None),
                (0b0001, True, "All rounding modes supported.", None),
            ], "Indicates the rounding modes supported by the FP floating-point hardware."),
            FieldBitfieldEnum("Short vectors", 24, 4, [
                (0b0000, True, "Not supported", None),
                (0b0001, False, "Supported", None)
            ]),
            FieldBitfieldEnum("Square root", 20, 4, [
                (0b0000, True, "Not supported", None),
                (0b0001, False, "Supported", None)
            ]),
            FieldBitfieldEnum("Divide", 16, 4, [
                (0b0000, True, "Not supported", None),
                (0b0001, False, "Supported", None)
            ]),
            FieldBitfieldEnum("FP exception trapping", 12, 4, [
                (0b0000, True, "Not supported", None),
            ]),
            FieldBitfieldEnum("Double-precision",  8, 4, [
                (0b0000, True, "Not supported", None),
                (0b0010, False, "Supported", None)
            ]),
            FieldBitfieldEnum("Single-precision",  4, 4, [
                (0b0000, True, "Not supported", None),
                (0b0010, False, "Supported.",
                 "FP adds an instruction to load a single-precision floating-point constant, and conversions between single-precision and fixed-point values."),
            ], "Indicates the hardware support for FP single-precision operations."),
            FieldBitfieldEnum("A_SIMD registers",  0, 4, [
                (0b0000, True, "Not supported", None),
                (0b0001, False, "Supported, 16 x 64-bit registers.", None),
            ]),
        ]),
        RegisterDef("MVFR1", "Media and FP Feature Register 1", 0xE000EF44, 4, [
            FieldBitfieldEnum("FP fused MAC", 28, 4, [
                (0b0000, True, "Not supported", None),
                (0b0001, False, "Supported", None)
            ]),
            FieldBitfieldEnum("FP HPFP", 24, 4, [
                (0b0000, True, "Not supported", None),
                (0b0001, False, "Supported half-single",
                 "Supports conversion between half-precision and single-precision."),
                (0b0010, False, "Supported half-single-double",
                 "Supports conversion between half-precision and single-precision0b0001, and also supports conversion between half-precision and double-precision."),
            ], "Floating Point half-precision and double-precision. Indicates whether the FP extension implements half-precision and double-precision floating-point conversion instructions."),
            FieldBitfieldEnum("D_NaN mode",  4, 4, [
                (0b0000, True, "Not supported", None),
                (0b0001, False, "Hardware supports propagation of NaN values.", None),
            ], "Indicates whether the FP hardware implementation supports only the Default NaN mode."),
            FieldBitfieldEnum("FtZ mode",  0, 4, [
                (0b0000, True, "Not supported", None),
                (0b0001, False, "Hardware supports full denormalized number arithmetic.", None),
            ], "Indicates whether the FP hardware implementation supports only the Flush-to-zero mode of operation."),
        ]),
        RegisterDef("MVFR2", "Media and FP Feature Register 2", 0xE000EF48, 4, [
            FieldBitfieldEnum("VFP_Misc",  4, 4, [
                (0b0000, True, "No support for miscellaneous features.", None),
                (0b0100, False, "Support for miscellaneous features.",
                 "Support for floating-point selection, floating-point conversion to integer with direct rounding modes, floating-point round to integral floating-point, and floating-point maximum number and minimum number."),
            ], "Indicates the hardware support for FP miscellaneous features"),
        ]),
    ]


class ArmToolsFPU (ArgCommand):
    """Dump of ARM Cortex-M FPU - SCB registers for the FP extension

Usage: arm fpu [/hab]

Modifier /h provides descriptions of names where available
Modifier /a Print all fields, including default values
Modifier /b prints bitmasks in binary instead of hex
"""

    def __init__(self):
        super().__init__('arm fpu', gdb.COMMAND_DATA)
        self.add_mod('h', 'descr')
        self.add_mod('a', 'all')
        self.add_mod('b', 'binary')

    def invoke(self, argument, from_tty):
        args = self.process_args(argument)
        if args is None:
            self.print_help()
            return

        base = 1 if args['binary'] else 4

        inf = gdb.selected_inferior()

        print("SCB FP registers:")

        try:
            regs = get_fpu_regs()
        except:
            traceback.print_exc()

        for reg in regs:
            reg.dump(inf, args['descr'], base=base, all=args['all'])
