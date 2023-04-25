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
from .lib import *


def read_reg(inf, addr, len):
    bs = inf.read_memory(addr, len).tobytes()
    return sum(v << (8*i) for i, v in enumerate(bs))


class ArgType:
    def __init__(self, name, completer=None, getter=None, optional=False):
        self.name = name
        self.completer = completer
        self.getter = getter
        self.optional = optional

    def complete(self, word, args={}):
        if self.completer is None:
            return gdb.COMPLETE_NONE
        elif callable(self.completer):
            return self.completer(word, args)
        else:
            return self.completer

    def get(self, word, args={}):
        if self.getter is None:
            return word
        else:
            return self.getter(word, args)


class ArgCommand(gdb.Command):
    def __init__(self, name, command_class=gdb.COMMAND_USER):
        super().__init__(name, command_class)
        self.name = name
        self.arg_list = []
        self.arg_mods = []

    def add_arg(self, argtype):
        self.arg_list.append(argtype)

    def add_mod(self, letter, name):
        self.arg_mods.append((letter, name))

    def complete(self, text, word):
        args = gdb.string_to_argv(text)

        if len(args) > 0 and args[0].startswith('/'):
            # First arg is modifiers
            mods = args[0][1:]
            args = args[1:]
        else:
            mods = ""

        # If ends with space, then it's the next argument that should start
        if len(text) == 0 or text[-1] == ' ':
            args.append("")

        if len(args) > len(self.arg_list):
            return gdb.COMPLETE_NONE

        values = {}
        for cur_arg, cur_argtype in zip(args[:-1], self.arg_list):
            values[cur_argtype.name] = cur_argtype.get(cur_arg, values)

        return self.arg_list[len(args)-1].complete(args[-1], values)

    def process_args(self, text):
        args = gdb.string_to_argv(text)
        if len(args) > 0 and args[0].startswith('/'):
            # First arg is modifiers
            mods = args[0][1:]
            args = args[1:]
        else:
            mods = ""

        if len(args) > len(self.arg_list):
            return None

        for i, argtype in enumerate(self.arg_list):
            if not argtype.optional and len(args) <= i:
                return None

        values = {}

        for m_letter, m_name in self.arg_mods:
            values[m_name] = mods.count(m_letter) > 0

        for cur_arg, cur_argtype in zip(args, self.arg_list):
            values[cur_argtype.name] = cur_argtype.get(cur_arg, values)

        return values

    def print_help(self):
        args = [self.name]
        if len(self.arg_mods) > 0:
            args += ['/' + ''.join(letter for letter, name in self.arg_mods)]
        args += [
            ('[<%s>]' if arg.optional else '<%s>') % (arg.name,)
            for arg in self.arg_list
        ]
        print("Usage:", *args)


class RegisterDef:
    def __init__(self, name, descr, addr, size, fields=[]):
        self.name = name
        self.descr = norm_descr(descr) if descr else None
        self.addr = addr
        self.size = size
        self.fields = fields

    def dump(self, inf, include_descr=True, base=4, all=False):
        m_int = read_reg(inf, self.addr, self.size)

        if self.descr and include_descr:
            descr = (" "*18 + "// " + self.descr)
        else:
            descr = ""

        field_align = "%%%ds" % (32//base)
        print(("%-32s = "+field_align+" %s") %
              (self.name, format_int(m_int, self.size * 8, base=base), descr)
              )

        for field in self.fields:
            if all or field.should_print(m_int):
                field.print(m_int, include_descr, base=base)


class Field:
    def __init__(self, name, descr=None, always=False):
        self.name = name
        self.descr = norm_descr(descr) if descr else None
        self.always = always

    def should_print(self, value):
        return False

    def get_value(self, value):
        return 0

    def get_print_bits(self, value, base=4):
        return format_int(value, 32, 0, 0, base)

    def get_print_value(self, value):
        return None

    def print(self, value, include_descr=True, base=4):
        if self.descr and include_descr:
            descr = (" // " + self.descr)
        else:
            descr = ""

        field_align = "%%%ds" % (32//base)
        print(
            ("    %-28s   "+field_align+" - %-15s%s") %
            (
                self.name,
                self.get_print_bits(value, base=base),
                self.get_print_value(value),
                descr
            )
        )


class FieldBitfield(Field):
    def __init__(self, name, bit_offset, bit_width, descr=None, always=False):
        super().__init__(name, descr, always=always)
        self.bit_offset = bit_offset
        self.bit_width = bit_width

    def should_print(self, value):
        return self.always or self.get_value(value) != 0

    def get_value(self, value):
        return (value >> self.bit_offset) & ((1 << self.bit_width)-1)

    def get_print_bits(self, value, base=4):
        return format_int(value, 32, self.bit_offset, self.bit_width, base)

    def get_print_value(self, value):
        return format_int(self.get_value(value), self.bit_width)


class FieldBitfieldEnum(FieldBitfield):
    def __init__(self, name, bit_offset, bit_width, enum_values, descr=None, always=False):
        super().__init__(name, bit_offset, bit_width, descr, always=always)
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
        if self.always:
            return True
        try:
            v, is_default, name, descr = self.get_enum_value(value)
            return not is_default
        except:
            return True


class FieldBitfieldMap(FieldBitfield):
    def __init__(self, name, bit_offset, bit_width, map_func, descr=None, always=False):
        super().__init__(name, bit_offset, bit_width, descr, always=always)
        self.map_func = map_func

    def get_print_value(self, value):
        return self.map_func(self.get_value(value))

class FieldBit(FieldBitfield):
    def __init__(self, name, bit, descr=None, always=False):
        super().__init__(name, bit, 1, descr, always=always)
        self.bit = bit
