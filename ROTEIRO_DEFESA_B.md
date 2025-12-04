# 📋 Roteiro da Defesa B - Simulador de Escalonamento

## Visão Geral

A Defesa B (Não Presencial) consiste em:
- **Parte A:** Executar os 5 casos de teste fornecidos
- **Parte B:** Responder 3 perguntas sobre a implementação

---

## 📁 Parte A - Casos de Teste

| Caso | Arquivo | Descrição |
|------|---------|-----------|
| 1 | `Casos de Teste/caso-teste-001.txt` | Teste básico |
| 2 | `Casos de Teste/caso-teste-002.txt` | Teste com I/O |
| 3 | `Casos de Teste/caso-teste-003.txt` | Teste com múltiplos mutexes (**deadlock intencional**) |
| 4 | `Casos de Teste/caso-teste-004.txt` | Teste adicional |
| 5 | `Casos de Teste/caso-teste-005.txt` | Teste adicional |

### Como executar:
1. Abrir o simulador: `python main.py`
2. Carregar arquivo de configuração
3. Executar passo a passo ou "Executar Tudo"
4. Observar o diagrama de Gantt e estatísticas

---

## 📝 Parte B - Respostas às Perguntas

---

## Pergunta 1: PRIOPEnv (Prioridade com Envelhecimento)

> "Explique como o algoritmo PRIOPEnv funciona e como o envelhecimento (aging) é aplicado para evitar starvation."

### RESPOSTA:

O PRIOPEnv é um escalonador **preemptivo por prioridade** com mecanismo de **envelhecimento (aging)**.

---

### 1. Seleção da Tarefa (Preempção por Prioridade)

📁 **Arquivo:** `scheduler.py` | **Linhas:** 178-199

```python
def select_next_task(self, ready_queue, current_task, current_time) -> Optional[TCB]:
    if ready_queue.is_empty():
        return None
    
    # Encontra a tarefa com maior prioridade dinâmica (prio_d)
    # Em caso de empate, usa a que chegou primeiro (menor inicio)
    best_task = None
    for task in ready_queue:
        if best_task is None:
            best_task = task
        elif task.prio_d > best_task.prio_d:
            best_task = task
        elif task.prio_d == best_task.prio_d and task.inicio < best_task.inicio:
            best_task = task
    
    # Preempção: se a melhor tarefa tem prioridade maior que a atual, troca
    if current_task and current_task in ready_queue and best_task:
        if best_task.prio_d > current_task.prio_d:
            return best_task
        # Mantém a tarefa atual se prioridades iguais
```

**Explicação:** 
- A tarefa com **maior `prio_d`** (prioridade dinâmica) sempre executa
- Se uma tarefa de maior prioridade ficar pronta, ela assume a CPU imediatamente (**preempção**)
- Em caso de empate, a tarefa que chegou primeiro tem preferência

---

### 2. Envelhecimento (Aging)

📁 **Arquivo:** `scheduler.py` | **Linhas:** 212-227

```python
def age_tasks(self, ready_queue, exclude_task=None):
    """
    Aplica envelhecimento a todas as tarefas na fila de prontos.
    Incrementa prio_d em +alpha para cada tarefa (exceto a excluída).
    """
    for task in ready_queue:
        if task != exclude_task:
            task.prio_d += self.alpha
```

**Explicação:**
- Cada tarefa na fila de prontos recebe `+alpha` na prioridade dinâmica
- A tarefa excluída (que acabou de chegar ou terminar) não recebe o incremento

---

### 3. Quando o Aging é Aplicado

#### Evento 1: Nova tarefa chega

📁 **Arquivo:** `simulador.py` | **Linhas:** 353-356

```python
# Aplica envelhecimento APENAS se houve novas chegadas
if new_arrivals and isinstance(self.scheduler, PRIOPEnvScheduler):
    for new_task in new_arrivals:
        # Envelhece todas as tarefas prontas EXCETO a que acabou de chegar
        self.scheduler.age_tasks(self.ready_queue, exclude_task=new_task)
```

#### Evento 2: Tarefa termina

📁 **Arquivo:** `simulador.py` | **Linhas:** 651-653

```python
# Aplica envelhecimento quando tarefa TERMINA (PRIOPEnv)
if isinstance(self.scheduler, PRIOPEnvScheduler):
    self.scheduler.age_tasks(self.ready_queue)
```

---

### 4. Como Evita Starvation

| Situação | Sem Aging | Com Aging (alpha=1) |
|----------|-----------|---------------------|
| Tarefa A: prio_s=10 | Sempre executa | Executa enquanto prio_d > outras |
| Tarefa B: prio_s=2 | **Nunca executa** (starvation) | Após 9 eventos: prio_d=11 > 10 |

**Resultado:** Tarefa B eventualmente será escalonada, evitando starvation.

---

## Pergunta 2: Mutex

> "Explique como o mutex é implementado no simulador e como ele gerencia a exclusão mútua entre tarefas."

### RESPOSTA:

O Mutex (Mutual Exclusion) garante que apenas **uma tarefa por vez** acesse uma região crítica.

---

### 1. Estrutura do Mutex

