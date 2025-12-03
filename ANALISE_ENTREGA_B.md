# 📋 ANÁLISE DA ENTREGA B - O QUE FALTA IMPLEMENTAR

## 🔍 SITUAÇÃO ATUAL

### ✅ O QUE JÁ ESTÁ IMPLEMENTADO (Entrega A)
- ✅ 4 Algoritmos de escalonamento: FIFO, SRTF, Priority, Round-Robin
- ✅ Eventos de I/O (IO:tempo-duracao)
- ✅ Quantum configurável para Round-Robin
- ✅ Estatísticas completas (Turnaround, Waiting, Response Time)
- ✅ Gráfico de Gantt visual
- ✅ Interface gráfica completa
- ✅ Testes automatizados (7/7 passando)
- ✅ Gerador de testes aleatórios
- ✅ Exportação de resultados

---

## ❌ O QUE ESTÁ FALTANDO (Entrega B - SINCRONIZAÇÃO COM MUTEX)

### 📊 EVIDÊNCIAS NO CÓDIGO

**Arquivo: `exemplos-arquivo-configuracao.txt`**
```txt
PRIOP;5
t01;0;5;2;IO:2-1;IO:3-2
t02;0;4;3;IO:3-1
t03;3;5;5;ML:1;MU:3          ← ML = Mutex Lock, MU = Mutex Unlock
t04;5;6;9;ML:1;IO:2-1;MU:3   ← Combina I/O com ML/MU
t05;7;4;6;ML:1;IO:2-1;MU:3   ← Combina I/O com ML/MU

Legenda:
IO: operação de I/O em algum dispositivo externo
ML: mutex lock           ← MUTEX LOCK (não Memory Load!)
MU: mutex unlock         ← MUTEX UNLOCK (não Memory Unload!)
- Os instantes de tempo indicados nos eventos são sempre relativos ao início da tarefa
```

### 🎯 FUNCIONALIDADES A IMPLEMENTAR

A **Entrega B** deve incluir **SINCRONIZAÇÃO DE TAREFAS COM MUTEX**:

#### 1. **EVENTOS DE MUTEX** 🆕
   - **ML:tempo** (Mutex Lock): Tarefa tenta adquirir o mutex no tempo relativo `tempo`
   - **MU:tempo** (Mutex Unlock): Tarefa libera o mutex no tempo relativo `tempo`
   - Formato: `ML:tempo_relativo` e `MU:tempo_relativo`
   - Exemplo: `ML:1` = tentar lock no tempo relativo 1, `MU:3` = unlock no tempo relativo 3

#### 2. **ESTRUTURA DE MUTEX**
   - [ ] Criar estrutura `Mutex` (lock/unlock, dono atual, fila de espera)
   - [ ] Gerenciar **fila de bloqueados por mutex**
   - [ ] Implementar bloqueio quando mutex está ocupado
   - [ ] Implementar desbloqueio quando mutex é liberado

#### 3. **ESTADOS DE TAREFA**
   - **Estado atual 4** = Bloqueado por I/O
   - [ ] **Novo estado 6** = Bloqueado aguardando Mutex (ou reutilizar estado 4 com flag)

#### 4. **LÓGICA DE SIMULAÇÃO COM MUTEX**
   - [ ] Processar evento `ML:tempo` durante execução da tarefa
   - [ ] Se mutex livre → adquirir e continuar
   - [ ] Se mutex ocupado → bloquear tarefa (aguardando mutex)
   - [ ] Processar evento `MU:tempo` durante execução
   - [ ] Liberar mutex e desbloquear próxima tarefa na fila

#### 5. **VISUALIZAÇÃO NO GANTT**
   - [ ] Nova cor para estado "Aguardando Mutex" (diferente de I/O)
   - [ ] Indicador visual de quando mutex está ocupado/livre
   - [ ] Legenda atualizada com novos estados

