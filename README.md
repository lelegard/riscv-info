# RISC-V Processor Information

The Python script `riscv_info.py` displays information on the RISC-V processor
on which it runs. The displayed information is:

- Base architecture flags.
- Supported ISA extensions.
- Supported profiles.
- With option `--verbose` or `-v`, for each unsupported profile, display the
  list of missing extensions for that profile.

Options `--list-extensions`, `--list-profiles`, and `--profile` can be used to
list known extensions or profiles, regardless of the current processor.

Limitations:

- Works on Linux only.
- Tested on Qemu emulated RISC-V processors only.
- The list of extensions in the YAML file is probably incomplete.
  Feel free to submit a pull request with missing names.

## Usage

~~~
Syntax: riscv_info.py [options]

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

  -e
  --list-extensions
     List known extensions.

  -h
  --help
     Display this help text.

  -i pattern
  --isa
     Use the specified file pattern, with optional wildcards, for the
     'riscv,isa-extensions' pseudo files.
     Useful to test alternative configurations.
     Default: /proc/device-tree/cpus/*/riscv,isa-extensions

  -l
  --list-profiles
     List known profiles.

  -p name
  --profile name
     Display the characteristics of the specified profile.

  -v
  --verbose
     Verbose display.
~~~

## Testing on other architectures

The script uses `/proc/cpuinfo` and `/proc/device-tree/cpus/*/riscv,isa-extensions`
on the RISC-V system. You can copy these pseudo-files from a RISC-V system on another
system and run the script there using options `--cpuinfo` and `--isa`.

Example:
~~~
$ scp vmriscv:/proc/cpuinfo cpuinfo.qemu.riscv
$ scp vmriscv:/proc/device-tree/cpus/cpu@0/riscv,isa-extensions isa-extensions.qemu.riscv
$ ./riscv_info.py --cpuinfo cpuinfo.qemu.riscv --isa isa-extensions.qemu.riscv
~~~

The directory `test` in this repository contains sample input and output files for
the following configurations:

- Ubuntu 25.04 on a Qemu system with default CPU.
- Ubuntu 25.04 on a Qemu system with `-cpu rva23s64` (RVA23 profile).
- Ubuntu 25.04 on a Qemu system with `-cpu max`.

## Prerequisite: PyYAML Python module

Install on Ubuntu:
~~~
sudo apt install python3-yaml
~~~

Install on macOS: The PyYAML module has been deprecated in HomeBrew for obscure reasons.
Use a Python virtual environment.

Example:
~~~
$ mkdir ~/.venv
$ python3 -m venv ~/.venv
$ source ~/.venv/bin/activate
(.venv) $ python3 -m pip install pyyaml
(.venv) $ ./riscv_info.py --cpuinfo cpuinfo.qemu.riscv
(.venv) $ deactivate
$
~~~