📁 **Arquivo:** `simulador.py` | **Linhas:** 11-24

```python
class Mutex:
    """
    Representa um mutex para sincronização de tarefas.
    O mutex permite que apenas uma tarefa por vez acesse uma seção crítica.
    Tarefas que tentam adquirir um mutex já bloqueado entram numa fila de espera.
    """
    
    def __init__(self, mutex_id: int = 0):
        """Inicializa o mutex como livre."""
        self.mutex_id = mutex_id              # ID do mutex
        self.locked = False                   # Estado: True = bloqueado, False = livre
        self.owner: Optional[TCB] = None      # Tarefa que possui o lock
        self.waiting_queue = TCBQueue()       # Fila de tarefas aguardando o mutex
```

**Atributos:**
- `locked`: Estado do mutex (livre/ocupado)
- `owner`: Tarefa que possui o lock atualmente
- `waiting_queue`: Fila FIFO de tarefas aguardando

---

### 2. Operação Lock (try_lock)

📁 **Arquivo:** `simulador.py` | **Linhas:** 26-41

```python
def try_lock(self, task: TCB) -> bool:
    """
    Tenta adquirir o mutex para uma tarefa.
    Returns: True se conseguiu, False se já está bloqueado
    """
    if not self.locked:
        self.locked = True
        self.owner = task
        task.held_mutexes.append(self.mutex_id)
        return True
    return False
```

**Uso no simulador:**

📁 **Arquivo:** `simulador.py` | **Linhas:** 413-429

```python
def _handle_mutex_lock_event(self, task: TCB) -> bool:
    mutex_id = task.check_mutex_lock_event()
    if mutex_id is not None:
        mutex = self._get_mutex(mutex_id)
        if mutex.try_lock(task):
            # Conseguiu o lock, continua executando
            return False
        else:
            # Mutex ocupado, bloqueia a tarefa
            task.state = STATE_BLOCKED_MUTEX
            self.ready_queue.remove(task)
            mutex.add_to_waiting(task)
            self.blocked_mutex_queue.push_back(task)
            return True
    return False
```

**Fluxo:**
1. Tarefa tenta `try_lock()`
2. Se mutex livre → adquire o lock, continua executando
3. Se mutex ocupado → tarefa vai para `BLOCKED_MUTEX` e entra na fila de espera

---

### 3. Operação Unlock

📁 **Arquivo:** `simulador.py` | **Linhas:** 43-66

```python
def unlock(self, task: TCB) -> Optional[TCB]:
    """
    Libera o mutex e retorna a próxima tarefa a ser desbloqueada.
    """
    if self.owner == task:
        if self.mutex_id in task.held_mutexes:
            task.held_mutexes.remove(self.mutex_id)
        
        # Verifica se há tarefas aguardando na fila
        if not self.waiting_queue.is_empty():
            # Passa o mutex para a próxima tarefa na fila
            next_task = self.waiting_queue.pop_front()
            self.owner = next_task
            next_task.held_mutexes.append(self.mutex_id)
            return next_task
        else:
            # Ninguém esperando, mutex fica livre
            self.locked = False
            self.owner = None
            return None
    return None
```

**Fluxo:**
1. Tarefa que possui o mutex chama `unlock()`
2. Se há tarefas na fila de espera → primeira tarefa recebe o lock
3. Se fila vazia → mutex fica livre

---

### 4. Detecção de Deadlock

📁 **Arquivo:** `simulador.py` | **Linhas:** 460-494

```python
def detect_deadlock(self) -> Optional[List[int]]:
    """
    Detecta se há deadlock entre tarefas bloqueadas por mutex.
    """
    # Se há tarefas prontas, em execução ou em I/O, não é deadlock
    if not self.ready_queue.is_empty():
        return None
    if self.current_task is not None:
        return None
    if not self.blocked_io_queue.is_empty():
        return None
    
    # Se não há tarefas bloqueadas por mutex, não é deadlock
    if self.blocked_mutex_queue.is_empty():
        return None
    
    # Verificar se ainda há tarefas para chegar
    for task in self.all_tasks:
        if task.state == STATE_NEW and task.inicio > self.time:
            return None
    
    # DEADLOCK: só restam tarefas bloqueadas por mutex
    deadlocked_ids = [task.id for task in self.blocked_mutex_queue]
    return deadlocked_ids if deadlocked_ids else None
```

**Condições para Deadlock:**
- Não há tarefas prontas
- Não há tarefa em execução
- Não há tarefas em I/O
- Não há tarefas para chegar
- Há tarefas bloqueadas por mutex

**Exemplo (caso-teste-003):**
- T2 possui Mutex1, aguarda Mutex2
- T4 possui Mutex2, aguarda Mutex1
- → **DEADLOCK** (ciclo de espera circular)

---

## Pergunta 3: Operações de I/O

> "Explique como as operações de I/O são tratadas no simulador e como elas afetam o escalonamento das tarefas."

### RESPOSTA:

As operações de I/O simulam espera por dispositivos externos (disco, rede, etc.), durante a qual a CPU fica livre.

---

### 1. Formato de Configuração

