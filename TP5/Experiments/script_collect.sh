#!/bin/bash
set -u -o pipefail

# ========= Config =========
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_ROOT="${RESULTS_ROOT:-${SCRIPT_DIR}/results}"
STATE_FILE="${STATE_FILE:-${RESULTS_ROOT}/state.tsv}"
OUTPUT_FILE="${OUTPUT_FILE:-${SCRIPT_DIR}/results.txt}"

echo "📊 Coletando resultados de: $RESULTS_ROOT"

if [[ ! -f "${STATE_FILE}" ]]; then
  echo "❌ Erro: state.tsv não encontrado em ${STATE_FILE}"
  exit 1
fi

{
  echo "=== Gem5 Q9 Results Summary ==="
  echo "Generated: $(date)"
  echo ""
  
  # Read state file and process DONE runs
  tail -n +2 "${STATE_FILE}" | while IFS=$'\t' read -r size width threads status outdir log; do
    if [[ "${status}" != "DONE" ]]; then
      continue
    fi
    
    stats_file="${outdir}/stats.txt"
    
    if [[ ! -f "${stats_file}" ]]; then
      echo "WARNING: Missing stats.txt for size=${size} width=${width} threads=${threads}"
      continue
    fi
    
    echo "=== size=${size} width=${width} threads=${threads} ==="
    echo "file: ${stats_file}"
    
    # Extract key metrics
    grep -m1 "^sim_seconds" "${stats_file}" 2>/dev/null || echo "sim_seconds N/A"
    grep -m1 "^sim_ticks" "${stats_file}" 2>/dev/null || echo "sim_ticks N/A"
    
    # IPC max (multi-core: max across cpus)
    ipc_max=$(grep -E "^system\.cpu[0-9]*\.ipc\s" "${stats_file}" 2>/dev/null | \
      awk '{print $2}' | sort -n | tail -1)
    if [[ -n "${ipc_max}" ]]; then
      echo "ipc_max ${ipc_max}"
    else
      echo "ipc_max N/A"
    fi
    
    # Cycles max
    cycles_max=$(grep -E "^system\.cpu[0-9]*\.numCycles\s" "${stats_file}" 2>/dev/null | \
      awk '{print $2}' | sort -n | tail -1)
    if [[ -n "${cycles_max}" ]]; then
      echo "cycles_max ${cycles_max}"
    else
      echo "cycles_max N/A"
    fi
    
    # Insts max
    insts_max=$(grep -E "^system\.cpu[0-9]*\.(numInsts|committedInsts)\s" "${stats_file}" 2>/dev/null | \
      awk '{print $2}' | sort -n | tail -1)
    if [[ -n "${insts_max}" ]]; then
      echo "insts_max ${insts_max}"
    else
      echo "insts_max N/A"
    fi
    
    echo ""
  done
  
} > "${OUTPUT_FILE}"

echo "✅ Resumo salvo em: ${OUTPUT_FILE}"
echo ""
echo "Primeiras 30 linhas:"
head -30 "${OUTPUT_FILE}"