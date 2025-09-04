#!/usr/bin/env python
#-----------------------------------------------------------------------------
#
#  RISCV-INFO - Collect information on RISC-V processor
#  Copyright (c) 2025, Thierry Lelegard
#  BSD-2-Clause license, see https://opensource.org/license/BSD-2-Clause
#
#-----------------------------------------------------------------------------

import os, sys, re, glob, yaml, argparse

DEFAULT_CPUINFO = '/proc/cpuinfo'
DEFAULT_ISAGLOB = '/proc/device-tree/cpus/*/riscv,isa-extensions'

#-----------------------------------------------------------------------------
# Force a default value to a dictionary key, with several levels of keys.
#-----------------------------------------------------------------------------

def set_default(dictionary, keys, default):
    # Make sure that keys is a list of strings.
    if type(keys) is str:
        keys = [keys]
    if type(keys) is not list or len(keys) == 0:
        return
    # Check or create all intermediate levels of dictionaries.
    d = dictionary
    for i in range(len(keys) - 1):
        k = keys[i]
        if k not in d or d[k] is None:
            d[k] = dict()
        d = d[k]
    # Check or create the last level.
    k = keys[-1]
    if k not in d or d[k] is None:
        d[k] = default

#-----------------------------------------------------------------------------
# Definition of RISC-V profiles and extensions.
#-----------------------------------------------------------------------------

class Profiles:

    # Constructor, load configuration from a YAML file.
    def __init__(self, args):
        self.args = args
        # Load the YAML configuration file.
        with open(self.args.definition, 'r') as input:
            self.data = yaml.safe_load(input)
        # Enforce default values.
        set_default(self.data, 'flags', dict())
        set_default(self.data, 'shorthands', dict())
        set_default(self.data, 'extensions', dict())
        set_default(self.data, 'profiles', dict())
        for name in self.data['profiles']:
            set_default(self.data, ['profiles', name, 'description'], '')
            set_default(self.data, ['profiles', name, 'bits'], 0)
            set_default(self.data, ['profiles', name, 'endian'], 'any')
            set_default(self.data, ['profiles', name, 'flags', 'mandatory'], '')
            set_default(self.data, ['profiles', name, 'flags', 'optional'], '')
            set_default(self.data, ['profiles', name, 'extensions', 'mandatory'], dict())
            set_default(self.data, ['profiles', name, 'extensions', 'optional'], dict())

    # Cleanup a string of flags. Remove duplicates. Expand shorthands.
    # Return the clean list of flags.
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

    # Get the description of a profile.
    def profile_desc(self, name):
        return self.data['profiles'][name]['description'] if name in self.data['profiles'] else 'Unknown'

    # Get the list of profile names.
    def profile_names(self):
        return list(self.data['profiles'].keys())

    # List all registered profiles.
    def list_profiles(self, file=sys.stdout):
        width = max(len(e) for e in self.data['profiles'])
        for name in self.data['profiles']:
            print('  %-*s : %s' % (width, name, self.profile_desc(name)), file=file)

    # List all registered extensions.
    def list_extensions(self, file=sys.stdout):
        width = max(len(e) for e in self.data['extensions'])
        for name in self.data['extensions']:
            print('  %-*s : %s' % (width, name, self.extension_desc(name)), file=file)

    # Print a description of a profile.
    def print_profile(self, name, file=sys.stdout):
        name = name.upper()
        if name not in self.data['profiles']:
            args.parser.error('unknown profile %s, use one of %s' % (name, ', '.join(self.data['profiles'].keys())))
        prof = self.data['profiles'][name]
        print('', file=file)
        print('%s: %s' % (name, prof['description']), file=file)
        print('Data: %d-bit, %s-endian' % (prof['bits'], prof['endian']), file=file)
        for tp in ['mandatory', 'optional']:
            if len(prof['flags'][tp]) > 0:
                print('', file=file)
                print('%s base architecture:' % tp.capitalize(), file=file)
                for f in prof['flags'][tp]:
                    print('  %s: %s' % (f, self.flag_desc(f)), file=file)
        for tp in ['mandatory', 'optional']:
            if len(prof['extensions'][tp]) > 0:
                print('', file=file)
                print('%s extensions:' % tp.capitalize(), file=file)
                width = max(len(e) for e in prof['extensions'][tp])
                for f in prof['extensions'][tp]:
                    print('  %-*s : %s' % (width, f, self.extension_desc(f)), file=file)
        print('', file=file)

#-----------------------------------------------------------------------------
# Definition of the characteristics of a RISC-V processor.
#-----------------------------------------------------------------------------

