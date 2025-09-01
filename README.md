# RISC-V Processor Information

The Python script `riscv_info.py` displays information on the RISC-V processor on which it runs.

Limitations:
- Works on Linux only.
- Tested on Qemu emulated RISC-V processors only.

## Testing on other architectures

The script uses the `/proc/cpuinfo` of the RISC-V system. You can copy that pseudo-file
from a RISC-V system as a text file on another system and run the script there using
option `--cpuinfo` (or `-c`).

Example:
~~~
$ scp vmriscv:/proc/cpuinfo cpuinfo.qemu.riscv
$ ./riscv_info.py --cpuinfo cpuinfo.qemu.riscv
~~~

The repository contains the following sample files:

- `cpuinfo.qemu.default`: collected on Ubuntu 25.04 on a Qemu system with default CPU.
- `cpuinfo.qemu.cpumax`: collected on Ubuntu 25.04 on a Qemu system with `-cpu max`.

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