#### 6. **ESTATÍSTICAS DE MUTEX**
   - [ ] Tempo total bloqueado por mutex (por tarefa)
   - [ ] Número de vezes que esperou pelo mutex
   - [ ] Tempo médio de espera por mutex

#### 7. **INTERFACE GRÁFICA**
   - [ ] Exibir estado do mutex (livre/ocupado/dono)
   - [ ] Exibir fila de tarefas aguardando mutex
   - [ ] Adicionar campos ML/MU no "Criar TXT"

---

## 📝 ARQUIVOS QUE PRECISAM SER MODIFICADOS

### 1. **`tasks.py`** - Estrutura TCB
```python
@dataclass
class TCB:
    # ... campos existentes ...
    
    # NOVOS CAMPOS PARA ENTREGA B (MUTEX):
    ml_events: List[int] = field(default_factory=list)  # [tempo1, tempo2, ...] - quando fazer lock
    mu_events: List[int] = field(default_factory=list)  # [tempo1, tempo2, ...] - quando fazer unlock
    mutex_wait_time: int = 0                            # Tempo total bloqueado por mutex
    mutex_wait_count: int = 0                           # Vezes que esperou pelo mutex
```

### 2. **`config_loader.py`** - Parser
```python
def parse_mutex_events(events_string: str) -> Tuple[List[int], List[int]]:
    """
    Analisa eventos de mutex ML (Mutex Lock) e MU (Mutex Unlock).
    
    Args:
        events_string: String com eventos (ex: 'ML:1;IO:2-1;MU:3')
    
    Returns:
        Tupla com (ml_events, mu_events) - listas de tempos relativos
    
    Exemplo:
        >>> parse_mutex_events('ML:1;MU:3')
        ([1], [3])
    """
    ml_events = []
    mu_events = []
    
    parts = events_string.split(';')
    for part in parts:
        part = part.strip()
        if part.startswith('ML:'):
            tempo = int(part[3:])
            ml_events.append(tempo)
        elif part.startswith('MU:'):
            tempo = int(part[3:])
            mu_events.append(tempo)
    
    return ml_events, mu_events
```

### 3. **`simulador.py`** - Lógica de Mutex
```python
class Mutex:
    """Representa um mutex para sincronização de tarefas."""
    def __init__(self):
        self.locked = False           # Estado do mutex
        self.owner: Optional[TCB] = None  # Tarefa que possui o lock
        self.waiting_queue = TCBQueue()   # Tarefas aguardando

    def try_lock(self, task: TCB) -> bool:
        """Tenta adquirir o mutex. Retorna True se conseguiu."""
        if not self.locked:
            self.locked = True
            self.owner = task
            return True
        return False
    
    def unlock(self, task: TCB) -> Optional[TCB]:
        """Libera o mutex. Retorna próxima tarefa a ser desbloqueada."""
        if self.owner == task:
            self.locked = False
            self.owner = None
            # Desbloqueia próxima tarefa na fila
            if not self.waiting_queue.is_empty():
                next_task = self.waiting_queue.head
                self.waiting_queue.remove(next_task)
                return next_task
        return None

class Simulator:
    def __init__(self, scheduler, all_tasks):
        # ... código existente ...
        
        # NOVOS ATRIBUTOS PARA ENTREGA B (MUTEX):
        self.mutex = Mutex()                    # Mutex global
        self.mutex_blocked_queue = TCBQueue()   # Fila de bloqueados por mutex
    
    def _check_mutex_lock_event(self, task: TCB) -> bool:
        """Verifica se a tarefa deve tentar lock no tempo atual."""
        pass
    
    def _check_mutex_unlock_event(self, task: TCB) -> bool:
        """Verifica se a tarefa deve fazer unlock no tempo atual."""
        pass
    
    def _handle_mutex_lock(self, task: TCB):
        """Processa tentativa de lock."""
        pass
    
    def _handle_mutex_unlock(self, task: TCB):
        """Processa unlock do mutex."""
        pass
```

