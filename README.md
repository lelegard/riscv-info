# RISC-V Processor Information

The Python script `riscv_info.py` displays information on the RISC-V processor on which it runs.

Limitations:
- Works on Linux only.
- Tested on Qemu emulated RISC-V processors only.
- The list of extensions in the YAML file is incomplete.

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
~~~

## Testing on other architectures

The script uses the `/proc/cpuinfo` of the RISC-V system. You can copy that pseudo-file
from a RISC-V system as a text file on another system and run the script there using
option `--cpuinfo` (or `-c`).

Example:
~~~
$ scp vmriscv:/proc/cpuinfo cpuinfo.qemu.riscv
$ scp vmriscv:/proc/device-tree/cpus/cpu@0/riscv,isa-extensions isa-extensions.qemu.riscv
$ ./riscv_info.py --cpuinfo cpuinfo.qemu.riscv --isa isa-extensions.qemu.riscv
~~~

The directory `test` in this repository contains the following sample files:

- `cpuinfo.qemu.default`: collected on Ubuntu 25.04 on a Qemu system with default CPU.
- `cpuinfo.qemu.rva23s64`: collected on Ubuntu 25.04 on a Qemu system with `-cpu rva23s64` (RVA23 profile).
- `cpuinfo.qemu.cpumax`: collected on Ubuntu 25.04 on a Qemu system with `-cpu max`.

The corresponding output files are provided.

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
