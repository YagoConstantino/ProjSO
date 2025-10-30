# 📘 DOCUMENTAÇÃO TÉCNICA DO PROJETO
## Simulador de Escalonamento de Processos

**Curso:** Sistemas Operacionais  
**Data:** 30 de outubro de 2025  
**Versão:** 1.0

---

## 📋 ÍNDICE

1. [Visão Geral do Projeto](#1-visão-geral-do-projeto)
2. [Problema Proposto](#2-problema-proposto)
3. [Arquitetura do Sistema](#3-arquitetura-do-sistema)
4. [Detalhamento dos Arquivos](#4-detalhamento-dos-arquivos)
5. [Algoritmos de Escalonamento](#5-algoritmos-de-escalonamento)
6. [Fluxo de Execução](#6-fluxo-de-execução)
7. [Eventos de I/O](#7-eventos-de-io)
8. [Estatísticas e Métricas](#8-estatísticas-e-métricas)
9. [Como Executar](#9-como-executar)

---

## 1. VISÃO GERAL DO PROJETO

### 1.1 Objetivo

Desenvolver um **simulador educacional de escalonamento de processos** que demonstre como diferentes algoritmos de gerenciamento de CPU tomam decisões sobre qual processo executar em cada momento.

### 1.2 Contexto

Em um sistema operacional real, múltiplos processos competem pelo uso da CPU. O **escalonador** é o componente responsável por decidir:
- **Qual processo executar** em cada instante
- **Por quanto tempo** ele pode executar
- **Quando fazer trocas de contexto** (context switches)

Este simulador implementa 5 algoritmos clássicos de escalonamento, permitindo visualizar e comparar seu comportamento.

### 1.3 Principais Funcionalidades

✅ **5 Algoritmos de Escalonamento** (FIFO, SRTF, Prioridade, Round-Robin)  
✅ **Eventos de I/O** (bloqueio e desbloqueio de processos)  
✅ **Visualização Gráfica** (Gráfico de Gantt animado)  
✅ **Estatísticas Detalhadas** (turnaround, waiting, response time)  
✅ **Interface Gráfica Intuitiva** (Tkinter)  
✅ **Execução Passo-a-Passo** (para fins didáticos)

---

## 2. PROBLEMA PROPOSTO

### 2.1 Definição do Problema

**Entrada:**
- Lista de processos (tarefas) com propriedades:
  - Tempo de chegada
  - Duração de execução
  - Prioridade
  - Eventos de I/O
- Algoritmo de escalonamento a ser utilizado
- Quantum (para Round-Robin)

**Processamento:**
- Simular a execução dos processos seguindo as regras do algoritmo escolhido
- Gerenciar estados dos processos (novo, pronto, executando, bloqueado, terminado)
- Controlar eventos de I/O (bloqueios e desbloqueios)
- Registrar todas as transições de estado

**Saída:**
- Gráfico de Gantt mostrando a linha do tempo de execução
- Estatísticas de performance:
  - **Turnaround Time**: Tempo total desde chegada até conclusão
  - **Waiting Time**: Tempo que o processo ficou aguardando na fila
  - **Response Time**: Tempo desde chegada até primeira execução
  - **Número de Ativações**: Quantas vezes o processo foi escalonado

### 2.2 Desafios Principais

1. **Gerenciar múltiplas filas** (prontos, bloqueados)
2. **Implementar preempção** corretamente (interrupção de processos)
3. **Sincronizar eventos de I/O** com o tempo de simulação
4. **Calcular estatísticas** precisas
5. **Visualizar de forma clara** o comportamento dos algoritmos

---

## 3. ARQUITETURA DO SISTEMA

### 3.1 Diagrama de Componentes

```
┌─────────────────────────────────────────────────────┐
│                    main.py                          │
│              (Interface Gráfica)                    │
│  - Botões de controle                              │
│  - Canvas para Gantt                               │
│  - Exibição de estatísticas                        │
└───────────────┬─────────────────────────────────────┘
                │ usa
                ▼
┌─────────────────────────────────────────────────────┐
│              config_loader.py                       │
│          (Parser de Configuração)                   │
│  - Lê arquivos .txt                                │
│  - Parse de eventos I/O                            │
│  - Cria objetos TCB                                │
└───────────────┬─────────────────────────────────────┘
                │ cria
                ▼
┌─────────────────────────────────────────────────────┐
│                   tasks.py                          │
│           (Estruturas de Dados)                     │
│  - TCB (Task Control Block)                        │
│  - TCBQueue (Fila de processos)                    │
└───────────────┬─────────────────────────────────────┘
                │ usado por
                ▼
┌─────────────────────────────────────────────────────┐
│                simulador.py                         │
│            (Motor de Simulação)                     │
│  - Controle de tempo                               │
│  - Gerenciamento de filas                          │
│  - Eventos de I/O                                  │
│  - Coleta de estatísticas                          │
└───────────────┬─────────────────────────────────────┘
                │ usa
                ▼
┌─────────────────────────────────────────────────────┐
│               scheduler.py                          │
│        (Algoritmos de Escalonamento)               │
│  - FIFOScheduler                                   │
│  - SRTFScheduler                                   │
│  - PriorityScheduler                               │
│  - RoundRobinScheduler                             │
└─────────────────────────────────────────────────────┘
```

### 3.2 Padrões de Projeto Utilizados

1. **Strategy Pattern**: Diferentes algoritmos de escalonamento implementam a mesma interface
2. **Observer Pattern**: Interface gráfica observa mudanças no simulador
3. **Factory Pattern**: SCHEDULER_FACTORY cria instâncias de escalonadores
4. **State Pattern**: TCB gerencia estados dos processos

---

## 4. DETALHAMENTO DOS ARQUIVOS

### 4.1 `tasks.py` - Estruturas de Dados

**Propósito:** Define as estruturas fundamentais para representar processos.

#### 4.1.1 Classe `TCB` (Task Control Block)

```python
@dataclass
class TCB:
    id: str                    # Identificador único (ex: "t01")
    RGB: List[int]             # Cor para visualização [R, G, B]
    state: int                 # Estado atual (NOVO=1, PRONTO=2, etc.)
    prio_s: int               # Prioridade estática
    prio_d: int               # Prioridade dinâmica
    inicio: int               # Tempo de chegada
    duracao: int              # Duração total de CPU necessária
    tempo_restante: int       # Tempo de CPU ainda necessário
    io_events: List[Tuple]    # Eventos de I/O [(tempo, duração), ...]
    tempo_exec_acumulado: int # Tempo já executado
    ativacoes: int            # Número de vezes escalonado
```

**Funcionalidades:**
- `check_io_event()`: Verifica se deve disparar I/O no tempo atual
- `reset_quantum()`: Reseta contador de quantum (Round-Robin)

**Estados Possíveis:**
```
NOVO (1)      → Processo criado, não chegou ainda
PRONTO (2)    → Na fila de prontos, aguardando CPU
EXECUTANDO (3)→ Atualmente usando a CPU
BLOQUEADO (4) → Aguardando I/O completar
TERMINADO (5) → Execução concluída
```

#### 4.1.2 Classe `TCBQueue` (Fila de Processos)

Implementa uma **lista duplamente encadeada** para gerenciar processos.

**Operações:**
- `enqueue(task)`: Adiciona processo no final
- `dequeue()`: Remove e retorna primeiro processo
- `remove(task)`: Remove processo específico da fila
- `peek()`: Retorna primeiro processo sem remover
- `to_list()`: Converte para lista Python (para ordenação)

**Por que lista encadeada?**
- Inserção/remoção O(1) nas pontas
- Remoção de elemento do meio O(n) mas necessária
- Mantém ordem de inserção (importante para FIFO)

---

### 4.2 `scheduler.py` - Algoritmos de Escalonamento

**Propósito:** Implementa a lógica de decisão de cada algoritmo.

#### 4.2.1 Classe Base `Scheduler`

Define a interface que todos os algoritmos devem seguir:

```python
@abstractmethod
def select_next_task(self, ready_queue, current_task, time):
    """
    Decide qual processo executar no próximo ciclo.
    
    Retorna:
        - TCB: Processo a executar
        - None: CPU fica ociosa
    """
    pass
```

#### 4.2.2 `FIFOScheduler` (First In, First Out)

**Princípio:** Primeiro a chegar, primeiro a executar.

**Características:**
- ❌ Não-preemptivo (processo executa até terminar ou bloquear)
- ✅ Simples de implementar
- ⚠️ Pode causar "starvation" de processos curtos

**Implementação:**
```python
def select_next_task(self, ready_queue, current_task, time):
    # Se há processo executando, continua com ele
    if current_task and current_task.state == EXECUTANDO:
        return current_task
    
    # Senão, pega o primeiro da fila (ordem de chegada)
    return ready_queue.dequeue()
```

**Exemplo:**
```
Tempo 0: T1 chega (duração 5) → executa
Tempo 2: T2 chega (duração 2) → aguarda
Tempo 5: T1 termina → T2 executa
Tempo 7: T2 termina
```

#### 4.2.3 `SRTFScheduler` (Shortest Remaining Time First)

**Princípio:** Sempre executa o processo com MENOR tempo restante.

**Características:**
- ✅ Preemptivo (pode interromper processo em execução)
- ✅ Minimiza tempo médio de espera
- ⚠️ Pode causar starvation de processos longos

**Implementação:**
```python
def select_next_task(self, ready_queue, current_task, time):
    # Converte fila para lista para ordenar
    ready_list = ready_queue.to_list()
    
    # Adiciona processo atual se estiver executando
    if current_task and current_task.state == EXECUTANDO:
        ready_list.append(current_task)
    
    # Ordena por tempo restante (menor primeiro)
    ready_list.sort(key=lambda t: t.tempo_restante)
    
    # Retorna o de menor tempo restante
    return ready_list[0] if ready_list else None
```

**Exemplo com Preempção:**
```
Tempo 0: T1 chega (duração 5) → executa
Tempo 1: T1 executando (restante 4)
Tempo 2: T2 chega (duração 2) → PREEMPTA T1 (2 < 4)
Tempo 2: T2 executa
Tempo 4: T2 termina → T1 volta
Tempo 8: T1 termina
```

#### 4.2.4 `PriorityScheduler` (Escalonamento por Prioridade)

**Princípio:** Sempre executa o processo de MAIOR prioridade.

**Variantes:**
- **PRIO**: Não-preemptivo (continua até terminar/bloquear)
- **PRIOP**: Preemptivo (interrompe se chegar prioridade maior)

**Implementação:**
```python
def select_next_task(self, ready_queue, current_task, time):
    ready_list = ready_queue.to_list()
    
    # Adiciona atual se for não-preemptivo
    if current_task and not self.preemptive:
        return current_task
    
    # Se preemptivo, inclui atual na comparação
    if current_task and self.preemptive:
        ready_list.append(current_task)
    
    # Ordena por prioridade (maior primeiro)
    ready_list.sort(key=lambda t: t.prio_d, reverse=True)
    
    return ready_list[0] if ready_list else None
```

**Exemplo PRIOP (Preemptivo):**
```
Tempo 0: T1 (prio 2) chega → executa
Tempo 2: T2 (prio 5) chega → PREEMPTA T1
Tempo 2: T2 executa
Tempo 6: T2 termina → T1 volta
```

#### 4.2.5 `RoundRobinScheduler` (Revezamento Circular)

**Princípio:** Cada processo executa por um QUANTUM de tempo, depois vai para o final da fila.

**Características:**
- ✅ Preemptivo por tempo
- ✅ Justo (todos têm chance)
- ⚠️ Quantum pequeno → muitas trocas de contexto
- ⚠️ Quantum grande → vira FIFO

**Implementação:**
```python
def select_next_task(self, ready_queue, current_task, time):
    # Se há processo executando
    if current_task and current_task.state == EXECUTANDO:
        # Verifica se quantum esgotou
        if self.time_slice_remaining > 0:
            self.time_slice_remaining -= 1
            return current_task  # Continua executando
        else:
            # Quantum esgotou → volta para fila
            ready_queue.enqueue(current_task)
            current_task = None
    
    # Pega próximo da fila e reseta quantum
    next_task = ready_queue.dequeue()
    if next_task:
        self.time_slice_remaining = self.quantum
    
    return next_task
```

**Exemplo (Quantum = 2):**
```
Fila: [T1, T2, T3]

Tempo 0-2: T1 executa (quantum esgota)
Fila: [T2, T3, T1]

Tempo 2-4: T2 executa (quantum esgota)
Fila: [T3, T1, T2]

Tempo 4-6: T3 executa (quantum esgota)
Fila: [T1, T2, T3]

... repete até todos terminarem
```

---

### 4.3 `simulador.py` - Motor de Simulação

**Propósito:** Gerencia o ciclo de vida dos processos e eventos.

#### 4.3.1 Estrutura da Classe `Simulator`

```python
class Simulator:
    def __init__(self, scheduler, all_tasks):
        self.scheduler = scheduler      # Algoritmo escolhido
        self.all_tasks = all_tasks      # Todos os processos
        self.ready_queue = TCBQueue()   # Fila de prontos
        self.blocked_queue = []         # Lista de bloqueados
        self.current_task = None        # Processo executando
        self.time = 0                   # Relógio da simulação
        self.gantt_data = []           # Registro para Gantt
```

#### 4.3.2 Método `step()` - Um Ciclo de Relógio

Este é o **coração do simulador**. Executado a cada unidade de tempo.

```python
def step(self):
    # 1. Verifica chegadas (NEW → READY)
    self._check_arrivals()
    
    # 2. Desbloqueia processos (I/O completou)
    self._check_io_unblock()
    
    # 3. Escalonador decide próximo processo
    next_task = self.scheduler.select_next_task(
        self.ready_queue, 
        self.current_task, 
        self.time
    )
    
    # 4. Gerencia troca de contexto
    if next_task != self.current_task:
        self._context_switch(next_task)
    
    # 5. Executa processo atual
    if self.current_task:
        self._execute_current_task()
    
    # 6. Registra estado no Gantt
    self._record_gantt()
    
    # 7. Incrementa relógio
    self.time += 1
```

#### 4.3.3 Gerenciamento de I/O

**Disparo de I/O:**
```python
def _execute_current_task(self):
    task = self.current_task
    
    # Processo executa 1 unidade de tempo
    task.tempo_exec_acumulado += 1
    task.tempo_restante -= 1
    
    # Verifica se deve disparar I/O
    io_duration = task.check_io_event()
    
    if io_duration:
        # Bloqueia processo
        task.state = BLOQUEADO
        task.io_blocked_until = self.time + io_duration
        self.blocked_queue.append(task)
        self.current_task = None
```

**Desbloqueio:**
```python
def _check_io_unblock(self):
    still_blocked = []
    
    for task in self.blocked_queue:
        # Verifica se I/O terminou
        if self.time >= task.io_blocked_until:
            # Desbloqueia
            task.state = PRONTO
            self.ready_queue.enqueue(task)
        else:
            still_blocked.append(task)
    
    self.blocked_queue = still_blocked
```

---

### 4.4 `config_loader.py` - Parser de Configuração

**Propósito:** Converte arquivos `.txt` em objetos Python.

#### 4.4.1 Formato do Arquivo

```
ALGORITMO;QUANTUM
#comentário
id;cor;chegada;duração;prioridade;IO:tempo-duração
```

**Exemplo:**
```
RR;3
#id;cor;ingresso;duracao;prioridade;io
t01;0;0;8;2;IO:3-2
t02;1;2;5;3
```

#### 4.4.2 Função `load_simulation_config()`

```python
def load_simulation_config(filepath):
    # 1. Lê primeira linha (algoritmo;quantum)
    algo_name, quantum = parse_header(first_line)
    
    # 2. Para cada linha de tarefa
    for line in file:
        # Parse: id;cor;chegada;duração;prioridade;[io]
        parts = line.split(';')
        
        # 3. Parse eventos I/O (se houver)
        io_events = parse_io_events(parts[-1])
        
        # 4. Cria TCB
        task = TCB(
            id=parts[0],
            RGB=COLOR_MAP[parts[1]],
            inicio=int(parts[2]),
            duracao=int(parts[3]),
            prio_s=int(parts[4]),
            io_events=io_events
        )
        
        tasks.append(task)
    
    return algo_name, quantum, tasks
```

#### 4.4.3 Parse de I/O

```python
def parse_io_events(io_string):
    # Formato: "IO:3-2;IO:5-1"
    events = []
    
    for event in io_string.split(';'):
        if event.startswith('IO:'):
            # Remove "IO:" e split por "-"
            time, duration = event[3:].split('-')
            events.append((int(time), int(duration)))
    
    return events
```

---

### 4.5 `main.py` - Interface Gráfica

**Propósito:** Conectar usuário com simulador através de GUI.

#### 4.5.1 Componentes da Interface

```
┌─────────────────────────────────────────────────┐
│  [Carregar] [Step] [Run] [Criar] [Aleatório]  │ ← Controles
├─────────────────────────────────────────────────┤
│  Tempo: 5  | Executando: T2 | Prontos: [T1]   │ ← Status
├─────────────────────────────────────────────────┤
│  Tarefas Carregadas:                           │
│  ID    Cor     Chegada  Duração  Prioridade    │ ← Tabela
│  t01   ff0000  0        8        2             │
├─────────────────────────────────────────────────┤
│  ┌─ Gráfico de Gantt ───────────────────────┐  │
│  │ T1 [██][  ][██][██][██]                  │  │ ← Gantt
│  │ T2 [  ][██][██]                          │  │
│  └───────────────────────────────────────────┘  │
└─────────────────────────────────────────────────┘
```

#### 4.5.2 Fluxo de Interação

```python
# 1. Usuário clica "Carregar Configuração"
def load_file(self):
    filepath = filedialog.askopenfilename()
    algo_name, quantum, tasks = load_simulation_config(filepath)
    
    # Cria escalonador apropriado
    scheduler = SCHEDULER_FACTORY[algo_name](quantum)
    
    # Cria simulador
    self.simulator = Simulator(scheduler, tasks)
    
    # Atualiza interface
    self.update_ui()

# 2. Usuário clica "Próximo Passo"
def do_step(self):
    self.simulator.step()     # Executa 1 ciclo
    self.update_ui()          # Atualiza tela
    self.draw_gantt()         # Redesenha Gantt

# 3. Usuário clica "Executar Tudo"
def run_all(self):
    self.simulator.run_full()  # Executa até o fim
    self.show_statistics()     # Mostra estatísticas
```

---

## 5. ALGORITMOS DE ESCALONAMENTO

### 5.1 Tabela Comparativa

| Algoritmo | Preemptivo? | Critério de Seleção | Vantagens | Desvantagens |
|-----------|-------------|---------------------|-----------|--------------|
| **FIFO** | ❌ Não | Ordem de chegada | Simples, justo temporalmente | Convoy effect, alto waiting time |
| **SRTF** | ✅ Sim | Menor tempo restante | Minimiza waiting time | Starvation de processos longos |
| **Prioridade** | ⚠️ Ambos | Maior prioridade | Flexível, controle fino | Starvation de baixa prioridade |
| **Round-Robin** | ✅ Sim (por tempo) | Circular com quantum | Justo, boa resposta | Overhead de context switch |

### 5.2 Quando Usar Cada Algoritmo

**FIFO:**
- ✅ Processos batch (não-interativos)
- ✅ Cargas previsíveis
- ❌ Sistemas interativos

**SRTF:**
- ✅ Minimizar tempo médio de espera
- ✅ Muitos processos curtos
- ❌ Sistemas com processos muito longos

**Prioridade:**
- ✅ Processos de tempo real
- ✅ Diferenciação de serviços
- ⚠️ Requer prevenção de starvation

**Round-Robin:**
- ✅ Sistemas de time-sharing
- ✅ Ambientes interativos
- ✅ Distribuição justa de CPU

---

## 6. FLUXO DE EXECUÇÃO

### 6.1 Diagrama de Estados de um Processo

```
    ┌──────┐
    │ NOVO │ (processo criado, não chegou)
    └───┬──┘
        │ tempo = inicio
        ▼
    ┌────────┐
    │ PRONTO │◄────┐ (na fila, aguardando CPU)
    └───┬────┘     │
        │          │ I/O completa
        │ escalonador escolhe
        ▼          │
┌──────────────┐   │
│  EXECUTANDO  │   │ (usando CPU)
└───┬────┬─────┘   │
    │    │         │
    │    │ I/O     │
    │    └────►┌──────────┐
    │          │BLOQUEADO │ (aguardando I/O)
    │          └────┬─────┘
    │               │
    │ termina       │
    ▼               ▼
┌───────────┐
│ TERMINADO │ (execução completa)
└───────────┘
```

### 6.2 Exemplo de Execução Completa

**Arquivo:** `teste_exemplo.txt`
```
SRTF;0
t01;0;0;5;2
t02;1;2;3;3
```

**Simulação Passo-a-Passo:**

```
Tempo 0:
  - T1 chega (duração 5)
  - ready_queue = [T1]
  - Escalonador escolhe T1
  - T1 → EXECUTANDO
  
Tempo 1:
  - T1 executa (restante = 4)
  - ready_queue = []
  - T1 continua
  
Tempo 2:
  - T2 chega (duração 3)
  - ready_queue = [T2]
  - SRTF compara: T1(restante=4) vs T2(restante=3)
  - PREEMPÇÃO! T2 < T1
  - T1 → PRONTO
  - T2 → EXECUTANDO
  
Tempo 3:
  - T2 executa (restante = 2)
  - ready_queue = [T1]
  - T2 continua (menor tempo restante)
  
Tempo 4:
  - T2 executa (restante = 1)
  - T2 continua
  
Tempo 5:
  - T2 termina
  - ready_queue = [T1]
  - T1 → EXECUTANDO
  
Tempo 6-9:
  - T1 executa até terminar

Resultado:
  T1: chegada=0, terminou=9, turnaround=9, ativações=2
  T2: chegada=2, terminou=5, turnaround=3, ativações=1
```

---

## 7. EVENTOS DE I/O

### 7.1 O que são Eventos de I/O?

Operações de **Entrada/Saída** representam momentos onde o processo:
- **Para de usar a CPU** (não pode executar)
- **Aguarda um dispositivo externo** (disco, rede, etc.)
- **É bloqueado** temporariamente
- **Volta à fila de prontos** quando o I/O termina

### 7.2 Formato e Sintaxe

```
IO:tempo_inicio-duracao
```

**Múltiplos I/Os:**
```
IO:3-2;IO:7-1
```

### 7.3 Exemplo Detalhado

**Configuração:**
```
t01;0;0;10;2;IO:4-3
```

**Significado:**
- Tarefa T1
- Chegada no tempo 0
- Duração total: 10 unidades de CPU
- Após executar 4 unidades, bloqueia por 3 unidades

**Timeline:**
```
Tempo 0-4:   T1 executa (acumulado = 4)
Tempo 4:     T1 dispara I/O
Tempo 4-7:   T1 BLOQUEADA (CPU livre para outros)
Tempo 7:     T1 volta à fila de prontos
Tempo 7-13:  T1 executa restante (6 unidades)
```

### 7.4 Implementação Técnica

**Disparo:**
```python
# Em simulador.py::_execute_current_task()
if task.tempo_exec_acumulado == 4:  # Chegou no tempo do I/O
    task.state = BLOQUEADO
    task.io_blocked_until = current_time + 3  # Bloqueia por 3
    blocked_queue.append(task)
```

**Desbloqueio:**
```python
# Em simulador.py::_check_io_unblock()
for task in blocked_queue:
    if current_time >= task.io_blocked_until:
        task.state = PRONTO
        ready_queue.enqueue(task)
```

---

## 8. ESTATÍSTICAS E MÉTRICAS

### 8.1 Métricas Calculadas

#### 8.1.1 Turnaround Time (Tempo de Retorno)

```
Turnaround = Tempo de Conclusão - Tempo de Chegada
```

**Exemplo:**
- T1 chega em t=0, termina em t=10
- Turnaround = 10 - 0 = 10

**Significado:** Tempo total que o processo ficou no sistema.

#### 8.1.2 Waiting Time (Tempo de Espera)

```
Waiting = Turnaround - Duração de Execução
```

**Exemplo:**
- T1 turnaround=10, duração=6
- Waiting = 10 - 6 = 4

**Significado:** Tempo que o processo ficou **aguardando** na fila.

#### 8.1.3 Response Time (Tempo de Resposta)

```
Response = Tempo da Primeira Execução - Tempo de Chegada
```

**Exemplo:**
- T1 chega em t=0, primeira execução em t=3
- Response = 3 - 0 = 3

**Significado:** Quanto tempo até o processo **começar** a executar.

#### 8.1.4 Número de Ativações

Conta quantas vezes o processo foi **escalonado** (colocado em EXECUTANDO).

**Exemplo:**
```
T1: Executa t=0-3, depois t=8-10
Ativações = 2 (duas vezes escolhido pelo escalonador)
```

### 8.2 Implementação

```python
# Em simulador.py::get_statistics()
def get_statistics(self):
    stats = {'tasks': []}
    
    for task in self.all_tasks:
        # Calcula métricas
        turnaround = task.fimExec - task.inicio
        waiting = turnaround - task.duracao
        response = task.first_exec_time - task.inicio
        
        stats['tasks'].append({
            'id': task.id,
            'arrival': task.inicio,
            'completion': task.fimExec,
            'turnaround_time': turnaround,
            'waiting_time': waiting,
            'response_time': response,
            'activations': task.ativacoes
        })
    
    # Calcula médias
    stats['avg_turnaround'] = mean([t['turnaround_time'] for t in stats['tasks']])
    stats['avg_waiting'] = mean([t['waiting_time'] for t in stats['tasks']])
    stats['avg_response'] = mean([t['response_time'] for t in stats['tasks']])
    
    return stats
```

---

## 9. COMO EXECUTAR

### 9.1 Requisitos

- Python 3.8 ou superior
- Tkinter (incluído no Python padrão)
- GNU Make (opcional, para build)

### 9.2 Execução Direta

```bash
# Método mais simples
python main.py
```

### 9.3 Usando Makefile

```bash
# Gerar executável standalone
make

# Executar direto
make run

# Executar testes
make test

# Ver ajuda
make help
```

### 9.4 Testando o Sistema

```bash
# Rodar suite de testes
python tests/test_suite.py

# Deve mostrar: 7/7 testes passando
```

### 9.5 Criando Arquivos de Teste

**Na interface gráfica:**
1. Clicar em "Criar TXT"
2. Definir algoritmo e quantum
3. Adicionar tarefas
4. Salvar arquivo

**Ou criar manualmente:**
```
RR;3
#id;cor;ingresso;duracao;prioridade;io
t01;0;0;5;2
t02;1;2;3;3;IO:1-1
```

---

## 10. CONCLUSÃO

Este projeto implementa um **simulador educacional completo** de escalonamento de processos, demonstrando:

✅ **5 algoritmos clássicos** de escalonamento  
✅ **Gerenciamento de estados** de processos  
✅ **Eventos de I/O** realistas  
✅ **Visualização gráfica** (Gantt)  
✅ **Métricas de performance** detalhadas  
✅ **Interface intuitiva** para experimentação  

### Arquitetura Modular

Cada arquivo tem uma **responsabilidade clara**:
- `tasks.py`: Estruturas de dados
- `scheduler.py`: Lógica de decisão
- `simulador.py`: Motor de execução
- `config_loader.py`: Entrada de dados
- `main.py`: Interface com usuário

### Comunicação Entre Componentes

```
Usuario → main.py → config_loader.py → tasks.py
                ↓
           simulador.py ←→ scheduler.py
                ↓
           main.py (Gantt + Stats)
```

### Princípios de Implementação

1. **Separação de Responsabilidades**: Cada classe tem papel específico
2. **Abstração**: Interface comum para algoritmos (Strategy Pattern)
3. **Extensibilidade**: Fácil adicionar novos algoritmos
4. **Testabilidade**: Suite de testes automatizados
5. **Didático**: Código comentado e visualização clara

---

**Projeto desenvolvido para fins educacionais.**  
**Demonstra conceitos fundamentais de Sistemas Operacionais.**

---

*Fim da Documentação Técnica*
