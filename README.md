# RISC-V Processor Information

The Python script `riscv_info.py` displays information on the RISC-V processor on which it runs.

Note: Linux only, tested on Qemu only.

Prerequisite: PyYAML Python module.

- On Ubuntu: `sudo apt install python3-yaml`
- On macOS, for test, using `--cpuinfo` option: use a Python virtual environment, see example below.

~~~
$ mkdir ~/.venv
$ python3 -m venv ~/.venv
$ source ~/.venv/bin/activate
(.venv) $ python3 -m pip install pyyaml
(.venv) $ python -q
>>> import yaml
>>> yaml.__version__
'6.0.2'
>>> 
(.venv) $ deactivate 
$ 
~~~
