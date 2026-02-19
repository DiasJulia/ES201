#!/bin/bash
set -u -o pipefail

MATRIX_SIZE=30

RUN_ROOT="${1:-.}/result/m${MATRIX_SIZE}"
OUT_FILE="${RUN_ROOT}/results.txt"

echo "📊 Coletando resultados de: $RUN_ROOT"

{
  for file in "$RUN_ROOT"/stats_o3_w*_t*_m*.txt; do
    [ -f "$file" ] || continue
    echo "=== $file ==="
    
    # sim_seconds
    grep -m1 "sim_seconds" "$file" 2>/dev/null || true
    
    # IPC máximo (aceita system.cpu ou system.cpu0, etc, ou system.cpu.ipc_total)
    grep -E "system\.cpu[0-9]*\.ipc" "$file" 2>/dev/null | awk '{print $2}' | sort -n | tail -1 | \
      { read val; [ -n "$val" ] && echo "ipc_max $val" || true; }
    
    # numCycles máximo
    grep -E "system\.cpu[0-9]*\.numCycles" "$file" 2>/dev/null | awk '{print $2}' | sort -n | tail -1 | \
      { read val; [ -n "$val" ] && echo "cycles_max $val" || true; }
    
    # numInsts ou committedInsts máximo
    grep -E "system\.cpu[0-9]*\.(numInsts|committedInsts)" "$file" 2>/dev/null | awk '{print $2}' | \
      sort -n | tail -1 | { read val; [ -n "$val" ] && echo "insts_max $val" || true; }
    
    # sim_ticks
    grep -m1 "sim_ticks" "$file" 2>/dev/null || true
    
  done
} > "$OUT_FILE"

echo "✅ Resumo salvo em: $OUT_FILE"
head -20 "$OUT_FILE"
set -u -o pipefail

RUN_ROOT="${1:-.}/result/m${MATRIX_SIZE}"
OUT_FILE="${RUN_ROOT}/results.txt"

  for file in "$RUN_ROOT"/stats_o3_w*_t*_m*.txt; do
    [ -f "$file" ] || continue
    echo "=== $file ==="
    
    # sim_seconds
    grep -m1 "sim_seconds" "$file" 2>/dev/null || true
    
    # IPC máximo (aceita system.cpu ou system.cpu0, etc, ou system.cpu.ipc_total)
    grep -E "system\.cpu[0-9]*\.ipc" "$file" 2>/dev/null | awk '{print $2}' | sort -n | tail -1 | \
      { read val; [ -n "$val" ] && echo "ipc_max $val" || true; }
    
    # numCycles máximo
    grep -E "system\.cpu[0-9]*\.numCycles" "$file" 2>/dev/null | awk '{print $2}' | sort -n | tail -1 | \
      { read val; [ -n "$val" ] && echo "cycles_max $val" || true; }
    
    # numInsts ou committedInsts máximo
    grep -E "system\.cpu[0-9]*\.(numInsts|committedInsts)" "$file" 2>/dev/null | awk '{print $2}' | \
      sort -n | tail -1 | { read val; [ -n "$val" ] && echo "insts_max $val" || true; }
    
    # sim_ticks
    grep -m1 "sim_ticks" "$file" 2>/dev/null || true
    
  done

cp "$OUT_FILE" "$RUN_ROOT/../../results.txt"
echo "✅ Resumo salvo em: $RUN_ROOT/../../results.txt"