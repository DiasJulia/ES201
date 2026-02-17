# Technical Guide: Multicore Performance Analysis (TP5)

## Context

Due to compatibility issues with m5threads on recent Linux kernels, this lab must be performed using the ENSTA infrastructure via SSH. **Do not attempt to compile Gem5 locally.**

---

## 1. Environment Setup (Critical Step)

Every team member must perform this step to access the simulation tools.

### SSH Connection

Connect to the school gateway and then jump to a lab machine (e.g., `salle`):

```bash
ssh <your_username>@ssh.ensta.fr -t salle
# Note: You may need to enter your password twice.
```

### Environment Variables

Once logged in, define the path to the stable Gem5 artifacts. **You must do this every time you log in.**

```bash
# 1. Create a workspace (if not already done)
mkdir -p ~/tp5_work
cd ~/tp5_work

# 2. Export the GEM5 path variable (Points to the pre-compiled tools)
export GEM5=/home/g/gbusnot/ES201/tools/TP5/gem5-stable
```

---

## 2. Simulation Command Reference

The simulation uses the ARM architecture (`gem5.fast`) and the Syscall Emulation script (`se.py`).

### Standard Command Template

```bash
$GEM5/build/ARM/gem5.fast $GEM5/configs/example/se.py \
    --cpu-type=<CPU_MODEL> \
    --caches --l2cache \
    -n <CORES> \
    -c $GEM5/../test_omp \
    -o "<THREADS> <MATRIX_SIZE>"
```

### Key Parameters

| Parameter | Description |
|-----------|-------------|
| `--cpu-type` | `MinorCPU`: In-Order processors (Cortex-A7 style)<br/>`DerivO3CPU`: Out-of-Order processors (Cortex-A15 style) |
| `-n <CORES>` | Number of physical cores (must match thread count in `-o`) |
| `-c ...` | Path to pre-compiled matrix multiplication binary (`test_omp`) |
| `-o "<THREADS> <SIZE>"` | C++ program arguments: thread count and matrix size<br/>Example: `-o "4 128"` runs 4 threads on a 128×128 matrix |

---

## 3. Team Task Division (3 Members)

To complete the lab efficiently, split the workload as follows. **Share your `stats.txt` files after every run.**

### Member 1: Infrastructure & In-Order Baseline

**Focus:** Verify SSH access and analyze the "Little" cores (Cortex-A7 style).

**Tasks:**

1. **Sanity Check:** Run with `-n 1 -o "1 64"` to verify the simulator works.
2. **Experiment A (Scaling):** Run `MinorCPU` with 1, 2, 4, and 8 cores.
   - Matrix size: Fixed at 128 (e.g., `-o "N 128"`)
3. **Data Extraction:** For each run, record:
   - `sim_seconds` (total execution time)
   - `system.cpu.ipc` (Instructions Per Cycle)
4. **Analysis (Q4–Q8):**
   - Identify the bottleneck core
   - Explain why speedup isn't perfectly linear (bus contention, cache effects)

### Member 2: High-Performance Architecture

**Focus:** Analyze the "Big" cores (Cortex-A15 style) and architectural parameters.

**Tasks:**

1. **Experiment B (O3 Performance):** Run `DerivO3CPU` with 1, 2, 4, and 8 cores.
   - Matrix size: Fixed at 128
2. **Experiment C (Deep Dive):** Optional—compare `MinorCPU` vs `DerivO3CPU` on a larger matrix (e.g., 256×256) with 1 core to see raw architectural differences.
3. **Data Extraction:** Record:
   - `sim_seconds`
   - `system.cpu.ipc`
   - `system.l2.overall_miss_rate`
4. **Analysis (Q9–Q12):**
   - Does Out-of-Order execution hide memory latency effectively?
   - Compare speedup curves: O3 vs MinorCPU

### Member 3: Theory & System Synthesis

**Focus:** Theoretical answers, cache coherence, and final report compilation.

**Tasks:**

1. **Theoretical Analysis (Q1):** Explain the MESI protocol in the context of matrix multiplication.
   - Matrix B: read-only (Shared state)
   - Matrix C: written (Modified state)
   - Address "False Sharing" when threads write to adjacent memory addresses

2. **Efficiency Analysis (Q13):**
   - Assume an O3 core takes ~4× the silicon area of a MinorCPU
   - Calculate Performance / Area for both architectures
   - Determine which is better for parallel tasks

3. **Super-Linear Speedup (Q14):**
   - Check Members 1 & 2's data: Did 2 or 4 cores provide >2× or >4× speedup?
   - Explanation: Matrix may be too large for one L1 cache but fit perfectly when split across multiple L1 caches

---

## 4. Report Content & Checklist

The final PDF report should consolidate these findings:

### 1. Introduction
- Briefly explain the move to SSH/ARM simulation due to m5threads constraints
- Define the objective: Comparing In-Order vs Out-of-Order scaling

### 2. Theoretical Framework
- Diagram of the bus-based architecture
- Explanation of cache coherence traffic during matrix multiplication

### 3. Experimental Results
- **Plot 1:** Execution Time vs Number of Cores (MinorCPU vs DerivO3CPU)
- **Plot 2:** Speedup vs Ideal Linear Speedup
- **Table:** IPC values for single-core vs multi-core configurations

### 4. Advanced Discussion
- **Area Efficiency:** Show that a cluster of many MinorCPUs is likely more area-efficient for this parallel task than fewer DerivO3CPUs
- **Super-Linear Speedup:** If observed, explain the cache capacity effect

---

## 5. Quick Commands Cheat Sheet

Copy-paste these into your terminal:

```bash
# Set Path
export GEM5=/home/g/gbusnot/ES201/tools/TP5/gem5-stable

# Run MinorCPU (In-Order) - 2 Cores
$GEM5/build/ARM/gem5.fast $GEM5/configs/example/se.py \
  --cpu-type=MinorCPU --caches --l2cache -n 2 \
  -c $GEM5/../test_omp -o "2 128"

# Run DerivO3CPU (Out-of-Order) - 2 Cores
$GEM5/build/ARM/gem5.fast $GEM5/configs/example/se.py \
  --cpu-type=DerivO3CPU --caches --l2cache -n 2 \
  -c $GEM5/../test_omp -o "2 128"

# View Stats
grep -E "sim_seconds|system.cpu.ipc|overall_miss_rate" m5out/stats.txt
```

---

**Last Updated:** February 17, 2026
