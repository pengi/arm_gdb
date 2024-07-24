# SPDX-FileCopyrightText: 2023 Max Sikström
# SPDX-License-Identifier: MIT

# Copyright © 2023 Max Sikström
# Copyright © 2023 Niklas Hauser
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

# MPU is part of ARMv8-M specification. Other architectures are not supported,
# since they are implementation defined.

# Architecture reference manuals:
#
# ARMv8-M https://developer.arm.com/documentation/ddi0553/latest/
#

def get_mpu_common_regs(model):
    def mair_attr_fields(num, offset):
        return [
            FieldBitfieldEnum(f"Outer {num}", offset + 4, 4, [
                (0b0000, None, "Device Memory", None),
                (0b0001, None, "Normal Memory, Outer Write-Through transient, Allocate W", None),
                (0b0010, None, "Normal Memory, Outer Write-Through transient, Allocate R", None),
                (0b0011, None, "Normal Memory, Outer Write-Through transient, Allocate RW", None),
                (0b0100, None, "Normal Memory, Outer Non-cacheable", None),
                (0b0101, None, "Normal Memory, Outer Write-Back Transient, Allocate W", None),
                (0b0110, None, "Normal Memory, Outer Write-Back Transient, Allocate R", None),
                (0b0111, None, "Normal Memory, Outer Write-Back Transient, Allocate RW", None),
                (0b1000, None, "Normal Memory, Outer Write-Through Non-transient", None),
                (0b1001, None, "Normal Memory, Outer Write-Through Non-transient, Allocate W", None),
                (0b1010, None, "Normal Memory, Outer Write-Through Non-transient, Allocate R", None),
                (0b1011, None, "Normal Memory, Outer Write-Through Non-transient, Allocate RW", None),
                (0b1100, None, "Normal Memory, Outer Write-Back Non-transient", None),
                (0b1101, None, "Normal Memory, Outer Write-Back Non-transient, Allocate W", None),
                (0b1110, None, "Normal Memory, Outer Write-Back Non-transient, Allocate R", None),
                (0b1111, None, "Normal Memory, Outer Write-Back Non-transient, Allocate RW", None),
            ], "Outer attributes. Specifies the Outer memory attributes."),
            FieldConditional(lambda value: value & (0xf0 << offset) == 0,
                FieldBitfieldEnum(f"Device {num}", offset + 2, 2, [
                    (0b00, None, "Device-nGnRnE.", None),
                    (0b01, None, "Device-nGnRE.", None),
                    (0b10, None, "Device-nGRE.", None),
                    (0b11, None, "Device-GRE", None),
                ], "Device attributes. Specifies the memory attributes for Device.")
            ),
            FieldConditional(lambda value: value & (0xf0 << offset) != 0,
                FieldBitfieldEnum(f"Inner {num}", offset + 0, 4, [
                    (0b0000, None, "Unpredictable", None),
                    (0b0001, None, "Normal Memory, Inner Write-Through transient, Allocate W", None),
                    (0b0010, None, "Normal Memory, Inner Write-Through transient, Allocate R", None),
                    (0b0011, None, "Normal Memory, Inner Write-Through transient, Allocate RW", None),
                    (0b0100, None, "Normal Memory, Inner Non-cacheable", None),
                    (0b0101, None, "Normal Memory, Inner Write-Back Transient, Allocate W", None),
                    (0b0110, None, "Normal Memory, Inner Write-Back Transient, Allocate R", None),
                    (0b0111, None, "Normal Memory, Inner Write-Back Transient, Allocate RW", None),
                    (0b1000, None, "Normal Memory, Inner Write-Through Non-transient", None),
                    (0b1001, None, "Normal Memory, Inner Write-Through Non-transient, Allocate W", None),
                    (0b1010, None, "Normal Memory, Inner Write-Through Non-transient, Allocate R", None),
                    (0b1011, None, "Normal Memory, Inner Write-Through Non-transient, Allocate RW", None),
                    (0b1100, None, "Normal Memory, Inner Write-Back Non-transient", None),
                    (0b1101, None, "Normal Memory, Inner Write-Back Non-transient, Allocate W", None),
                    (0b1110, None, "Normal Memory, Inner Write-Back Non-transient, Allocate R", None),
                    (0b1111, None, "Normal Memory, Inner Write-Back Non-transient, Allocate RW", None),
                ], "Inner attributes. Specifies the Inner memory attributes.")
            ),
        ]
    return [
        RegisterDef("MPU_TYPE", "MPU Type Register", 0xE000ED90, 4, [
            FieldBitfield("DREGION",  8, 8,
                        "Number of regions supported by the MPU."),
            FieldBitfield("SEPARATE",  0, 1,
                        "Indicates support for separate instructions and data address regions"),
        ]),
        RegisterDef("MPU_CTRL", "MPU Control Register", 0xE000ED94, 4, [
            FieldBitfield("PRIVDEFENA", 2, 1,
                        "Privileged default enable. Controls whether the system address map is enabled for privileged software"),
            FieldBitfield("HFNMIENA", 1, 1,
                        "HardFault, NMI enable. Controls whether handlers executing with a requested execution priority of less than 0 access memory with the MPU enabled or disabled"),
            FieldBitfield("ENABLE", 0, 1,
                        "Enable. Enables the MPU."),
        ]),
        RegisterDef("MPU_RNR", "MPU Region Number Register", 0xE000ED98, 4, [
            FieldBitfield("REGION", 0, 8,
                        "Region number. Indicates the memory region accessed by MPU_RBAR and MPU_RLAR."),
        ]),
        RegisterDef("MPU_MAIR0", "MPU Memory Attribute Indirection Register 0", 0xE000EDC0, 4,
                    mair_attr_fields(0, 0) +
                    mair_attr_fields(1, 8) + 
                    mair_attr_fields(2, 16) + 
                    mair_attr_fields(3, 24)
        ),
        RegisterDef("MPU_MAIR1", "MPU Memory Attribute Indirection Register 0", 0xE000EDC4, 4,
                    mair_attr_fields(4, 0) +
                    mair_attr_fields(6, 16) + 
                    mair_attr_fields(5, 8) + 
                    mair_attr_fields(7, 24)
        )
    ]