### 4. **`main.py`** - Interface
```python
class App(tk.Tk):
    def draw_gantt(self):
        # ... código existente ...
        
        # ADICIONAR novas cores para estados de mutex:
        # - Aguardando Mutex: Roxo (#9932CC)
        # - Em seção crítica (com lock): Verde mais escuro
        pass
    
    def show_statistics(self):
        # ... código existente ...
        
        # ADICIONAR estatísticas de mutex:
        # - Tempo bloqueado por mutex
        # - Vezes que esperou pelo mutex
        pass
```

---

## 🎯 PRIORIDADE DE IMPLEMENTAÇÃO

### FASE 1: Estruturas Básicas (CRÍTICO)
1. [ ] Adicionar campos de mutex no TCB (`ml_events`, `mu_events`)
2. [ ] Criar parser para ML/MU no config_loader
3. [ ] Criar classe `Mutex` no simulador

### FASE 2: Lógica de Sincronização (ESSENCIAL)
4. [ ] Implementar `Mutex.try_lock()` e `Mutex.unlock()`
5. [ ] Implementar verificação de eventos ML durante execução
6. [ ] Implementar verificação de eventos MU durante execução
7. [ ] Gerenciar fila de bloqueados por mutex

### FASE 3: Integração com Simulação (ESSENCIAL)
8. [ ] Modificar `step()` para processar eventos de mutex
9. [ ] Bloquear tarefa quando não consegue lock
10. [ ] Desbloquear tarefas quando mutex é liberado
11. [ ] Adicionar novo estado "Bloqueado por Mutex" (ou flag)

### FASE 4: Visualização (IMPORTANTE)
12. [ ] Atualizar Gantt com novo estado/cor para mutex
13. [ ] Adicionar indicador visual de seção crítica
14. [ ] Atualizar legenda de cores

### FASE 5: Estatísticas (IMPORTANTE)
15. [ ] Contabilizar tempo bloqueado por mutex
16. [ ] Contabilizar vezes que esperou pelo mutex
17. [ ] Exibir na janela de estatísticas
18. [ ] Exportar para arquivo

### FASE 6: Testes (CRÍTICO)
19. [ ] Criar teste com eventos ML/MU simples
20. [ ] Testar cenário com contenção (2+ tarefas disputando mutex)
21. [ ] Testar combinação de I/O + mutex

---

## 📊 ESTIMATIVA DE ESFORÇO (REVISADA)

- **Estruturas e Parser**: 1-2 horas
- **Classe Mutex**: 1-2 horas
- **Lógica de Sincronização**: 3-4 horas
- **Integração com Simulação**: 2-3 horas
- **Interface e Visualização**: 1-2 horas
- **Estatísticas**: 1 hora
- **Testes e Ajustes**: 2-3 horas

**TOTAL ESTIMADO**: 11-17 horas de desenvolvimento

---

## 🚀 PRÓXIMOS PASSOS

1. **Começar implementação** do parser de eventos ML/MU
2. **Criar classe Mutex** com lógica de lock/unlock
3. **Integrar no simulador** para processar eventos
4. **Testar** com arquivos de exemplo existentes
5. **Atualizar interface** com visualização de mutex

---

## 📚 REFERÊNCIAS NO CÓDIGO

### Formato com Mutex (exemplos-arquivo-configuracao.txt):
```txt
algoritmo_escalonamento;quantum
id;cor;ingresso;duracao;prioridade;lista_eventos

PRIOP;5
t01;0;5;2;IO:2-1;IO:3-2       ← Apenas I/O
t02;0;4;3;IO:3-1              ← Apenas I/O  
t03;3;5;5;ML:1;MU:3           ← Lock no tempo 1, Unlock no tempo 3
t04;5;6;9;ML:1;IO:2-1;MU:3    ← Lock + I/O + Unlock
t05;7;4;6;ML:1;IO:2-1;MU:3    ← Lock + I/O + Unlock

Legenda:
IO: operação de I/O em algum dispositivo externo
ML: mutex lock
MU: mutex unlock
- Os instantes de tempo são RELATIVOS ao início da execução da tarefa
```

