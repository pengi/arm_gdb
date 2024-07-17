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

def get_mpu_regs():
    return [
        RegisterDef("MPU_TYPE", "MPU Type Register", 0xE000ED90, 4, [
            FieldBitfield("DREGION",  8, 8,
                          "Number of MPU regions that are supported by the MPU in selected security state"),
            FieldBitfield("SEPARATE",  0, 1,
                          "Indicates support for separate instruction data address regions. ARMv8-M only supports unified MPU regions and therefore this bit is set to 0."),
        ]),
        RegisterDef("MPU_CTRL", "MPU Control Register", 0xE000ED94, 4, [
            FieldBitfield("PRIVDEFENA", 2, 1,
                          "Privileged background region enable, 1 enable background, 0 clear"),
            FieldBitfield("HFNMIENA", 1, 1,
                          "MPU Enable for HardFault and NMI (Non-Maskable Interrupt)"),
            FieldBitfield("ENABLE", 0, 1,
                          "Enable control"),
        ]),
    ]

def print_outer_inner_attr(mair_attr_outer, mair_attr_inner):
    if mair_attr_outer != 0 :
        if mair_attr_outer == 0b0001:
            print(f"Normal memory,  Outer Write-Through transient, Write allocation")
        elif mair_attr_outer == 0b0010:
            print(f"Normal memory,  Outer Write-Through transient, Read allocation")
        elif mair_attr_outer == 0b0011:
            print(f"Normal memory,  Outer Write-Through transient, Read/Write allocation")
        elif mair_attr_outer == 0b0100:
            print(f"Normal memory,  Outer Non-cacheable")
        elif mair_attr_outer == 0b0101:
            print(f"Normal memory,  Outer Write-Back Transient, Write allocation")
        elif mair_attr_outer == 0b0110:
            print(f"Normal memory,  Outer Write-Back Transient, Read allocation")
        elif mair_attr_outer == 0b0111:
            print(f"Normal memory,  Outer Write-Back Transient, Read/Write allocation")
        elif mair_attr_outer == 0b1001:
            print(f"Normal memory,   Outer Write-Through Non-transient, Write allocation")
        elif mair_attr_outer == 0b1010:
            print(f"Normal memory,   Outer Write-Through Non-transient, Read allocation")
        elif mair_attr_outer == 0b1011:
            print(f"Normal memory,   Outer Write-Through Non-transient, Read/Write allocation")
        elif mair_attr_outer == 0b1101:
            print(f"Normal memory,   Outer Write-Back Non-transient, Write allocation")
        elif mair_attr_outer == 0b1110:
            print(f"Normal memory,   Outer Write-Back Non-transient, Read allocation")
        elif mair_attr_outer == 0b1111:
            print(f"Normal memory,   Outer Write-Back Non-transient, Read/Write allocation")

        if mair_attr_inner == 0b0001:
            print(f"Normal memory,  Inner Write-Through transient, Write allocation")
        elif mair_attr_inner == 0b0010:
            print(f"Normal memory,  Inner Write-Through transient, Read allocation")
        elif mair_attr_inner == 0b0011:
            print(f"Normal memory,  Inner Write-Through transient, Read/Write allocation")
        elif mair_attr_inner == 0b0100:
            print(f"Normal memory,  Inner Non-cacheable")
        elif mair_attr_inner == 0b0101:
            print(f"Normal memory,  Inner Write-Back Transient, Write allocation")
        elif mair_attr_inner == 0b0110:
            print(f"Normal memory,  Inner Write-Back Transient, Read allocation")
        elif mair_attr_inner == 0b0111:
            print(f"Normal memory,  Inner Write-Back Transient, Read/Write allocation")
        elif mair_attr_inner == 0b1001:
            print(f"Normal memory,   Inner Write-Through Non-transient, Write allocation")
        elif mair_attr_inner == 0b1010:
            print(f"Normal memory,   Inner Write-Through Non-transient, Read allocation")
        elif mair_attr_inner == 0b1011:
            print(f"Normal memory,   Inner Write-Through Non-transient, Read/Write allocation")
        elif mair_attr_inner == 0b1101:
            print(f"Normal memory,   Inner Write-Back Non-transient, Write allocation")
        elif mair_attr_inner == 0b1110:
            print(f"Normal memory,   Inner Write-Back Non-transient, Read allocation")
        elif mair_attr_inner == 0b1111:
            print(f"Normal memory,   Inner Write-Back Non-transient, Read/Write allocation")
    #device memory
    elif mair_attr_outer == 0 :
        device_attr = ( mair_attr_inner >> 2 ) & 0b11
        if device_attr == 0b00:
            print(f"Device memory,   nGnRnE")
        elif device_attr == 0b01:
            print(f"Device memory,   nGnRE")
        elif device_attr == 0b10:
            print(f"Device memory,   nGRE")
        elif device_attr == 0b11:
            print(f"Device memory,   GRE")

def get_mair_attr(reg_addr, offset):
    value_str = gdb.execute(f"x/1x {reg_addr}", to_string=True)
    print("mair ", value_str)
    value_hex = value_str.split(':')[1].strip()
    value = int(value_hex, 16)

    for attr_index in range(0,4):
        attr = value & 0xff
        mair_attr_outer = ( attr & 0xf0 ) >> 4
        mair_attr_inner = ( attr & 0x0f )
        print("ATTR", attr_index + offset)
        print_outer_inner_attr(mair_attr_outer, mair_attr_inner)
        value = value >> 8

