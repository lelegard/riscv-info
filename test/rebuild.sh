#!/usr/bin/env bash
cd $(dirname "$0")
for cpuinfo in cpuinfo.qemu.*; do
    suffix=${cpuinfo##*.}
    isa=isa-extensions.qemu.$suffix
    ../riscv_info.py --cpuinfo $cpuinfo --isa $isa >output.qemu.$suffix
    ../riscv_info.py --cpuinfo $cpuinfo --isa $isa --verbose >verbose.qemu.$suffix
done
