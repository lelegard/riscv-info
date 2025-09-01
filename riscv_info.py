#!/usr/bin/env python
#-----------------------------------------------------------------------------
#
#  RISCV-INFO - Collect information on RISC-V processor
#  Copyright (c) 2025, Thierry Lelegard
#  BSD-2-Clause license, see https://opensource.org/license/BSD-2-Clause
#
#-----------------------------------------------------------------------------

import os, sys, re, glob, yaml

USAGE = """
Syntax: %s [options]

Options:

  -c filename
  --cpuinfo filename
     Use the specified file for 'cpuinfo' pseudo file.
     Useful to test alternative configurations.
     Default: /proc/cpuinfo

  -d filename
  --definition filename
     Use the specified file instead of the default YAML definition file for
     RISC-V configurations which comes with that script.

  -i pattern
  --isa
     Use the specified file pattern, with optional wildcards, for the
     'riscv,isa-extensions' pseudo files.
     Useful to test alternative configurations.
     Default: /proc/device-tree/cpus/*/riscv,isa-extensions

  -h
  --help
     Display this help text.

  -v
  --verbose
     Verbose display.
"""

DEFAULT_CPUINFO = '/proc/cpuinfo'
DEFAULT_ISAGLOB = '/proc/device-tree/cpus/*/riscv,isa-extensions'

#-----------------------------------------------------------------------------
# Generic command line management.
#-----------------------------------------------------------------------------

class CommandLine:

    # Constructor.
    def __init__(self, argv=sys.argv, usage=''):
        self.argv = argv
        self.usage_text = usage
        self.script = os.path.basename(argv[0])
        self.scriptdir = os.path.dirname(os.path.abspath(argv[0]))
        self.verbose_mode = self.has_opt(['-v', '--verbose'])
        if self.has_opt(['-h', '--help']):
            print(self.usage_text % self.script)
            exit(0)

    # Get the value of an option in the command line.
    # Remove the option from the command line.
    # Use a name or list of names.
    def get_opt(self, names, default=None):
        if type(names) is str:
            names = [names]
        value = default
        i = 0
        while i < len(self.argv):
            if self.argv[i] in names:
                self.argv.pop(i)
                if i < len(self.argv):
                    value = self.argv[i]
                    self.argv.pop(i)
            else:
                i += 1
        return value

    # Check if an option without value is in the command line.
    # Remove the option from the command line.
    # Use a name or list of names.
    def has_opt(self, names):
        if type(names) is str:
            names = [names]
        value = False
        i = 0
        while i < len(self.argv):
            if self.argv[i] in names:
                self.argv.pop(i)
                value = True
            else:
                i += 1
        return value

    # Check that all command line options were recognized.
    def check_opt_final(self):
        if len(self.argv) > 1:
            self.fatal('extraneous options: %s' % ' '.join(self.argv[1:]))

    # Message reporting.
    def verbose(self, message):
        if self.verbose_mode:
            print(message, file=sys.stderr)
    def info(self, message):
        print(message, file=sys.stderr)
    def warning(self, message):
        print('%s: warning: %s' % (self.script, message), file=sys.stderr)
    def error(self, message):
        print('%s: error: %s' % (self.script, message), file=sys.stderr)
    def fatal(self, message):
        self.error(message)
        exit(1)

#-----------------------------------------------------------------------------
# Force a default value to a dictionary key
#-----------------------------------------------------------------------------

def set_default(dictionary, key, default):
    if key not in dictionary or dictionary[key] is None:
        dictionary[key] = default

#-----------------------------------------------------------------------------
# Definition of RISC-V profiles and extensions.
#-----------------------------------------------------------------------------

class Profiles:

    # Constructor, load configuration from a YAML file.
    def __init__(self, cmd, definition_file):
        self.cmd = cmd
        # Load the YAML configuration file.
        with open(definition_file, 'r') as input:
            self.data = yaml.safe_load(input)
        # Enforce default values.
        set_default(self.data, 'flags', dict())
        set_default(self.data, 'shorthands', dict())
        set_default(self.data, 'extensions', dict())
        set_default(self.data, 'profiles', dict())
        for name in self.data['profiles'].keys():
            set_default(self.data['profiles'], name, dict())
            set_default(self.data['profiles'][name], 'bits', 0)
            set_default(self.data['profiles'][name], 'endian', 'any')
            set_default(self.data['profiles'][name], 'flags', dict())
            set_default(self.data['profiles'][name]['flags'], 'mandatory', '')
            set_default(self.data['profiles'][name]['flags'], 'optional', '')
            set_default(self.data['profiles'][name], 'extensions', dict())
            set_default(self.data['profiles'][name]['extensions'], 'mandatory', dict())
            set_default(self.data['profiles'][name]['extensions'], 'optional', dict())

    # Cleanup a string of flags. Remove duplicates. Expand shorthands.
    def cleanup_flags(self, flags):
        input = flags.upper()
        clean = ''
        for s in self.data['shorthands'].keys():
            input = input.replace(s, self.data['shorthands'][s])
        for f in input:
            if f not in clean:
                clean += f
        return clean

    # Get the description of a flag.
    def flag_desc(self, flag):
        return self.data['flags'][flag] if flag in self.data['flags'] else 'Unknown'

    # Get the description of an extension.
    def extension_desc(self, name):
        return self.data['extensions'][name] if name in self.data['extensions'] else 'Unknown'

    # Get the list of profile names.
    def profile_names(self):
        return list(self.data['profiles'].keys())