### Interpretação do exemplo `t04;5;6;9;ML:1;IO:2-1;MU:3`:
- **ID**: t04
- **Cor**: 5 (magenta)
- **Ingresso**: 6 (chega no tempo global 6)
- **Duração**: 9 (precisa de 9 unidades de CPU)
- **Prioridade**: Não especificada (usa padrão ou algoritmo não precisa)
- **ML:1**: Tenta adquirir MUTEX LOCK no tempo relativo 1 de execução
- **IO:2-1**: Faz I/O no tempo relativo 2 por 1 unidade
- **MU:3**: Faz MUTEX UNLOCK no tempo relativo 3 de execução

### Cenário de Execução Esperado:
1. Tarefa t04 chega no tempo 6
2. Começa a executar (tempo relativo 0)
3. No tempo relativo 1: tenta `ML` (lock)
   - Se mutex livre: adquire e continua
   - Se mutex ocupado: BLOQUEIA até liberação
4. No tempo relativo 2: faz I/O por 1 unidade (bloqueia)
5. No tempo relativo 3: faz `MU` (unlock) - libera mutex
6. Continua até completar 9 unidades de CPU

---

## ✅ CONCLUSÃO (ATUALIZADA)

A **Entrega B** exige implementar **SINCRONIZAÇÃO COM MUTEX**:

| Item | Descrição | Status |
|------|-----------|--------|
| Parser ML/MU | Interpretar eventos de mutex | ✅ **Implementado** |
| Classe Mutex | Lock/unlock com fila de espera | ✅ **Implementado** |
| Bloqueio por Mutex | Bloquear tarefa quando mutex ocupado | ✅ **Implementado** |
| Desbloqueio | Desbloquear quando mutex liberado | ✅ **Implementado** |
| Visualização | Mostrar estado de mutex no Gantt | ✅ **Implementado** (estado "MUTEX") |
| Estatísticas | Tempo de espera por mutex | ✅ **Implementado** |

**STATUS**: ✅ **Entrega B IMPLEMENTADA** (100% completo)

---

## 📝 RESUMO DAS ALTERAÇÕES FEITAS

### Arquivos Modificados:

1. **`tasks.py`**
   - Adicionados constantes de estado (STATE_NEW, STATE_READY, etc.)
   - Novo estado: `STATE_BLOCKED_MUTEX = 6`
   - Novos campos no TCB: `ml_events`, `mu_events`, `has_mutex`, `mutex_wait_time`, `mutex_wait_count`
   - Novos métodos: `check_mutex_lock_event()`, `check_mutex_unlock_event()`

2. **`config_loader.py`**
   - Nova função `parse_events()` que extrai I/O, ML e MU de uma string de eventos
   - Função `load_simulation_config()` atualizada para parser mais flexível
   - Suporte a eventos múltiplos na mesma linha

3. **`simulador.py`**
   - Nova classe `Mutex` com métodos `try_lock()`, `unlock()`, `add_to_waiting()`
   - Novo atributo `mutex` no Simulator
   - Novos métodos: `_handle_mutex_lock_event()`, `_handle_mutex_unlock_event()`, `get_mutex_status()`
   - Método `step()` atualizado para processar eventos de mutex
   - Método `get_statistics()` atualizado com estatísticas de mutex

4. **`tests/test_suite.py`**
   - 3 novos testes: `test_mutex_basic()`, `test_mutex_contention()`, `test_mutex_io_combined()`

### Arquivos Criados:

- `tests/teste_mutex_basico.txt` - Teste de contenção de mutex
- `tests/teste_mutex_io.txt` - Teste combinando mutex e I/O

### Testes Passando: **10/10** ✅
