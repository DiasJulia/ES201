`#` Section 3 — DerivO3CPU (matrix 32)

On se propose dans cette partie d’étudier une architecture multiprocesseur de type CMP à base de cœurs équivalents au Cortex A15 étudié dans le TD/TP5. Dans notre simulateur gem5, on dispose d’un modèle de processeur superscalaire out-of-order : le modèle o3 (--cpu-type=detailed) 

En fixant la taille de la matrice à m, et en faisant varier le nombre de threads parallèles de l'application (nombre de threads = 1, 2, 4, 8, 16, …, m), et la largeur du processeur superscalaire (nombre de voies = 2, 4, 8), répondre aux questions suivantes :

## Comandos de execução (conforme o enunciado)

> Obs.: fixe a matriz em `m` e varíe **threads** (1, 2, 4, 8, 16, …, m) e **largura superscalar** (2, 4, 8). Mantém os `stats.txt` em `results/`.

```bash
# Ajuste aqui
m=32
threads_list="1 2 4 8 16"
width_list="2 4 8"

mkdir -p results

for width in $width_list; do
  for threads in $threads_list; do
    # Evita executar threads > m (se m for pequeno)
    if [ "$threads" -gt "$m" ]; then
      continue
    fi

    outdir="results/o3_w${width}_t${threads}_m${m}"

    $GEM5/build/ARM/gem5.fast -d "$outdir" \
      $GEM5/configs/example/se.py \
      --cpu-type=DerivO3CPU --caches --l2cache -n "$threads" \
      -w "$width" \
      -c $GEM5/../test_omp -o "$threads $m"

    cp "$outdir"/stats.txt "results/stats_o3_w${width}_t${threads}_m${m}.txt"
  done
done
```

## Coleta de resultados

```bash
out_file="results/summary_o3.txt"
{
  for file in results/stats_o3_w*_t*_m*.txt; do
    echo "=== $file ==="
    grep "sim_seconds\|system.cpu.ipc\|overall_miss_rate" "$file"
  done
} > "$out_file"
echo "Resumo salvo em $out_file"
```

## Para copiar o arquivo gerado

```bash
scp -J julia-ellen.dias@ssh.ensta.fr julia-ellen.dias@salle:tp5_work/results/summary_o3.txt ./results.txt
```