class Processor:

    # Constructor, load from a cpuinfo file.
    def __init__(self, profiles):
        self.basename = ''     # Example: RV64GCVH
        self.bits = 0          # Example: 32, 64, 128
        self.flags = ''        # Example: IMAFDCVH
        self.extensions = []   # List of extension names
        self.profiles = profiles
        self.args = profiles.args
        # Parse /proc/cpuinfo
        with open(args.cpuinfo, 'r') as input:
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
                                print('error: multiple base ISA: %s, %s' % (self.basename, c), file=sys.stderr)
        # Parse /proc/device-tree/cpus/*/riscv,isa-extensions
        for isa_file in glob.glob(args.isa):
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
    def print_processor(self, file=sys.stdout):
        print('', file=file)
        print('Base architecture', file=file)
        print('=================', file=file)
        print('%s (%d bits)' % (self.basename, self.bits), file=file)
        for f in self.flags:
            print('  %s: %s' % (f, self.profiles.flag_desc(f)), file=file)
        if self.args.verbose:
            missing_flags = [f for f in self.profiles.data['flags'] if f not in self.flags]
            if len(missing_flags) > 0:
                print('', file=file)
                print('Unimplemented flags', file=file)
                for f in missing_flags:
                    print('  %s: %s' % (f, self.profiles.flag_desc(f)), file=file)
        print('', file=file)
        print('ISA extensions', file=file)
        print('==============', file=file)
        width = max(len(e) for e in [''] + self.extensions)
        print('Found %d extensions' % len(self.extensions), file=file)
        for e in self.extensions:
            print('  %-*s : %s' % (width, e, self.profiles.extension_desc(e)), file=file)
        if self.profiles.args.verbose:
            missing_exts = [e for e in self.profiles.data['extensions'] if e not in self.extensions]
            if len(missing_exts) > 0:
                width = max(len(e) for e in missing_exts)
                print('', file=file)
                print('%d unimplemented extensions' % len(missing_exts), file=file)
                for e in missing_exts:
                    print('  %-*s : %s' % (width, e, self.profiles.extension_desc(e)), file=file)
            
        print('', file=file)
        print('ISA profiles', file=file)
        print('============', file=file)
        pnames = self.profiles.profile_names()
        width = max(len(e) for e in [''] + pnames)
        for pname in pnames:
            supported = pname in self.profiles.data['profiles']
            if supported:
                profile = self.profiles.data['profiles'][pname]
                missing_flags = ''.join([f for f in profile['flags']['mandatory'] if f not in self.flags])
                missing_opt_flags = ''.join([f for f in profile['flags']['optional'] if f not in self.flags])
                missing_exts = [e for e in profile['extensions']['mandatory'] if e not in self.extensions]
                missing_opt_exts = [e for e in profile['extensions']['optional'] if e not in self.extensions]
                supported = self.bits == profile['bits'] and len(missing_flags) == 0 and len(missing_exts) == 0
            else:
                missing_flags = ''
                missing_opt_flags = ''
                missing_exts = []
                missing_opt_exts = []
            print('  %-*s : %s' % (width, pname, 'Yes' if supported else 'No'), file=file)
            if self.args.verbose:
                if len(missing_flags) > 0:
                    print('  - Missing %d mandatory flags: %s' % (len(missing_flags), missing_flags), file=file)
                if len(missing_opt_flags) > 0:
                    print('  - Missing %d optional flags: %s' % (len(missing_opt_flags), missing_opt_flags), file=file)
                ewidth = max(len(e) for e in [''] + missing_exts + missing_opt_exts)
                if len(missing_exts) > 0:
                    print('  - Missing %d mandatory extensions:' % len(missing_exts), file=file)
                    for e in missing_exts:
                        print('    %-*s : %s' % (ewidth, e, self.profiles.extension_desc(e)), file=file)
                if len(missing_opt_exts) > 0:
                    print('  - Missing %d optional extensions:' % len(missing_opt_exts), file=file)
                    for e in missing_opt_exts:
                        print('    %-*s : %s' % (ewidth, e, self.profiles.extension_desc(e)), file=file)
        print('', file=file)

# Main code.
if __name__ == '__main__':

    # Decode command line options.
    parser = argparse.ArgumentParser(description='Get RISC-V ISA information')
    parser.add_argument('-c', '--cpuinfo', default=DEFAULT_CPUINFO, help=
                        'Use the specified file for "cpuinfo" pseudo file. ' +
                        'Useful to test alternative configurations. ' +
                        'Default: /proc/cpuinfo')
    parser.add_argument('-i', '--isa', default=DEFAULT_ISAGLOB, help=
                        'Use the specified file pattern, with optional wildcards, ' +
                        'for the "riscv,isa-extensions" pseudo files. ' +
                        'Useful to test alternative configurations. ' +
                        'Default: /proc/device-tree/cpus/*/riscv,isa-extensions')
    parser.add_argument('-d', '--definition', default=os.path.splitext(__file__)[0] + '.yml', help=
                        'Use the specified file instead of the default YAML definition ' +
                        'file for RISC-V configurations which comes with that script.')
    parser.add_argument('-e', '--list-extensions', action='store_true', help=
                        'List known extensions.')
    parser.add_argument('-l', '--list-profiles', action='store_true', help=
                        'List known profiles.')
    parser.add_argument('-p', '--profile', help=
                        'Display the characteristics of the specified profile.')
    parser.add_argument('-v', '--verbose', action='store_true', help=
                        'Verbose display.')
    args = parser.parse_args()
    args.parser = parser

    # Execute command.
    profiles = Profiles(args)
    if args.list_profiles:
        profiles.list_profiles()
    elif args.list_extensions:
        profiles.list_extensions()
    elif args.profile is not None:
        profiles.print_profile(args.profile)
    else:
        proc = Processor(profiles)
        proc.print_processor()