def get_mpu_region_regs(model):
    return [
        RegisterDef(f"MPU_RBAR", f"MPU Region Base Address Register", 0xE000ED9C, 4, [
            FieldBitfieldMap("BASE", 5, 27, lambda x: format_int(x << 5, 32),
                        "Base address. Contains bits [31:5] of the lower inclusive limit of the selected MPU memory region"),
            FieldBitfieldEnum("SH", 3, 2, [
                            (0b00, False, "Non-shareable.", None),
                            (0b01, False, "Invalid", None),
                            (0b10, False, "Outer Shareable.", None),
                            (0b11, False, "Inner Shareable.", None),
                        ],
                        "Shareability. Defines the Shareability domain of this region for Normal memory."),
            FieldBitfieldEnum("AP", 1, 2, [
                            (0b00, False, "Read/write by privileged code only.", None),
                            (0b01, False, "Read/write by any privilege level.", None),
                            (0b10, False, "Read-only by privileged code only.", None),
                            (0b11, False, "Read-only by any privilege level.", None),
                        ],
                        "Access permissions. Defines the access permissions for this region."),
            FieldBitfieldEnum("XN", 0, 1, [
                            (0b0, False, "Execution only permitted if read permitted", None),
                            (0b1, False, "Execution not permitted.", None),
                        ],
                        "Execute-never. Defines whether code can be executed from this region"),
        ]),
        RegisterDef(f"MPU_RLAR", f"MPU Region Limit Address Register", 0xE000EDA0, 4, [
            FieldBitfieldMap("LIMIT", 5, 27, lambda x: format_int(x << 5, 32),
                        "Limit address. Contains bits [31:5] of the upper inclusive limit of the selected MPU memory region"),
            FieldBitfieldEnum("PXN", 4, 1, [
                            (0b0, False, "Execution only permitted if read permitted.", None),
                            (0b1, False, "Execution from a privileged mode is not permitted.", None),
                        ],
                        "Privileged execute-never. Defines whether code can be executed from this privileged region."),
            FieldBitfield("AttrIndx", 1, 3,
                        "Attribute index. Associates a set of attributes in the MPU_MAIR0 and MPU_MAIR1 fields."),
            FieldBitfieldEnum("EN", 0, 1, [
                            (0b0, False, "Region disabled.", None),
                            (0b1, False, "Region enabled.", None),
                        ],
                        "Enable. Region enable."),
        ])
    ]

