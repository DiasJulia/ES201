# 📄 Explicação do Arquivo `O3CPU.py`

## **O QUE É ESTE ARQUIVO?**

Este é um **arquivo de configuração Python** do GEM5 que define os **parâmetros microarquiteturais** da CPU `DerivO3CPU` (a CPU Out-of-Order que você está usando no TP5).

Pense nele como um "blueprint" ou "receita" que especifica:
- Quantos registradores físicos tem a CPU?
- Qual é a largura do pipeline (fetch width, decode width, etc.)?
- Tamanho das filas de instrução?
- Como gerenciar dependências de memória?

---

## **COMO É USADO NO TP5?**

Quando você executa:

```bash
$GEM5/build/ARM/gem5.fast $GEM5/configs/example/se.py \
  --cpu-type=DerivO3CPU \
  --caches --l2cache \
  -n 4 \
  -c $GEM5/../test_omp -o "4 64"
```

O que acontece é:
1. O `se.py` procura pela classe `DerivO3CPU` 
2. Carrega os **parâmetros padrão** deste arquivo `O3CPU.py
`
3. Instancia 4 cópias dessa CPU (por `-n 4`)
4. Executa a simulação com esses parâmetros

---

## **ESTRUTURA GERAL**

```python
class DerivO3CPU(BaseCPU):
    type = 'DerivO3CPU'
    # ... todos os parâmetros abaixo
```

A classe `DerivO3CPU` **herda** de `BaseCPU`, ou seja, já tem alguns parâmetros básicos, mas adiciona os específicos do pipeline Out-of-Order.

---

## **OS PARÂMETROS PRINCIPAIS (AGRUPADOS POR CATEGORIA)**

### **1️⃣ CONFIGURAÇÃO GERAL**

```python
activity = Param.Unsigned(0, "Initial count")
cachePorts = Param.Unsigned(200, "Cache Ports")
```

- `cachePorts`: Quantas requisições simultâneas à cache?
  - 200 = bastante generoso (não é o gargalo)
  - Importante para multicore: cada core precisa acessar cache

---

### **2️⃣ PIPELINE - ESTÁGIOS E LATÊNCIAS**

O pipeline Out-of-Order tem 5 estágios principais:

```
FETCH → DECODE → RENAME → IEW (Issue/Execute/Writeback) → COMMIT
```

#### **FETCH (buscar instruções)**

```python
decodeToFetchDelay = Param.Cycles(1, "Decode to fetch delay")
renameToFetchDelay = Param.Cycles(1, "Rename to fetch delay")
iewToFetchDelay = Param.Cycles(1, "Issue/Execute/Writeback to fetch delay")
commitToFetchDelay = Param.Cycles(1, "Commit to fetch delay")
fetchWidth = Param.Unsigned(8, "Fetch width")
fetchBufferSize = Param.Unsigned(64, "Fetch buffer size in bytes")
fetchQueueSize = Param.Unsigned(32, "Fetch queue size in micro-ops")
```

- `fetchWidth = 8`: Busca **8 instruções por ciclo**
- `fetchQueueSize = 32`: Buffer que armazena até 32 micro-ops aguardando decodificação

#### **DECODE (decodificar instruções)**

```python
decodeWidth = Param.Unsigned(8, "Decode width")
fetchToDecodeDelay = Param.Cycles(1, "Fetch to decode delay")
renameToDecodeDelay = Param.Cycles(1, "Rename to decode delay")
```

- `decodeWidth = 8`: Decodifica **8 instruções por ciclo**
- Latência de 1 ciclo entre etapas

#### **RENAME (renomeação de registradores)**

```python
renameWidth = Param.Unsigned(8, "Rename width")
renameToDecodeDelay = Param.Cycles(1, "Rename to decode delay")
decodeToRenameDelay = Param.Cycles(1, "Decode to rename delay")
iewToRenameDelay = Param.Cycles(1, "Issue/Execute/Writeback to rename delay")
commitToRenameDelay = Param.Cycles(1, "Commit to rename delay")
```

- **Por que "rename"?** Para permitir execução fora-de-ordem sem conflitos falsos
- Se temos `mov rax, 1` seguido de `add rax, 2`, renaming faz:
  - `mov p0, 1` (registrador físico 0)
  - `add p1, p0, 2` (registrador físico 1)
  - Permitem executar "fora de ordem" sem conflitos

