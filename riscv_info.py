#!/usr/bin/env python
#-----------------------------------------------------------------------------
#
#  RISCV-INFO - Collect information on RISC-V processor
#  Copyright (c) 2025, Thierry Lelegard
#  BSD-2-Clause license, see https://opensource.org/license/BSD-2-Clause
#
#-----------------------------------------------------------------------------

import os, sys, re

# The base architecture contains the following letters.
# Note: 'G' is a shorthand for IMAFD extensions.
RV_BASE_CODES = {
    'A': 'Atomic instructions',
    'B': 'Bit manipulation',
    'C': 'Compressed instructions',
    'D': 'Double-precision floating-point',
    'E': 'Integer instructions (embedded)',
    'F': 'Single-precision floating-point',
    'H': 'Hypervisor extension',
    'I': 'Integer instructions',
    'J': 'Dynamically translated languages',
    'L': 'Decimal floating-point',
    'M': 'Integer multiplication and division',
    'N': 'User-level interrupts',
    'P': 'Packed-SIMD instructions',
    'Q': 'Quad-precision floating-point',
    'S': 'Supervisor mode',
    'T': 'Transactional memory',
    'V': 'Vector operations'
}

# A dictionary of known RISC-V extensions.
# It may be not complete, feel free to submit contributions to supplement it.
# Please keep the list sorted.
RV_EXTENSIONS = {
    'Smctr': 'Control Transfer Records, machine and supervisor modes',
    'Smmpm': 'Machine-level pointer masking for M-mode',
    'Smnpm': 'Machine-level pointer masking for next lower privilege',
    'Ssctr': 'Control Transfer Records, supervisor mode only',
    'Ssnpm': 'Supervisor-level pointer masking for next lower privilege',
    'Sspm':  'Indicates that there is pointer-masking support in supervisor mode',
    'Supm':  'Indicates that there is pointer-masking support in user mode',
    'Zclsd': 'Compressed Load/Store pair instructions',
    'Zilsd': 'Load/Store pair instructions',
}

# A dictionary of known RISC-V profiles.
RV_PROFILES = {}

# Definition of a RISC-V profile.
class RVProfile:
    # Constructor. Register itself into RV_PROFILES/
    def __init__(self, name, flags, exts, opt_flags, opt_exts):
        self.name = name
        self.flags = flags
        self.exts = exts
        self.opt_flags = opt_flags
        self.opt_exts = opt_exts
        m = re.fullmatch(r'.*[^0-9]([0-9]+)', name)
        self.bits = int(m.group(1)) if m is not None else 0
        RV_PROFILES[name] = self

# Known RISC-V profiles.
RVProfile('RVI20U32', 'I', [], 'MAFDC', ['Zifencei', 'Zicntr', 'Zihpm'])
RVProfile('RVI20U64', 'I', [], 'MAFDC', ['Zifencei', 'Zicntr', 'Zihpm'])

# Definition of the characteristics of a RISC-V processor.
class RVProcessor:
    # Constructor.
    def __init__(self):
        self.basename = ''     # Example: RV64GCVH
        self.bits = 0          # Example: 32, 64, 128
        self.flags = ''        # Example: IMAFDCVH
        self.extensions = []   # List of extension names
        self.error = False     # Error in parsing capabilities

    # Try to set basename, bits and flags.
    # Return False if not a RISC-V basename.
    def set_basename(self, basename):
        # The base ISA is RV32xxx, RV64xxx, RV128xxx.
        name = basename.upper()
        match = re.fullmatch(r'RV([0-9]+)(.*)', name)
        if match is None:
            return False
        if self.basename == '':
            self.basename = name
            self.bits = int(match.group(1))
            # Note: 'G' is a shorthand for IMAFD extensions.
            self.flags = match.group(2).replace('G', 'IMAFD')
        elif self.basename != name:
            print('ERROR: multiple base ISA: %s, %s' % (self.basename, name), file=sys.stderr)
            self.error = True
        return True

    # Load from the current processor.
    def load(self):
        self.__init__()
        with open('/proc/cpuinfo', 'r') as input:
            for line in input:
                prefix, _, value = line.partition(':')
                if prefix.strip().lower() in ['isa', 'hart isa']:
                    for c in value.strip().split('_'):
                        if not self.set_basename(c):
                            c = c.capitalize()
                            if c not in self.extensions:
                                self.extensions.append(c)
        self.extensions.sort()

    # Print a description of the processor.
    def print(self, file=sys.stdout):
        print('', file=file)
        print('Base architecture', file=file)
        print('=================', file=file)
        print('%s (%d bits)' % (self.basename, self.bits), file=file)
        for f in self.flags:
            print('  %s: %s' % (f, RV_BASE_CODES[f] if f in RV_BASE_CODES else '(unknown)'), file=file)
        print('', file=file)
        print('ISA extensions', file=file)
        print('==============', file=file)
        width = max(len(e) for e in [''] + self.extensions)
        print('Found %d extensions' % len(self.extensions), file=file)
        for e in self.extensions:
            print('  %-*s : %s' % (width, e, RV_EXTENSIONS[e] if e in RV_EXTENSIONS else '(unknown)'), file=file)
        print('', file=file)

# Main code.
if __name__ == '__main__':
    proc = RVProcessor()
    proc.load()
    proc.print()
