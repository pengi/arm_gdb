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

# To auto complete `amd loaddb`
import pkg_resources

devices = {}


class DevicesArgType(ArgType):
    def __init__(self, name, optional=False):
        super().__init__(name, optional=optional)

    def complete(self, word, args={}):
        return [w for w in devices.keys() if w.startswith(word)]

    def get(self, word, args={}):
        return devices[word]


class PeripheralsArgType(ArgType):
    def __init__(self, name, device_arg, optional=False):
        super().__init__(name, optional=optional)
        self.device_arg = device_arg

    def complete(self, word, args={}):
        device = args[self.device_arg]
        return [p.name for p in device.peripherals if p.name.startswith(word)]

    def get(self, word, args={}):
        device = args[self.device_arg]
        for p in device.peripherals:
            if p.name == word:
                return p
        return None


class ArmToolsSVDList (ArgCommand):
    """List peripherals and registers from device
    
Usage: arm list

Lists loaded devices

Usage: arm list <device>

List peripherals from a device

Usage: arm list <device> <peripheral>

List registers from a peripheral

Examples:
    arm list
    arm list nrf52840
    arm list nrf52840 UARTE0
"""

    def __init__(self):
        super().__init__('arm list', gdb.COMMAND_SUPPORT)
        self.add_arg(DevicesArgType('device', optional=True))
        self.add_arg(PeripheralsArgType('peripheral', 'device', optional=True))

    def invoke(self, argument, from_tty):
        args = self.process_args(argument)
        if args is None:
            self.print_help()
            return

        if not 'device' in args:
            print("Devices loaded:")
            for device in devices.keys():
                print(" -", device)
        elif not 'peripheral' in args:
            device = args['device']
            print("Peripherals:")
            for peripheral in device.peripherals:
                print(
                    "%-10s @ 0x%08x" % (
                        peripheral.name,
                        peripheral.base_address
                    )
                )
        else:
            device = args['device']
            peripheral = args['peripheral']
            print(
                "Registers in %s @ 0x%08x:" % (
                    peripheral.name,
                    peripheral.base_address
                )
            )
            for register in peripheral.registers:
                print(
                    " - %s @ +0x%x" % (
                        register.name,
                        register.address_offset
                    )
                )
                for field in register._fields:
                    mask = "." * (32-field.bit_offset-field.bit_width) + \
                        "#" * field.bit_width + "." * field.bit_offset

                    print("        %s %s" % (mask, field.name))


class ArmToolsSVDInspect (ArgCommand):
    """Dump register values from device peripheral

Usage: arm inspect /h <device> <peripheral>

Modifier /h provides descriptions of names where available

    <device>     - Name of loaded device. See `help arm loadfile`
    <peripheral> - Name of peripheral

Exmaple: arm inspect nrf52840 UARTE0
"""

    def __init__(self):
        super().__init__('arm inspect', gdb.COMMAND_DATA)
        self.add_arg(DevicesArgType('device'))
        self.add_arg(PeripheralsArgType('peripheral', 'device'))
        self.add_mod('h', 'descr')

    def invoke(self, argument, from_tty):
        args = self.process_args(argument)
        if args is None:
            self.print_help()
            return

        peripheral = args['peripheral']

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
            reg.dump(inf, args['descr'])


class ArmToolsSVDLoadFile (ArgCommand):
    """Load an SVD file from file

Usage: arm loadfile <device> <filename>

    <device>    - Name to refer to the device in commands like `arm inspect`
    <filename>  - SVD file to load

This command can preferrably be added to .gdbinit for easy access of devices
"""

    def __init__(self):
        super().__init__('arm loadfile', gdb.COMMAND_USER)
        self.add_arg(ArgType('device', gdb.COMPLETE_NONE))
        self.add_arg(ArgType('filename', gdb.COMPLETE_FILENAME))

    def invoke(self, argument, from_tty):
        args = self.process_args(argument)
        if args is None:
            self.print_help()
            return

        parser = SVDParser.for_xml_file(args['filename'])
        devices[args['device']] = parser.get_device()


class ArmToolsSVDLoadDB (ArgCommand):
    """Load an SVD file from resitry

Usage: arm loaddb <device> <vendor> <filename>

    <device>    - Name to refer to the device in commands like `arm inspect`
    <vendor>    - Device vendor
    <filename>  - SVD file within registry

Load file from cmsis-svd package registry. Many common devices are available. If
not available, you can load a custom svd file using `arm loadfile`

This command can preferrably be added to .gdbinit for easy access of devices
"""

    def __init__(self):
        super().__init__('arm loaddb', gdb.COMMAND_USER)
        self.add_arg(ArgType('device', gdb.COMPLETE_NONE))
        self.add_arg(ArgType('vendor', self.get_vendors))
        self.add_arg(ArgType('filename', self.get_filenames))

    def get_vendors(self, word, args):
        vendors = pkg_resources.resource_listdir('cmsis_svd', 'data')
        return [v for v in vendors if v.startswith(word)]

    def get_filenames(self, word, args):
        files = pkg_resources.resource_listdir(
            'cmsis_svd',
            'data/'+args['vendor']
        )
        return [f for f in files if f.startswith(word)]

    def invoke(self, argument, from_tty):
        args = self.process_args(argument)
        if args is None:
            self.print_help()
            return

        parser = SVDParser.for_packaged_svd(args['vendor'], args['filename'])
        devices[args['device']] = parser.get_device()