def set_rnr_reg(number):
    REG_RNR = 0xE000ED98
    gdb.execute(f"set *((unsigned int*){REG_RNR}) = {number}", to_string=True)

def get_mpu_regions_number():
    REG_TYPE = 0xE000ED90
    type_str = gdb.execute(f"x/1x {REG_TYPE}", to_string=True)
    regions_hex = type_str.split(':')[1].strip()
    regions_value = int(regions_hex, 16)
    regions = (regions_value >> 8) & 0xff
    print(f"MPU region number {regions:#d}")

    return regions

def get_rbar_reg():
    return [
        RegisterDef("MPU_RBAR", "MPU Region Base Address Register", 0xE000ED9C, 4, [
            FieldBitfield("BASE", 5, 27, "Starting address of MPU region address"),
            FieldBitfieldEnum("SH", 3, 2, [
                (0b00, False, "Non-shareable", None),
                (0b01, False, "Outer shareable", None),
                (0b10, False, "Inner Shareable", None),
                ],"Shareability for Normal memory"),
            FieldBitfieldEnum("AP", 1, 2, [
                (0b00, False, "read/write by privileged code only", None),
                (0b01, False, "read/write by any privilege level", None),
                (0b10, False, "Read only by privileged code only", None),
                (0b11, False, "Read only by any privilege level", None),
                ],"Access permissions"),
            FieldBitfieldEnum("XN", 0, 1, [
                (0b1, False, "Disallow program execution in this region", None),
                (0b0, False, "Allow program execution in this region", None),
                ],"eXecute Never attribute"),
            ]),
    ]

def get_rlar_reg():
    return [
        RegisterDef("MPU_RLAR", "MPU Region Base Limit Register", 0xE000EDA0, 4, [
            FieldBitfield("LIMIT", 5, 27, "Ending address (upper inclusive limit) of MPU region address"),
            FieldBitfieldEnum("PXN", 4, 1, [
                (0b1, False, "Execution from a privileged mode is not permitted", None),
                (0b0, False, "Execution only permitted if read permitted", None),
                ],"Privileged execute-never"),
            FieldBitfield("AttrIndx", 1, 3, "Attribute Index. Select memory attributes from attribute sets in MPU_MAIR0 and MPU_MAIR1"),
            FieldBitfieldEnum("EN", 0, 1, [
                (0b0, False, "disable", None),
                (0b1, False, "Region enable", None),
            ],"Region enable"),
        ]),
    ]

def get_mpu_region_start():
    REG_RBAR = 0xE000ED9C
    value_str = gdb.execute(f"x/1x {REG_RBAR}", to_string=True)
    value_hex = value_str.split(':')[1].strip()
    value = int(value_hex, 16)
    start = value & 0xFFFFFFE0;
    return start

def get_mpu_region_limit():
    REG_RLAR = 0xE000EDA0
    value_str = gdb.execute(f"x/1x {REG_RLAR}", to_string=True)
    value_hex = value_str.split(':')[1].strip()
    value = int(value_hex, 16)
    limit = value & 0xFFFFFFE0;
    return limit

def mpu_region_enable():
    REG_RLAR = 0xE000EDA0
    value_str = gdb.execute(f"x/1x {REG_RLAR}", to_string=True)
    value_hex = value_str.split(':')[1].strip()
    value = int(value_hex, 16)
    enabled = bool(value & 0x01)
    return enabled

def get_mpu_regions():
    set_rnr_reg(1)
    reg = get_rbar_reg()
    reg.dump(inf, args['descr'], base=base, all=args['all'])

    reg = get_rlar_reg()
    reg.dump(inf, args['descr'], base=base, all=args['all'])

class ArmToolsMPU (ArgCommand):
    """Dump of ARM Cortex-M MPU - SCB registers for the FP extension

Usage: arm mpu [/hab]

Modifier /h provides descriptions of names where available
Modifier /a Print all fields, including default values
Modifier /b prints bitmasks in binary instead of hex
"""

    def __init__(self):
        super().__init__('arm mpu', gdb.COMMAND_DATA)
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

        print("SCB MPU registers:")

        try:
            regs = get_mpu_regs()
        except:
            traceback.print_exc()

        for reg in regs:
            reg.dump(inf, args['descr'], base=base, all=args['all'])

        print("MPU MAIR registers:")
        REG_MAIR0 = 0xE000EDC0
        get_mair_attr(REG_MAIR0, 0)
        REG_MAIR1 = 0xE000EDC4
        get_mair_attr(REG_MAIR1, 4)

        regions = get_mpu_regions_number()
        for i in range(1, regions):
            set_rnr_reg(i)
            if  mpu_region_enable():
                print("mpu region: ", i)
                start = get_mpu_region_start()
                limit = get_mpu_region_limit()
                print(f"region start at {start:#x}")
                print(f"region end   at {limit:#x}")
                regs = get_rbar_reg()
                for reg in regs:
                    reg.dump(inf, args['descr'], base=base, all=args['all'])

                regs = get_rlar_reg()
                for reg in regs:
                    reg.dump(inf, args['descr'], base=base, all=args['all'])


