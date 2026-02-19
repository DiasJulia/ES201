#!/bin/bash
set -u -o pipefail

# ========= Config =========
MATRIX_SIZE=30

# gem5 paths
GEM5_ROOT="${GEM5_ROOT:-/home/g/gbusnot/ES201/tools/TP5/gem5-stable}"
GEM5_BIN="${GEM5_BIN:-$GEM5_ROOT/build/ARM/gem5.fast}"
GEM5_CONFIG="${GEM5_CONFIG:-$GEM5_ROOT/configs/example/se.py}"

# App
APP_BIN="${APP_BIN:-$HOME/TP5/test_omp}"

# Output 
OUTPUT_ROOT="${OUTPUT_ROOT:-.}/result"
RUN_ROOT="$OUTPUT_ROOT/m${MATRIX_SIZE}"
mkdir -p "$RUN_ROOT"

# Widths (voies)
WIDTH_LIST=(2 4 8)

# Threads
THREADS_LIST=(1 2 4 8 16)

for W in "${WIDTH_LIST[@]}"; do
  for T in "${THREADS_LIST[@]}"; do
    if [ "$T" -gt "$MATRIX_SIZE" ]; then
      continue
    fi

    OUTDIR="$RUN_ROOT/w${W}_t${T}" 
    mkdir -p "$OUTDIR"

    echo "=== Run: W=$W, T=$T, m=$MATRIX_SIZE -> $OUTDIR ==="

    echo "Comando: OMP_NUM_THREADS=$T $GEM5_BIN --outdir=$OUTDIR $GEM5_CONFIG --caches --l2cache -n $T --cpu-type=detailed --o3-width=$W -c $APP_BIN -o \"$T $MATRIX_SIZE\""

    OMP_NUM_THREADS="$T" \
    "$GEM5_BIN" --outdir="$OUTDIR" \
      "$GEM5_CONFIG" \
      --caches --l2cache \
      -n "$T" --cpu-type=detailed --o3-width="$W" \
      -c $GEM5_ROOT/../test_omp -o "$T $MATRIX_SIZE" \
      >"$OUTDIR/console.out" 2>"$OUTDIR/console.err"

    RC=$?
    if [ "$RC" -ne 0 ]; then
      echo "FALHA: w=$W t=$T (rc=$RC)"
    else
      cp "$OUTDIR/stats.txt" "$RUN_ROOT/stats_o3_w${W}_t${T}_m${MATRIX_SIZE}.txt"
      echo "OK"
    fi
  done
done