#### **IEW (Issue/Execute/Writeback)**

```python
issueWidth = Param.Unsigned(8, "Issue width")
issueToExecuteDelay = Param.Cycles(1, "Issue to execute delay")
wbWidth = Param.Unsigned(8, "Writeback width")
dispatchWidth = Param.Unsigned(8, "Dispatch width")
```

- `issueWidth = 8`: **8 instruções podem ser lançadas por ciclo**
- Isso permite paralelismo real (múltiplas instruções executando simultaneamente)

#### **COMMIT (confirmar resultados)**

```python
commitWidth = Param.Unsigned(8, "Commit width")
squashWidth = Param.Unsigned(8, "Squash width")
```

- Confirma resultados de até 8 instruções por ciclo
- `squashWidth`: Quantas instruções descartar se houver erro (branch misprediction)

---

### **3️⃣ MEMÓRIA E DEPENDÊNCIAS**

```python
LQEntries = Param.Unsigned(32, "Number of load queue entries")
SQEntries = Param.Unsigned(32, "Number of store queue entries")
LSQDepCheckShift = Param.Unsigned(4, "Number of places to shift addr before check")
LSQCheckLoads = Param.Bool(True, "Should dependency violations be checked...")
store_set_clear_period = Param.Unsigned(250000, "Number of load/store insts...")
LFSTSize = Param.Unsigned(1024, "Last fetched store table size")
SSITSize = Param.Unsigned(1024, "Store set ID table size")
```

**O que isso tudo significa?**

- **Load Queue (32 entradas)**: Armazena até 32 loads em execução
- **Store Queue (32 entradas)**: Armazena até 32 stores em execução
- **Dependency Check**: Verifica se um `load` depende de um `store` anterior
  - Problema: Se não verifica, pode ler dados errados
  - Se verifica sempre, é lento

**Por que é importante para matrix multiplication?**

```c
C[i][j] = A[i][k] * B[k][j] + C[i][j];
          ^^^^^^ Load   ^^^^^^ Load   ^^^^^^ Load
                                     ^^^^^^ Store
```

Se o `load` de `C[i][j]` for anterior ao `store` (fora de ordem), precisa da fila de memória!

---

### **4️⃣ REGISTRADORES FÍSICOS**

```python
numPhysIntRegs = Param.Unsigned(256, "Number of physical integer registers")
numPhysFloatRegs = Param.Unsigned(256, "Number of physical floating point registers")
numPhysCCRegs = Param.Unsigned(..., "Number of physical cc registers")
```

**Por que 256 se a arquitetura ARM tem só 16?**

A técnica de **renaming** precisa de **registradores físicos adicionais** para manter múltiplas versões de valores. 

Exemplo:
```
Original:
  r0 = 1
  r0 = r0 + 2  (depende de r0 anterior)
  r0 = r0 * 3  (depende de r0 anterior)

Com Renaming (256 registradores físicos):
  p0 = 1
  p1 = p0 + 2
  p2 = p1 * 3

Agora todas podem executar em paralelo (se não há dependência no nível de p0, p1, p2)!
```

---

### **5️⃣ REORDER BUFFER (ROB)**

```python
numRobs = Param.Unsigned(1, "Number of Reorder Buffers")
numROBEntries = Param.Unsigned(192, "Number of reorder buffer entries")
```

- **ROB = Reorder Buffer**: Estrutura que mantém o controle da ordem das instruções
- Permite executar fora de ordem, mas **commit na ordem correta**
- 192 entradas = pode ter até 192 instruções "em voo"

**Impacto no TP5**: Com mais instruções em voo, pode explorar mais paralelismo, mas usa mais energia e área!

---

### **6️⃣ INSTRUCTION QUEUE (IQ)**

```python
numIQEntries = Param.Unsigned(64, "Number of instruction queue entries")
```

- Buffer onde instruções aguardam seus operandos ficarem prontos
- 64 = bastante generoso

---

### **7️⃣ SMT (Simultaneous Multi-Threading)**

