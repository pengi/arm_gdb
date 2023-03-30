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

from cmsis_svd.parser import SVDParser

devices = {}


class ArmToolsSVDList (gdb.Command):
    """List peripherals from a loaded SVD file"""

    def __init__(self):
        super().__init__('arm list', gdb.COMMAND_USER, gdb.COMPLETE_NONE, True)

        self.parser = argparse.ArgumentParser(
            description="Inspect a peripheral from a loaded SVD file"
        )
        self.parser.add_argument('device')

    def invoke(self, argument, from_tty):
        argv = gdb.string_to_argv(argument)
        try:
            args = self.parser.parse_args(argv)
        except SystemExit:
            # We're running argparse in gdb, don't exit just return
            return

        device = devices[args.device]

        for peripheral in device.peripherals:
            print("%-10s @ 0x%08x" %
                  (peripheral.name, peripheral.base_address))


class ArmToolsSVDInspect (gdb.Command):
    """Dump peripherals specified by SVD file"""

    def __init__(self):
        super().__init__('arm inspect', gdb.COMMAND_USER, gdb.COMPLETE_NONE, True)

        self.parser = argparse.ArgumentParser(
            description="Inspect a peripheral from a loaded SVD file"
        )
        self.parser.add_argument('device')
        self.parser.add_argument('peripheral')
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

        device = devices[args.device]
        peripheral = None
        for p in device.peripherals:
            if p.name == args.peripheral:
                peripheral = p
        if peripheral is None:
            print("Unknown peripheral", args.peripheral)
            return

        inf = gdb.selected_inferior()

        for register in peripheral.registers:
            fields = []
            for field in register._fields:
                if field.is_enumerated_type:
                    fields.append(FieldBitfieldEnum(
                        field.name,
                        field.bit_offset,
                        field.bit_width,
                        [
                            (ev.value, ev.is_default, ev.name, ev.description)
                            for ev in field.enumerated_values
                        ],
                        field.description
                    ))
                else:
                    fields.append(FieldBitfield(
                        field.name,
                        field.bit_offset,
                        field.bit_width,
                        field.description
                    ))
            reg = RegisterDef(
                peripheral.name + "." + register.name,
                register.description,
                peripheral.base_address + register.address_offset,
                4,
                fields
            )
            reg.dump(inf, args.descr)


class ArmToolsSVDLoadFile (gdb.Command):
    """Load an SVD file from registry"""

    def __init__(self):
        super().__init__('arm loadfile', gdb.COMMAND_USER)

        self.parser = argparse.ArgumentParser(
            description="Load an SVD file given a path"
        )
        self.parser.add_argument('device')
        self.parser.add_argument('filename')

    def invoke(self, argument, from_tty):
        argv = gdb.string_to_argv(argument)
        try:
            args = self.parser.parse_args(argv)
        except SystemExit:
            # We're running argparse in gdb, don't exit just return
            return

        parser = SVDParser.for_xml_file(args.filename)
        devices[args.device] = parser.get_device()


class ArmToolsSVDLoadDB (gdb.Command):
    """Load an SVD file from registry"""

    def __init__(self):
        super().__init__('arm loaddb', gdb.COMMAND_USER)

        self.parser = argparse.ArgumentParser(
            description="Load an SVD file from database. See cmsis-svd python package for a list"
        )
        self.parser.add_argument('device')
        self.parser.add_argument('vendor')
        self.parser.add_argument('filename')

    def invoke(self, argument, from_tty):
        argv = gdb.string_to_argv(argument)
        try:
            args = self.parser.parse_args(argv)
        except SystemExit:
            # We're running argparse in gdb, don't exit just return
            return

        parser = SVDParser.for_packaged_svd(args.vendor, args.filename)
        devices[args.device] = parser.get_device()