```
IO:tempo_relativo-duração
```

**Exemplo:** `IO:2-3` = "após 2 unidades de execução, bloqueia por 3 unidades de tempo"

---

### 2. Tratamento do Evento I/O

📁 **Arquivo:** `simulador.py` | **Linhas:** 374-401

```python
def _handle_io_event(self, task: TCB) -> bool:
    """
    Trata um evento de I/O da tarefa.
    O I/O é verificado com base no tempo_exec_acumulado atual.
    A tarefa executa no ciclo atual e entra em I/O a partir do PRÓXIMO ciclo.
    """
    io_event = task.check_io_event()
    if io_event:
        _, duracao = io_event
        # Bloqueia a tarefa por 'duracao' unidades de tempo
        # O I/O começa no PRÓXIMO ciclo (self.time + 1)
        task.io_blocked_until = self.time + 1 + duracao
        task.state = STATE_BLOCKED_IO
        self.ready_queue.remove(task)
        self.blocked_io_queue.push_back(task)
        
        # Registra o bloqueio no Gantt para os ciclos de I/O
        for t in range(duracao):
            self.gantt_data.append((self.time + 1 + t, task.id, task.RGB, "IO"))
        
        return True
    return False
```

**Fluxo:**
1. Quando `tempo_exec_acumulado` atinge o tempo do evento
2. Tarefa muda para estado `BLOCKED_IO`
3. É removida da fila de prontos
4. É calculado `io_blocked_until = tempo_atual + 1 + duração`

---

### 3. Verificação do Evento (no TCB)

📁 **Arquivo:** `tasks.py` | **Linhas:** 106-120

```python
def check_io_event(self) -> Optional[Tuple[int, int]]:
    """
    Verifica se há um evento de I/O que deve ser disparado agora.
    Remove o evento da lista após disparar para não repetir.
    """
    for i, (tempo_inicio, duracao) in enumerate(self.io_events):
        if tempo_inicio == self.tempo_exec_acumulado:
            # Remove o evento para não disparar novamente
            self.io_events.pop(i)
            return (tempo_inicio, duracao)
    return None
```

**Lógica:**
- Compara `tempo_exec_acumulado` com o tempo configurado do evento
- Remove o evento da lista após disparar (evita repetição)

---

### 4. Desbloqueio de I/O

📁 **Arquivo:** `simulador.py` | **Linhas:** 358-372

```python
def _check_io_unblock(self):
    """
    Verifica se há tarefas bloqueadas que completaram seu I/O.
    Move tarefas da fila de bloqueadas para a fila de prontos.
    """
    tasks_to_unblock = []
    for task in self.blocked_io_queue:
        if self.time >= task.io_blocked_until:
            tasks_to_unblock.append(task)
    
    for task in tasks_to_unblock:
        self.blocked_io_queue.remove(task)
        task.state = STATE_READY
        self.ready_queue.push_back(task)
```

**Fluxo:**
1. A cada tick, verifica se `tempo_atual >= io_blocked_until`
2. Se sim, tarefa volta para `READY`
3. Pode ser escalonada novamente

---

### 5. Efeito no Escalonamento

| Momento | Estado da Tarefa | CPU |
|---------|------------------|-----|
| Antes do I/O | RUNNING | Ocupada pela tarefa |
| Disparo do I/O | BLOCKED_IO | **Liberada** para outras tarefas |
| Durante I/O | BLOCKED_IO | Outras tarefas executam |
| Fim do I/O | READY | Tarefa pode ser escalonada |

**Benefício:** Permite **multiprogramação** - enquanto uma tarefa espera I/O, outras usam a CPU.

---

## 🎯 Dicas para Apresentação

### Para cada pergunta:

1. **Abrir o arquivo** no VS Code
2. **Ir para a linha** indicada (`Ctrl+G`)
3. **Mostrar o código** enquanto explica
4. **Executar um caso de teste** que demonstre o comportamento

### Casos de teste sugeridos por conceito:

| Conceito | Caso de Teste | O que observar |
|----------|---------------|----------------|
| PRIOPEnv + Aging | caso-teste-001 ou 002 | Coluna PrioD mudando na tabela |
| Mutex | caso-teste-003 | Tarefas bloqueadas, deadlock detectado |
| I/O | caso-teste-002 | Barras de I/O no Gantt (padrão listrado) |

### Atalhos úteis no VS Code:

- `Ctrl+G` - Ir para linha
- `Ctrl+F` - Buscar no arquivo
- `Ctrl+Shift+F` - Buscar em todos os arquivos

---

## ✅ Checklist Final

- [ ] Executar caso-teste-001.txt
- [ ] Executar caso-teste-002.txt
- [ ] Executar caso-teste-003.txt (mostrar detecção de deadlock)
- [ ] Executar caso-teste-004.txt
- [ ] Executar caso-teste-005.txt
- [ ] Responder Pergunta 1 (PRIOPEnv) com código
- [ ] Responder Pergunta 2 (Mutex) com código
- [ ] Responder Pergunta 3 (I/O) com código
- [ ] Exportar Gantt de cada caso (PNG ou SVG)
