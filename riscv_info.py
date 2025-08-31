#!/usr/bin/env python
#-----------------------------------------------------------------------------
#
#  RISCV-INFO - Collect information on RISC-V processor
#  Copyright (c) 2025, Thierry Lelegard
#  BSD-2-Clause license, see https://opensource.org/license/BSD-2-Clause
#
#-----------------------------------------------------------------------------

import os, sys, re, yaml

USAGE = """
Syntax: %s [options]

Options:

  -c filename
  --cpuinfo filename
     Use the specified file instead of /proc/cpuinfo. Useful to test alternative
     configurations.

  -d filename
  --definition filename
     Use the specified file instead of the default JSON definition file for
     RISC-V configurations which comes with that script.

  -h
  --help
     Display this help text.

  -v
  --verbose
     Display this help text.
"""


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
# Definition of RISC-V profiles and extensions.
#-----------------------------------------------------------------------------

class Profiles:

    # Constructor, load configuration from a YAML file.
    def __init__(self, cmd, definition_file):
        self.cmd = cmd
        with open(definition_file, 'r') as input:
            self.data = yaml.safe_load(input)
        self.flags = self.data.get('flags', dict())
        self.shorthands = self.data.get('shorthands', dict())
        self.extensions = self.data.get('extensions', dict())
        self.profiles = self.data.get('profiles', dict())

    # Cleanup a string of flags. Remove duplicates. Expand shorthands.
    def cleanup_flags(self, flags):
        input = flags.upper()
        clean = ''
        for s in self.shorthands.keys():
            input = input.replace(s, self.shorthands[s])
        for f in input:
            if f not in clean:
                clean += f
        return clean

    # Get the description of a flag.
    def flag_desc(self, flag):
        return self.flags[flag] if flag in self.flags.keys() else 'Unknown'

    # Get the description of an extension.
    def extension_desc(self, name):
        return self.extensions[name] if name in self.extensions.keys() else 'Unknown'

    # Get the list of profile names.
    def profiles(self):
        return list(self.profiles.keys())

#-----------------------------------------------------------------------------
# Definition of the characteristics of a RISC-V processor.
#-----------------------------------------------------------------------------

class Processor:

    # Constructor, load from a cpuinfo file.
    def __init__(self, profiles, cpuinfo_file='/proc/cpuinfo'):
        self.basename = ''     # Example: RV64GCVH
        self.bits = 0          # Example: 32, 64, 128
        self.flags = ''        # Example: IMAFDCVH
        self.extensions = []   # List of extension names
        self.profiles = profiles
        self.cmd = profiles.cmd
        with open(cpuinfo_file, 'r') as input:
            for line in input:
                # Keep only lines with 'isa' or 'hart isa'
                prefix, _, value = line.partition(':')
                if prefix.strip().lower() in ['isa', 'hart isa']:
                    # Loop on all characteristics of the processor.
                    for c in value.strip().split('_'):
                        # The base ISA is RV32xxx, RV64xxx, RV128xxx.
                        c = c.upper()
                        match = re.fullmatch(r'RV([0-9]+)(.*)', c)
                        if match is None:
                            # Not a base name, this is an extension name.
                            c = c.capitalize()
                            if c not in self.extensions:
                                self.extensions.append(c)
                        else:
                            # This is a base ISA name.
                            if self.basename == '':
                                self.basename = c
                                self.bits = int(match.group(1))
                                self.flags = self.profiles.cleanup_flags(match.group(2))
                            elif self.basename != c:
                                cmd.error('multiple base ISA: %s, %s' % (self.basename, c))
        self.extensions.sort()

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

# Main code.
if __name__ == '__main__':

    # Decode command line options.
    cmd = CommandLine(sys.argv, USAGE)
    definition_file = cmd.get_opt(['-d', '--definition'], os.path.splitext(__file__)[0] + '.yml')
    cpuinfo_file = cmd.get_opt(['-c', '--cpuinfo'], '/proc/cpuinfo')
    cmd.check_opt_final()
    
    # Execute command.
    profiles = Profiles(cmd, definition_file)
    proc = Processor(profiles, cpuinfo_file)
    proc.print()
