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

def read_reg(inf, addr, len):
    bs = inf.read_memory(addr, len).tobytes()
    return sum(v << (8*i) for i, v in enumerate(bs))


def format_int(val, bits):
    chars = (bits + 3) // 4
    return (("0" * chars) + ("%x" % (val,)))[-chars:]


class RegisterDef:
    def __init__(self, name, descr, addr, size, fields=[]):
        self.name = name
        self.descr = descr
        self.addr = addr
        self.size = size
        self.fields = fields

    def dump(self, inf, include_descr=True):
        m_int = read_reg(inf, self.addr, self.size)

        if self.descr and include_descr:
            descr = (" "*18 + "// " + self.descr)
        else:
            descr = ""

        print("%-32s = %8s %s" %
              (self.name, format_int(m_int, self.size * 8), descr)
              )

        for field in self.fields:
            if field.should_print(m_int):
                field.print(m_int, include_descr)


class Field:
    def __init__(self, name, descr=None):
        self.name = name
        self.descr = descr

    def should_print(self, value):
        return False

    def get_bitmask(self, value):
        return 0

    def get_print_value(self, value):
        return None

    def print(self, value, include_descr=True):
        bitmask = self.get_bitmask(value)
        print_value = self.get_print_value(value)

        if self.descr and include_descr:
            descr = (" // " + self.descr)
        else:
            descr = ""

        print(
            "    %-28s   %8s - %-15s%s" %
            (
                self.name,
                format_int(bitmask, 32),
                print_value,
                descr
            )
        )


class FieldBitfield(Field):
    def __init__(self, name, bit_offset, bit_width, descr=None):
        super().__init__(name, descr)
        self.bit_offset = bit_offset
        self.bit_width = bit_width

    def get_bitmask(self, value):
        return value & (((1 << self.bit_width)-1) << self.bit_offset)

    def get_value(self, value):
        return (value >> self.bit_offset) & ((1 << self.bit_width)-1)

    def get_print_value(self, value):
        return format_int(self.get_value(value), self.bit_width)

    def should_print(self, value):
        return self.get_value(value) != 0


class FieldBitfieldEnum(FieldBitfield):
    def __init__(self, name, bit_offset, bit_width, enum_values, descr=None):
        super().__init__(name, bit_offset, bit_width, descr)
        self.enum_values = enum_values

    def get_enum_value(self, value):
        my_value = self.get_value(value)
        for enum_value in self.enum_values:
            if my_value == enum_value[0]:
                return enum_value
        return None

    def get_print_value(self, value):
        try:
            v, is_default, name, descr = self.get_enum_value(value)
            return name
        except:
            return format_int(self.get_value(value), self.bit_width)

    def should_print(self, value):
        try:
            v, is_default, name, descr = self.get_enum_value(value)
            return not is_default
        except:
            return True


class FieldBit(FieldBitfield):
    def __init__(self, name, bit, descr=None):
        super().__init__(name, bit, 1, descr)
        self.bit = bit
