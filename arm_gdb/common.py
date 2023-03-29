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


class RegisterDef:
    def __init__(self, name, descr, addr, size):
        self.name = name
        self.descr = descr
        self.addr = addr
        self.size = size

    def format_int(self, val, chars=-1):
        if chars < 0:
            chars = chars = self.size * 2
        return (("0" * chars) + ("%x" % (val,)))[-chars:]

    def dump(self, inf):
        self.dump_info(read_reg(inf, self.addr, self.size))

    def dump_hdr(self, m_int):
        print("%-10s = %8s %s// %s" %
              (self.name, self.format_int(m_int), " "*20, self.descr)
              )

    def dump_info(self, m_int):
        self.dump_hdr(m_int)


class RegisterDefBitfield(RegisterDef):
    def __init__(self, name, descr, addr, size, bits):
        super().__init__(name, descr, addr, size)
        self.bits = bits

    def dump_info(self, m_int):
        self.dump_hdr(m_int)
        for (i, len, name) in self.bits:
            value = (m_int >> i) & ((1 << len) - 1)
            if value != 0:
                print(
                    "             %8s - %4s - %s" %
                    (
                        self.format_int(value << i),
                        self.format_int(value, (len + 3)//4),
                        name
                    )
                )