```python
smtNumFetchingThreads = Param.Unsigned(1, "SMT Number of Fetching Threads")
smtFetchPolicy = Param.String('SingleThread', "SMT Fetch policy")
smtLSQPolicy = Param.String('Partitioned', "SMT LSQ Sharing Policy")
smtROBPolicy = Param.String('Partitioned', "SMT ROB Sharing Policy")
```

- `smtNumFetchingThreads = 1`: **Não é SMT**, apenas 1 thread por core
- Se fosse `4`, permitiria 4 threads simultâneas no mesmo core

---

### **8️⃣ BRANCH PREDICTOR**

```python
branchPreddictor = Param.BranchPredictor(TournamentBP(...), "Branch Predictor")
```

- Usa **Tournament Branch Predictor**: combina múltiplos preditores
- Crítico para manter o pipeline cheio

**No TP5**: Matrix multiplication tem loops, então branch prediction é importante

---

### **9️⃣ FUNCTIONAL UNIT POOL**

```python
fuPool = Param.FUPool(DefaultFUPool(), "Functional Unit pool")
```

Define quantas unidades de execução existem:
- Quantas ALUs (Arithmetic Logic Units)?
- Quantas unidades de multiplicação?
- Quantas de memória?

Padrão = bastante generoso

---

### **🔟 MEMORY MODEL**

```python
needsTSO = Param.Bool(buildEnv['TARGET_ISA'] == 'x86',
                      "Enable TSO Memory model")
```

- Para ARM: `needsTSO = False` (ARM usa relaxed memory model)
- Para x86: `needsTSO = True` (x86 é mais restritivo)

---

## **COMPARAÇÃO COM MinorCPU**

Para entender por que `DerivO3CPU` é mais complexo, aqui está a diferença:

| Aspecto | MinorCPU (In-Order) | DerivO3CPU (Out-of-Order) |
|---------|---|---|
| **Fetch Width** | Menor | 8 |
| **Decode Width** | Menor | 8 |
| **Issue Width** | Menor | 8 |
| **Registradores Físicos** | ~100 | 256 |
| **ROB Entries** | ~50 | 192 |
| **Execução** | Ordem | Fora de ordem |
| **Latência** | Mais simples | Mais complexa |
| **Energia** | Menor | Maior |
| **Área** | Menor | ~4× maior |

---

## **COMO ESTES PARÂMETROS AFETAM SEU TP5?**

### **Nos Experimentos:**

1. **Single-Core (1 core)**:
   - `DerivO3CPU` terá IPC melhor porque explora paralelismo
   - Consegue esconder latências de memória

2. **Multi-Core (4, 8 cores)**:
   - Parâmetros como `cachePorts=200` permitem muitos acessos à cache
   - Mas contention no barramento compartilhado ainda afeta
   - **Renaming ajuda menos** com múltiplos cores (dependências entre cores)

3. **Nas Estatísticas**:
   ```bash
   grep "system.cpu.ipc" stats.txt
   ```
   - O3: pode ter IPC > 1 mesmo em single-core
   - Minor: típicamente IPC < 1

---

## **RESUMO PRÁTICO PARA O TP5**

| Pergunta | Resposta |
|----------|----------|
| O que é `O3CPU.py`? | Definição dos parâmetros da CPU Out-of-Order |
| Como é usado? | GEM5 lê este arquivo ao instanciar `DerivO3CPU` |
| Por que 8 instruções por ciclo? | Permite execução de múltiplas instruções em paralelo |
| Por que 256 registradores? | Para renaming e explorar paralelismo |
| Por que ROB de 192 entradas? | Permite muitas instruções "em voo" |
| Qual é o impacto em multicore? | Reduz eficiência de área mas pode ter melhor IPC |

---

## **PERGUNTA DE BÔNUS PARA SEU TP5**

Quando você rodar:

```bash
grep "system.cpu0.ipc\|system.cpu1.ipc" stats_o3_4core.txt
```

Você pode notar que:
- **CPU0 tem IPC maior** que **CPU1, CPU2, CPU3**
- Por quê? Porque CPU0 consegue explorar paralelismo do renaming mais rapidamente, enquanto as outras competem por cache/barramento

**Isso é um ponto excelente para sua análise!**