#-----------------------------------------------------------------------------
# Definition of the characteristics of a RISC-V processor.
#-----------------------------------------------------------------------------

class Processor:

    # Constructor, load from a cpuinfo file.
    def __init__(self, profiles, cpuinfo_file=DEFAULT_CPUINFO, isa_pattern=DEFAULT_ISAGLOB):
        self.basename = ''     # Example: RV64GCVH
        self.bits = 0          # Example: 32, 64, 128
        self.flags = ''        # Example: IMAFDCVH
        self.extensions = []   # List of extension names
        self.profiles = profiles
        self.cmd = profiles.cmd
        # Parse /proc/cpuinfo
        with open(cpuinfo_file, 'r') as input:
            for line in input:
                prefix, _, value = line.partition(':')
                if prefix.strip().lower() in ['isa', 'hart isa', 'mmu']:
                    # Loop on all characteristics of the processor.
                    for c in value.strip().split('_'):
                        # The base ISA is RV32xxx, RV64xxx, RV128xxx.
                        c = c.upper()
                        match = re.fullmatch(r'RV([0-9]+)(.*)', c)
                        if match is None:
                            # Not a base name, this is an extension name.
                            self.add_extension(c)
                        else:
                            # This is a base ISA name.
                            if self.basename == '':
                                self.basename = c
                                self.bits = int(match.group(1))
                                self.add_flags(match.group(2))
                            elif self.basename != c:
                                cmd.error('multiple base ISA: %s, %s' % (self.basename, c))
        # Parse /proc/device-tree/cpus/*/riscv,isa-extensions
        for isa_file in glob.glob(isa_pattern):
            with open(isa_file, 'r') as input:
                for c in input.read().split('\0'):
                    if len(c) == 1:
                        self.add_flags(c)
                    elif len(c) > 0:
                        self.add_extension(c)
        self.extensions.sort()

    # Add a string of flags to the processor capabilities.
    def add_flags(self, new_flags):
        self.flags = self.profiles.cleanup_flags(self.flags + new_flags)

    # Add an extension to the processor.
    def add_extension(self, new_ext):
        new_ext = new_ext.capitalize()
        if new_ext not in self.extensions:
            self.extensions.append(new_ext)

    # Check if the processor matches the mandatory specs of a profile.
    def match_profile(self, profile_name):
        pdata = self.profiles.data['profiles']
        if profile_name not in pdata or pdata[profile_name]['bits'] != self.bits:
            return False
        for f in pdata[profile_name]['flags']['mandatory']:
            if f not in self.flags:
                return False
        for e in pdata[profile_name]['extensions']['mandatory']:
            if e not in self.extensions:
                return False
        return True

    # Print a description of the processor.
    def print(self, file=sys.stdout):
        print('', file=file)
        print('Base architecture', file=file)
        print('=================', file=file)
        print('%s (%d bits)' % (self.basename, self.bits), file=file)
        for f in self.flags:
            print('  %s: %s' % (f, self.profiles.flag_desc(f)), file=file)
        print('', file=file)
        print('ISA extensions', file=file)
        print('==============', file=file)
        width = max(len(e) for e in [''] + self.extensions)
        print('Found %d extensions' % len(self.extensions), file=file)
        for e in self.extensions:
            print('  %-*s : %s' % (width, e, self.profiles.extension_desc(e)), file=file)
        print('', file=file)
        print('ISA profiles', file=file)
        print('============', file=file)
        pnames = self.profiles.profile_names()
        width = max(len(e) for e in [''] + pnames)
        for pname in pnames:
            supported = pname in self.profiles.data['profiles']
            profile = None
            missing_flags = ''
            missing_exts = []
            if supported:
                profile = self.profiles.data['profiles'][pname]
                supported = self.bits == profile['bits']
            if supported:
                for f in profile['flags']['mandatory']:
                    if f not in self.flags:
                        missing_flags += f
                        supported = False
                for e in profile['extensions']['mandatory']:
                    if e not in self.extensions:
                        missing_exts.append(e)
                        supported = False
            print('  %-*s : %s' % (width, pname, 'Yes' if supported else 'No'), file=file)
            if len(missing_flags) > 0:
                print('      Missing %d flags: %s' % (len(missing_flags), missing_flags), file=file)
            if len(missing_exts) > 0:
                print('      Missing %d extensions:' % len(missing_exts), file=file)
                ewidth = max(len(e) for e in missing_exts)
                for e in missing_exts:
                    print('      %-*s : %s' % (ewidth, e, self.profiles.extension_desc(e)), file=file)
        print('', file=file)

# Main code.
if __name__ == '__main__':

    # Decode command line options.
    cmd = CommandLine(sys.argv, USAGE)
    definition_file = cmd.get_opt(['-d', '--definition'], os.path.splitext(__file__)[0] + '.yml')
    cpuinfo_file = cmd.get_opt(['-c', '--cpuinfo'], DEFAULT_CPUINFO)
    isa_pattern = cmd.get_opt(['-i', '--isa'], DEFAULT_ISAGLOB)
    cmd.check_opt_final()

    # Execute command.
    profiles = Profiles(cmd, definition_file)
    proc = Processor(profiles, cpuinfo_file, isa_pattern)
    proc.print()