def get_mpu_dregions(inf):
    MPU_TYPE = read_reg(inf, 0xE000ED90, 4)
    return (MPU_TYPE >> 8) & 0xff

def get_mpu_region(inf):
    MPU_RNR = read_reg(inf, 0xE000ED98, 4)
    return (MPU_RNR >> 0) & 0xff

def set_mpu_region(inf, region):
    write_reg(inf, 0xE000ED98, region & 0xff, 4)

def is_mpu_region_enabled(inf):
    MPU_RLAR = read_reg(inf, 0xE000EDA0, 4)
    return ((MPU_RLAR >> 0) & 1) == 1


class ArmToolsMPU (ArgCommand):
    """Dump of ARM Cortex-M MPU - Memory Protection Unit registers

Usage: arm mpu [/habf]

Modifier /h provides descriptions of names where available
Modifier /a Print all fields, including default values and disabled regions
Modifier /b prints bitmasks in binary instead of hex
Modifier /f force printing fields from all Cortex-M models
"""

    def __init__(self):
        super().__init__('arm mpu', gdb.COMMAND_DATA)
        self.add_mod('h', 'descr')
        self.add_mod('a', 'all')
        self.add_mod('b', 'binary')
        self.add_mod('f', 'force')

    def invoke(self, argument, from_tty):
        args = self.process_args(argument)
        if args is None:
            self.print_help()
            return

        try:
            base = 1 if args['binary'] else 4

            inf = gdb.selected_inferior()

            # Detect CPU type, convert to a useful key for dicts
            CPUID = read_reg(inf, 0xE000ED00, 4)
            model = {
                "4100c200": ["M0", "v6"],
                "4100c600": ["M0+", "v6"],
                "4100c210": ["M1", "v6"],
                "4100c230": ["M3", "v7"],
                "4100c240": ["M4", "v7"],
                "4100c270": ["M7", "v7"],
                # TODO: support ARMv8-M, for now pretend it's v7, since it's similar
                "4100d200": ["M23", "v8"],
                "4100d210": ["M33", "v8"],
                "63001320": ["M55", "v8"],
            }.get(format_int(CPUID & 0xff00fff0, 32), None)

            if "v8" not in model and not args['force']:
                print("MPU prinout only supported on ARMv8-M devices")
                return

            print("MPU for Cortex-%s - ARM%s-M" %
                  ((model[0], model[1]) if model else ("XX", "XX")))

            if args['force']:
                print("(printing fields from all Cortex-M models)")
                model = None

            common_regs = get_mpu_common_regs(set(model) if model is not None else None)
            region_regs = get_mpu_region_regs(set(model) if model is not None else None)
            
            print("\nMPU common registers:\n")
            for reg in common_regs:
                reg.dump(inf, args['descr'], base=base, all=args['all'])
            
            initial_region = get_mpu_region(inf)
            for region in range(get_mpu_dregions(inf)):
                set_mpu_region(inf, region)
                if is_mpu_region_enabled(inf) or args["all"]:
                    print(f"\nMPU registers for region {region}:\n")
                    for reg in region_regs:
                        reg.dump(inf, args['descr'], base=base, all=args['all'])
                
            set_mpu_region(inf, initial_region)
        except:
            traceback.print_exc()
