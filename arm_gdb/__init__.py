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
from . import scb
from . import fpu
from . import systick
from . import nvic
from . import svd

class ArmTools (gdb.Command):
    """Tools for debugging ARM Cortex-M - series CPUs"""

    def __init__(self):
        super().__init__('arm', gdb.COMMAND_USER, gdb.COMPLETE_NONE, True)

    def invoke(self, argument, from_tty):
        gdb.execute('help arm')


ArmTools()
scb.ArmToolsSCB()
fpu.ArmToolsFPU()
systick.ArmToolsSysTick()
nvic.ArmToolsNVIC()
svd.ArmToolsSVDList()
svd.ArmToolsSVDInspect()
svd.ArmToolsSVDLoadFile()
svd.ArmToolsSVDLoadDB()
