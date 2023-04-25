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

#
# Library functions, that can be tested outside of gdb. used for type
#
import re

def base_convert(val, base, bits):
    """
    Convert a value to string, given base

    The base is specified as 2**n, thus number of bits to group. And up to 2**4.
    Thus basically binary, octal and hex.

    >>> base_convert(255, 4, 8)
    'ff'
    >>> base_convert(255, 3, 8)
    '377'
    >>> base_convert(0xaa, 4, 8)
    'aa'
    >>> base_convert(0xcafe, 1, 16)
    '1100101011111110'
    >>> base_convert(0, 1, 16)
    '0000000000000000'
    """
    digits = '0123456789abcdef'

    bitmask = (1 << base)-1
    num_digits = (bits + base - 1) // base

    outp = [0] * num_digits
    for i in range(num_digits):
        outp[i] = val & bitmask
        val >>= base

    outp.reverse()

    return "".join(digits[v] for v in outp)


def format_int(val, bits, bit_offset=0, bit_length=None, base=4):
    """
    >>> format_int(0x12345678, 32)
    '12345678'
    >>> format_int(0x0, 31)
    '00000000'
    >>> format_int(0x0, 28)
    '0000000'
    >>> format_int(0x12345678, 32, 16, 8)
    '..34....'
    >>> format_int(0x12345678, 32, 16, 8, 1)
    '........00110100................'
    """
    if bit_length is None:
        bit_length = bits - bit_offset

    # Mask out bits
    mask = ((1 << bit_length)-1) << bit_offset
    val &= mask

    # Generate printout of both number and mask
    val_str = base_convert(val, base, bits)
    mask_str = base_convert(mask, base, bits)
    # replace all digits in val_str that's zero in mask
    return "".join('.' if m == '0' else v for v, m in zip(val_str, mask_str))


def filt(tags, list):
    """
    Filter elements of a list based on version tags. Each element in the list
    is a tuple where first field is a comma separated list of tags, second field
    is the value.

    The tags argument is a set of tags as strings of which elements should be
    kept

    If either tags is None or the first element in the tuple is None, then the
    element will be included

    >>> filt({'a', 'x'}, [(None, 'x'), ('a,b', 'y')])
    ['x', 'y']

    >>> filt({'c', 'x'}, [(None, 'x'), ('a,b', 'y')])
    ['x']

    >>> filt(None, [(None, 'x'), ('a,b', 'y')])
    ['x', 'y']
    """

    return [
        v
        for m, v in list
        if (
            tags is None or
            m is None or
            len(set(m.split(",")) & tags) > 0
        )
    ]

def norm_descr(text):
    """
    Replace multiple successive line breaks, tabs and spaces a single space to
    compactify descriptions.

    >>> norm_descr('Hello\\n\\t     World')
    'Hello World'
    """
    return re.sub(r"[\n\r\t ]+", " ", text)


if __name__ == "__main__":
    import doctest
    doctest.testmod(verbose=True)
