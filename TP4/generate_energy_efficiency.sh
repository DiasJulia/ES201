#!/bin/bash
# Script para gerar dados e gráficos de eficiência energética

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
RESULTS_DIR="$SCRIPT_DIR/Projet/results_l1"

echo "=== Gerando eficiência energética para Cortex A7 ==="
python3 "$SCRIPT_DIR/energy_efficiency.py" \
  --cpu A7 \
  --input-csv "$RESULTS_DIR/results_A7.csv" \
  --output-csv "$RESULTS_DIR/efficiency_a7.csv" \
  --output-dir "$RESULTS_DIR/figures_energy"

echo ""
echo "=== Gerando eficiência energética para Cortex A15 ==="
python3 "$SCRIPT_DIR/energy_efficiency.py" \
  --cpu A15 \
  --input-csv "$RESULTS_DIR/results_A15.csv" \
  --output-csv "$RESULTS_DIR/efficiency_a15.csv" \
  --output-dir "$RESULTS_DIR/figures_energy"

echo ""
echo "=== Combinando resultados ==="
# Combinar os CSVs de A7 e A15
python3 << 'PYTHON_SCRIPT'
import csv
from pathlib import Path

results_dir = Path("Projet/results_l1")
a7_csv = results_dir / "efficiency_a7.csv"
a15_csv = results_dir / "efficiency_a15.csv"
combined_csv = results_dir / "efficiency_combined.csv"

rows = []
for csv_file in [a7_csv, a15_csv]:
    with csv_file.open("r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)

if rows:
    with combined_csv.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    print(f"Eficiência combinada escrita em {combined_csv}")
else:
    print("Nenhuma linha para combinar")

PYTHON_SCRIPT

echo ""
echo "✓ Processamento concluído! Gráficos disponíveis em $RESULTS_DIR/figures_energy/"
