# gem5 usage instructions (TP4)

This document explains how to compile RISC-V programs, run gem5 in SE mode, and use the developed scripts.

## What is gem5

gem5 is a computer architecture simulator that lets you evaluate CPUs, caches, and memory under different configurations. In this project we use SE (System Emulation) mode, which runs a user-level RISC-V binary inside the simulator.

## Setup and installation

gem5 is already compiled in this project. The main binary is:

- /home/julia/gem5/build/RISCV/gem5.opt

If you need to rebuild (optional), use SCons with the desired ISA (RISC-V) and the opt build.

### Toolchain dependency

To compile the RISC-V benchmarks you need a cross-compiler:

- riscv64-linux-gnu-gcc (recommended on Debian/Ubuntu)
- or riscv64-unknown-linux-gnu-gcc

## How to compile and run a C program (RISC-V)

Example with the poly_mult benchmark:

1) Compile:

```
cd /home/julia/gem5/ES201-GIT/TP4/Projet/poly_mult
make
```

2) Run in gem5 (A7 example):

```
/home/julia/gem5/build/RISCV/gem5.opt \
  -d /home/julia/gem5/ES201-GIT/TP4/Projet/poly_mult/m5out_poly_mult \
  /home/julia/gem5/ES201-GIT/TP4/se_A7.py \
  --cmd=/home/julia/gem5/ES201-GIT/TP4/Projet/poly_mult/poly_mult.riscv
```

### Generated outputs

The m5out_* directory contains important files:

- stats.txt: performance metrics (IPC, cycles, miss rates, etc.)
- config.ini and config.json: full simulation configuration
- config.dot/config.dot.pdf: topology diagram

The stats.txt values are the main data used for analysis.

## Provided scripts

This folder contains scripts to automate result collection.

### l1_sweep.py

This script sweeps L1I/L1D sizes, runs gem5, and generates CSV + plots.

#### Modes

- run: executes simulations for a list of L1 sizes.
- collect: scans output directories and creates a consolidated CSV.
- plot: generates charts from the CSV.

#### bench parameter syntax

Use the format below to specify the binary and its arguments:

name:path::args

Examples:

- dijkstra:/path/dijkstra_small.riscv::/path/input.dat
- blowfish:/path/bf.riscv::e /path/input_small.asc /path/out.bin 0123456789abcdef
- /path/poly_mult.riscv (no arguments)

#### Run (A15 example)

```
python3 l1_sweep.py run --cpu A15 --gem5 ~/gem5/build/RISCV/gem5.opt --cfg se_A15.py --out-root /home/julia/gem5/ES201-GIT/TP4/Projet/results_l1 --bench "dijkstra:/home/julia/gem5/ES201-GIT/TP4/Projet/dijkstra/dijkstra_small.riscv::/home/julia/gem5/ES201-GIT/TP4/Projet/dijkstra/input.dat" --bench "blowfish:/home/julia/gem5/ES201-GIT/TP4/Projet/blowfish/bf.riscv::e input_small.asc /home/julia/gem5/ES201-GIT/TP4/Projet/blowfish/out.bin 0123456789abcdef"
```

#### Collect

```
python3 /home/julia/gem5/ES201-GIT/TP4/l1_sweep.py collect \
  --cpu A7 \
  --out-root /home/julia/gem5/ES201-GIT/TP4/Projet/results_l1 \
  --csv /home/julia/gem5/ES201-GIT/TP4/Projet/results_l1/results_A7.csv
```

#### Plot

```
python3 /home/julia/gem5/ES201-GIT/TP4/l1_sweep.py plot \
  --csv /home/julia/gem5/ES201-GIT/TP4/Projet/results_l1/results_A7.csv \
  --out-dir /home/julia/gem5/ES201-GIT/TP4/Projet/results_l1/figures_A7
```

## Understanding the plotted metrics

The l1_sweep.py script generates plots for the following performance metrics:

### IPC (Instructions Per Cycle)
- Number of instructions executed per clock cycle
- **Higher is better** → more efficient processor
- Typical range: 0.5 to 2.0 for out-of-order processors
- Shows how well the CPU exploits instruction-level parallelism

### CPI (Cycles Per Instruction)
- Number of clock cycles needed to execute one instruction
- **Lower is better** → fewer wasted cycles
- Inverse of IPC: `CPI = 1 / IPC`
- Increases with cache misses, branch mispredictions, and data hazards

### I$ miss rate (Instruction Cache miss rate)
- Percentage of instruction cache (L1I) accesses that result in a miss
- **Lower is better** → fewer stalls waiting for instructions
- Example: 0.02 = 2% miss rate
- Affects fetch bandwidth and instruction supply to the pipeline

### D$ miss rate (Data Cache miss rate)
- Percentage of data cache (L1D) accesses that result in a miss
- **Lower is better** → fewer stalls waiting for data
- Example: 0.05 = 5% miss rate
- Critical for load/store intensive workloads

### L2 miss rate
- Percentage of L2 cache accesses that miss (and go to main memory)
- **Lower is better** → fewer accesses to slow DRAM
- More critical than L1 misses due to higher memory latency penalty
- Shows effectiveness of the cache hierarchy

### Branch mispred rate (Branch misprediction rate)
- Percentage of branch instructions predicted incorrectly by the branch predictor
- **Lower is better** → fewer pipeline flushes
- Depends on branch predictor algorithm (BiMode in this configuration)
- Impacts control flow intensive code more severely

### Sim seconds (Simulated time)
- Real (simulated) time the program would take to execute on the hardware
- **Lower is better** → faster program execution
- Depends on clock frequency (1 GHz by default in gem5)
- Represents end-to-end performance including all stalls and delays

### Expected relationship with L1 size

As L1 cache size increases:
- ↓ Miss rates (I$, D$, L2)
- ↑ IPC / ↓ CPI
- ↓ Simulated execution time

However, beyond a certain point, increasing L1 size yields diminishing returns when the working set fits entirely in the cache.

### extract_inst_class_percentages.py

This script computes the percentage of each instruction class in a compiled program.

