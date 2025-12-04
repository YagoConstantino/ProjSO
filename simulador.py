"""
Módulo principal do simulador de escalonamento de processos.
Gerencia a execução das tarefas, eventos de I/O, sincronização com mutex e coleta de estatísticas.
"""

from tasks import TCB, TCBQueue, STATE_NEW, STATE_READY, STATE_RUNNING, STATE_BLOCKED_IO, STATE_TERMINATED, STATE_BLOCKED_MUTEX
from scheduler import Scheduler, RoundRobinScheduler, PRIOPEnvScheduler, PRIOPEnvTickScheduler
from typing import List, Optional


class Mutex:
    """
    Representa um mutex para sincronização de tarefas.
    
    O mutex permite que apenas uma tarefa por vez acesse uma seção crítica.
    Tarefas que tentam adquirir um mutex já bloqueado entram numa fila de espera.
    """
    
    def __init__(self, mutex_id: int = 0):
        """Inicializa o mutex como livre."""
        self.mutex_id = mutex_id              # ID do mutex
        self.locked = False                   # Estado do mutex: True = bloqueado, False = livre
        self.owner: Optional[TCB] = None      # Tarefa que possui o lock
        self.waiting_queue = TCBQueue()       # Fila de tarefas aguardando o mutex
    
    def try_lock(self, task: TCB) -> bool:
        """
        Tenta adquirir o mutex para uma tarefa.
        
        Args:
            task: Tarefa que está tentando adquirir o mutex
            
        Returns:
            True se conseguiu adquirir o mutex, False se já está bloqueado
        """
        if not self.locked:
            self.locked = True
            self.owner = task
            task.held_mutexes.append(self.mutex_id)
            return True
        return False
    
    def unlock(self, task: TCB) -> Optional[TCB]:
        """
        Libera o mutex e retorna a próxima tarefa a ser desbloqueada.
        
        Args:
            task: Tarefa que está liberando o mutex (deve ser o owner)
            
        Returns:
            Próxima tarefa na fila de espera que foi desbloqueada, ou None
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
    
    def add_to_waiting(self, task: TCB):
        """
        Adiciona uma tarefa à fila de espera do mutex.
        
        Args:
            task: Tarefa a ser adicionada à fila de espera
        """
        task.mutex_wait_count += 1
        self.waiting_queue.push_back(task)
    
    def is_free(self) -> bool:
        """Verifica se o mutex está livre."""
        return not self.locked
    
    def get_owner_id(self) -> Optional[int]:
        """Retorna o ID da tarefa que possui o mutex, ou None se livre."""
        return self.owner.id if self.owner else None


class Simulator:
    """
    Simulador de escalonamento de processos.
    
    Gerencia o ciclo de vida das tarefas, incluindo:
    - Chegada de novas tarefas
    - Escalonamento de CPU
    - Eventos de I/O
    - Sincronização com mutex (lock/unlock)
    - Coleta de estatísticas de execução
    - Histórico para voltar passos (step_back)
    """
    
    def __init__(self, scheduler: Scheduler, all_tasks: List[TCB]):
        """
        Inicializa o simulador.
        
        Args:
            scheduler: Algoritmo de escalonamento a ser utilizado
            all_tasks: Lista de todas as tarefas da simulação
        """
        self.scheduler = scheduler
        # Ordena tarefas por tempo de chegada para processamento correto
        self.all_tasks = sorted(all_tasks, key=lambda t: t.inicio)
        
        self.time = 0  # Relógio da simulação
        self.current_task: Optional[TCB] = None  # Tarefa em execução
        
        self.ready_queue = TCBQueue()       # Fila de tarefas prontas
        self.blocked_io_queue = TCBQueue()  # Fila de tarefas bloqueadas em I/O
        self.blocked_mutex_queue = TCBQueue()  # Fila de tarefas bloqueadas por mutex (global - para visualização)
        self.done_tasks = []  # Lista de tarefas concluídas
        
        # Múltiplos mutexes para sincronização (Entrega B)
        self.mutexes = {}  # Dicionário de mutexes: {mutex_id: Mutex}
        self._init_mutexes()
        
        self.gantt_data = []  # Dados para o gráfico de Gantt
        
        # Histórico para funcionalidade de voltar - OTIMIZADO
        self.history = []
        self.max_history = 100  # Limita para economizar memória
    
    def _init_mutexes(self):
        """Inicializa os mutexes necessários baseado nos eventos das tarefas."""
        mutex_ids = set()
        for task in self.all_tasks:
            for mutex_id, _ in task.ml_events:
                mutex_ids.add(mutex_id)
            for mutex_id, _ in task.mu_events:
                mutex_ids.add(mutex_id)
        
        for mutex_id in mutex_ids:
            self.mutexes[mutex_id] = Mutex(mutex_id)
        
        # Garante que pelo menos o mutex 0 exista (para compatibilidade)
        if 0 not in self.mutexes:
            self.mutexes[0] = Mutex(0)
    
    def _get_mutex(self, mutex_id: int) -> Mutex:
        """Obtém um mutex pelo ID, criando-o se não existir."""
        if mutex_id not in self.mutexes:
            self.mutexes[mutex_id] = Mutex(mutex_id)
        return self.mutexes[mutex_id]

    def _save_state(self):
        """
        Salva o estado atual da simulação no histórico.
        Salva apenas dados essenciais para economizar memória.
        """
        # Conta quantos registros de gantt existem ANTES deste passo
        gantt_count_before = len(self.gantt_data)
        
        state = {
            'time': self.time,
            'current_task_id': self.current_task.id if self.current_task else None,
            'gantt_count': gantt_count_before,  # Posição do gantt antes deste step
            'tasks_state': {},
            'ready_queue_ids': [t.id for t in self.ready_queue],
            'blocked_io_ids': [t.id for t in self.blocked_io_queue],
            'blocked_mutex_ids': [t.id for t in self.blocked_mutex_queue],
            'done_ids': [t.id for t in self.done_tasks],
            'scheduler_quantum': getattr(self.scheduler, 'time_slice_remaining', None),
            'mutexes': {
                mutex_id: {
                    'locked': mutex.locked,
                    'owner_id': mutex.get_owner_id(),
                    'waiting_ids': [t.id for t in mutex.waiting_queue]
                } for mutex_id, mutex in self.mutexes.items()
            }
        }
        
        # Salva estado de cada tarefa (apenas campos que mudam)
        for task in self.all_tasks:
            state['tasks_state'][task.id] = {
                'state': task.state,
                'tempo_restante': task.tempo_restante,
                'tempo_exec_acumulado': task.tempo_exec_acumulado,
                'io_blocked_until': task.io_blocked_until,
                'io_events': list(task.io_events) if task.io_events else [],
                'ml_events': list(task.ml_events) if task.ml_events else [],
                'mu_events': list(task.mu_events) if task.mu_events else [],
                'ativacoes': task.ativacoes,
                'inicioExec': task.inicioExec,
                'fimExec': task.fimExec,
                'somaExec': task.somaExec,
                'held_mutexes': list(task.held_mutexes) if task.held_mutexes else [],
                'mutex_wait_time': task.mutex_wait_time,
                'mutex_wait_count': task.mutex_wait_count,
                'fim': task.fim,
                'prio_d': task.prio_d
            }
        
        self.history.append(state)
        
        # Limita tamanho do histórico
        if len(self.history) > self.max_history:
            self.history.pop(0)

    def step_back(self) -> bool:
        """
        Volta um passo na simulação, restaurando o estado anterior.
        
        Returns:
            True se conseguiu voltar, False se não há histórico
        """
        if not self.history:
            return False
        
        # Pega o estado anterior
        state = self.history.pop()
        
        # Restaura tempo
        self.time = state['time']
        
        # Restaura quantum do scheduler
        if state['scheduler_quantum'] is not None and hasattr(self.scheduler, 'time_slice_remaining'):
            self.scheduler.time_slice_remaining = state['scheduler_quantum']
        
        # Restaura estado de cada tarefa
        for task in self.all_tasks:
            if task.id in state['tasks_state']:
                ts = state['tasks_state'][task.id]
                task.state = ts['state']
                task.tempo_restante = ts['tempo_restante']
                task.tempo_exec_acumulado = ts['tempo_exec_acumulado']
                task.io_blocked_until = ts['io_blocked_until']
                task.io_events = list(ts['io_events'])
                task.ml_events = list(ts['ml_events'])
                task.mu_events = list(ts['mu_events'])
                task.ativacoes = ts['ativacoes']
                task.inicioExec = ts['inicioExec']
                task.fimExec = ts['fimExec']
                task.somaExec = ts['somaExec']
                task.held_mutexes = list(ts['held_mutexes'])
                task.mutex_wait_time = ts['mutex_wait_time']
                task.mutex_wait_count = ts['mutex_wait_count']
                task.fim = ts['fim']
                task.prio_d = ts['prio_d']
        
        # Reconstrói filas baseado nos IDs salvos
        self._rebuild_queues(state)
        
        # Restaura current_task
        if state['current_task_id'] is not None:
            self.current_task = self._find_task_by_id(state['current_task_id'])
        else:
            self.current_task = None
        
        # Restaura mutexes
        self._restore_mutexes(state['mutexes'])
        
        # Remove registros do gantt adicionados neste passo
        gantt_count = state['gantt_count']
        self.gantt_data = self.gantt_data[:gantt_count]
        
        # Restaura done_tasks
        self.done_tasks = [self._find_task_by_id(tid) for tid in state['done_ids']]
        
        return True

    def _find_task_by_id(self, task_id) -> Optional[TCB]:
        """Busca tarefa pelo ID."""
        for task in self.all_tasks:
            if task.id == task_id:
                return task
        return None

    def _rebuild_queues(self, state: dict):
        """Reconstrói as filas de prontos e bloqueados."""
        # IMPORTANTE: Limpa ponteiros de TODAS as tarefas primeiro
        # para evitar referências cruzadas corrompidas
        for task in self.all_tasks:
            task.prev = None
            task.next = None
        
        # Limpa filas atuais
        self.ready_queue = TCBQueue()
        self.blocked_io_queue = TCBQueue()
        self.blocked_mutex_queue = TCBQueue()
        
        # Reconstrói ready_queue na ordem correta
        for tid in state['ready_queue_ids']:
            task = self._find_task_by_id(tid)
            if task:
                self.ready_queue.push_back(task)
        
        # Reconstrói blocked_io_queue
        for tid in state['blocked_io_ids']:
            task = self._find_task_by_id(tid)
            if task:
                self.blocked_io_queue.push_back(task)
        
        # Reconstrói blocked_mutex_queue
        for tid in state['blocked_mutex_ids']:
            task = self._find_task_by_id(tid)
            if task:
                self.blocked_mutex_queue.push_back(task)

    def _restore_mutexes(self, mutexes_state: dict):
        """Restaura o estado de todos os mutexes."""
        for mutex_id, mutex_state in mutexes_state.items():
            mutex = self._get_mutex(mutex_id)
            mutex.locked = mutex_state['locked']
            
            if mutex_state['owner_id'] is not None:
                mutex.owner = self._find_task_by_id(mutex_state['owner_id'])
            else:
                mutex.owner = None
            
            # Reconstrói fila de espera do mutex
            # Os ponteiros já foram limpos em _rebuild_queues
            mutex.waiting_queue = TCBQueue()
            for tid in mutex_state['waiting_ids']:
                task = self._find_task_by_id(tid)
                if task:
                    mutex.waiting_queue.push_back(task)

    def can_step_back(self) -> bool:
        """Verifica se é possível voltar um passo."""
        return len(self.history) > 0

    # Alias para compatibilidade com código existente
    @property
    def blocked_queue(self):
        """Alias para blocked_io_queue (compatibilidade)."""
        return self.blocked_io_queue

    def _check_for_new_arrivals(self):
        """
        Verifica se há novas tarefas chegando no tempo atual.
        Move tarefas de NEW (estado 1) para READY (estado 2).
        Aplica envelhecimento nas tarefas prontas quando nova tarefa chega (PRIOPEnv).
        """
        new_arrivals = []
        for task in self.all_tasks:
            if task.state == STATE_NEW and task.inicio == self.time:
                task.state = STATE_READY
                task.prio_d = task.prio_s  # Reseta prioridade dinâmica ao chegar
                self.ready_queue.push_back(task)
                new_arrivals.append(task)
        
        # Aplica envelhecimento APENAS se houve novas chegadas
        if new_arrivals and isinstance(self.scheduler, PRIOPEnvScheduler):
            for new_task in new_arrivals:
                # Envelhece todas as tarefas prontas EXCETO a que acabou de chegar
                self.scheduler.age_tasks(self.ready_queue, exclude_task=new_task)

    def _check_io_unblock(self):
        """
        Verifica se há tarefas bloqueadas que completaram seu I/O.
        Move tarefas da fila de bloqueadas para a fila de prontos.
        NÃO aplica envelhecimento aqui - apenas na chegada de novas tarefas e término.
        """
        tasks_to_unblock = []
        for task in self.blocked_io_queue:
            if self.time >= task.io_blocked_until:
                tasks_to_unblock.append(task)
        
        for task in tasks_to_unblock:
            self.blocked_io_queue.remove(task)
            task.state = STATE_READY
            self.ready_queue.push_back(task)

    def _handle_io_event(self, task: TCB) -> bool:
        """
        Trata um evento de I/O da tarefa.
        
        O I/O é verificado com base no tempo_exec_acumulado atual.
        A tarefa executa no ciclo atual e entra em I/O a partir do PRÓXIMO ciclo.
        
        Args:
            task: Tarefa que pode disparar evento de I/O
            
        Returns:
            True se a tarefa foi bloqueada por I/O, False caso contrário
        """
        io_event = task.check_io_event()
        if io_event:
            _, duracao = io_event
            # Bloqueia a tarefa por 'duracao' unidades de tempo
            # O I/O começa no PRÓXIMO ciclo (self.time + 1)
            # O desbloqueio acontece quando self.time >= io_blocked_until
            task.io_blocked_until = self.time + 1 + duracao
            task.state = STATE_BLOCKED_IO
            self.ready_queue.remove(task)
            self.blocked_io_queue.push_back(task)
            
            # Registra o bloqueio no Gantt para os ciclos de I/O (começando no próximo)
            for t in range(duracao):
                self.gantt_data.append((self.time + 1 + t, task.id, task.RGB, "IO"))
            
            return True
        return False
    
    def _handle_mutex_lock_event(self, task: TCB) -> bool:
        """
        Trata um evento de mutex lock da tarefa.
        
        Args:
            task: Tarefa que está tentando adquirir o mutex
            
        Returns:
            True se a tarefa foi bloqueada (mutex ocupado), False se adquiriu o lock
        """
        mutex_id = task.check_mutex_lock_event()
        if mutex_id is not None:
            mutex = self._get_mutex(mutex_id)
            if mutex.try_lock(task):
                # Conseguiu o lock, continua executando
                return False
            else:
                # Mutex ocupado, bloqueia a tarefa
                task.state = STATE_BLOCKED_MUTEX
                task.mutex_blocked_until = 0  # Indefinido, aguarda unlock de outra tarefa
                self.ready_queue.remove(task)
                mutex.add_to_waiting(task)
                self.blocked_mutex_queue.push_back(task)
                return True
        return False
    
    def _handle_mutex_unlock_event(self, task: TCB) -> Optional[TCB]:
        """
        Trata um evento de mutex unlock da tarefa.
        
        Args:
            task: Tarefa que está liberando o mutex
            
        Returns:
            Tarefa que foi desbloqueada (se houver), ou None
        """
        mutex_id = task.check_mutex_unlock_event()
        if mutex_id is not None:
            mutex = self._get_mutex(mutex_id)
            unblocked_task = mutex.unlock(task)
            if unblocked_task:
                # Remove da fila de bloqueados por mutex e volta para prontos
                self.blocked_mutex_queue.remove(unblocked_task)
                unblocked_task.state = STATE_READY
                self.ready_queue.push_back(unblocked_task)
                return unblocked_task
        return None

    def is_finished(self) -> bool:
        """
        Verifica se a simulação terminou.
        
        Returns:
            True se todas as tarefas foram concluídas
        """
        return len(self.done_tasks) == len(self.all_tasks)
    
    def detect_deadlock(self) -> Optional[List[int]]:
        """
        Detecta se há deadlock entre tarefas bloqueadas por mutex.
        
        Um deadlock ocorre quando:
        - Não há tarefas prontas ou em execução
        - Não há tarefas bloqueadas por I/O
        - Há tarefas bloqueadas por mutex aguardando umas às outras
        - Todas as tarefas pendentes estão em um ciclo de espera
        
        Returns:
            Lista de IDs das tarefas em deadlock, ou None se não há deadlock
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
                return None  # Ainda há tarefas que vão chegar
        
        # Se chegou aqui: não há tarefas prontas, em execução, em I/O,
        # não há tarefas para chegar, mas há tarefas bloqueadas por mutex
        # => DEADLOCK!
        
        deadlocked_ids = [task.id for task in self.blocked_mutex_queue]
        return deadlocked_ids if deadlocked_ids else None
    
    def is_deadlocked(self) -> bool:
        """
        Verifica se o sistema está em deadlock.
        
        Returns:
            True se há deadlock, False caso contrário
        """
        return self.detect_deadlock() is not None
    
    def get_deadlock_info(self) -> Optional[dict]:
        """
        Retorna informações detalhadas sobre o deadlock.
        
        Returns:
            Dicionário com informações do deadlock ou None se não há deadlock
        """
        deadlocked = self.detect_deadlock()
        if deadlocked is None:
            return None
        
        info = {
            'deadlocked_tasks': deadlocked,
            'mutex_status': {},
            'waiting_for': {}
        }
        
        # Para cada tarefa em deadlock, identificar qual mutex ela aguarda
        for task in self.blocked_mutex_queue:
            # Verificar em qual fila de espera de mutex a tarefa está
            for mutex_id, mutex in self.mutexes.items():
                for waiting_task in mutex.waiting_queue:
                    if waiting_task.id == task.id:
                        info['waiting_for'][task.id] = {
                            'mutex_id': mutex_id,
                            'owner_id': mutex.get_owner_id()
                        }
                        break
            
            # Registrar quais mutexes a tarefa possui
            if task.held_mutexes:
                info['mutex_status'][task.id] = list(task.held_mutexes)
        
        return info

    def step(self):
        """
        Executa um passo da simulação (1 unidade de tempo).
        
        Sequência de operações:
        1. Verifica chegada de novas tarefas
        2. Desbloqueia tarefas que completaram I/O
        3. Verifica preempção por quantum (Round-Robin)
        4. Seleciona próxima tarefa a executar
        5. Gerencia troca de contexto
        6. Executa a tarefa por 1 unidade de tempo
        7. Verifica eventos de Mutex (lock/unlock)
        8. Verifica eventos de I/O
        9. Atualiza estatísticas
        10. Incrementa o tempo
        """
        if self.is_finished():
            return

        self._save_state()

        # 1. Processa chegada de novas tarefas
        self._check_for_new_arrivals()
        # 2. Desbloqueia tarefas que completaram I/O
        self._check_io_unblock()
        
        # Verifica preempção por quantum esgotado (Round-Robin ou PRIOPEnv)
        if isinstance(self.scheduler, (RoundRobinScheduler, PRIOPEnvScheduler)):
            if self.current_task and self.scheduler.time_slice_remaining <= 0 and self.current_task.tempo_restante > 0:
                # Quantum esgotado: move tarefa atual para o fim da fila
                self.ready_queue.remove(self.current_task)
                self.ready_queue.push_back(self.current_task)
                # Força troca de contexto
                self.current_task.state = STATE_READY
                self.current_task.fimExec = self.time
                self.current_task.somaExec += (self.time - self.current_task.inicioExec)
                self.current_task = None
        
        # 4. Seleciona a próxima tarefa a executar
        next_task = self.scheduler.select_next_task(self.ready_queue, self.current_task, self.time)
        
        # 5. Gerencia troca de contexto
        if self.current_task != next_task:
            # Tarefa atual foi preemptada ou terminou
            if self.current_task:
                self.current_task.state = STATE_READY
                self.current_task.fimExec = self.time
                self.current_task.somaExec += (self.time - self.current_task.inicioExec)
            
            # Nova tarefa entra em execução
            self.current_task = next_task
            if self.current_task:
                self.current_task.state = STATE_RUNNING
                self.current_task.inicioExec = self.time
                self.current_task.ativacoes += 1
                
                # Reseta quantum para a nova tarefa
                if hasattr(self.scheduler, 'reset_quantum'):
                    self.scheduler.reset_quantum()
        
        # Registrar tarefas prontas (state = READY) - DEPOIS da troca de contexto
        # Isso garante que tarefas preemptadas também sejam registradas
        for task in self.all_tasks:
            if task.state == STATE_READY and task != self.current_task:
                self.gantt_data.append((self.time, task.id, task.RGB, "READY"))
        
        # 6. Executa a tarefa atual
        if self.current_task:
            # PRIMEIRO: Verifica eventos de Mutex Lock ANTES de executar
            # (eventos são baseados no tempo de execução acumulado ANTES da execução)
            if self._handle_mutex_lock_event(self.current_task):
                # Tarefa foi bloqueada aguardando mutex
                # Registra no Gantt como MUTEX (bloqueado)
                self.gantt_data.append((self.time, self.current_task.id, self.current_task.RGB, "MUTEX"))
                self.current_task = None
            else:
                # Executa por 1 unidade de tempo
                self.current_task.tempo_restante -= 1
                self.current_task.tempo_exec_acumulado += 1
                
                # NOVO: Reseta prioridade dinâmica após executar (PRIOPEnv)
                if isinstance(self.scheduler, PRIOPEnvScheduler):
                    self.current_task.prio_d = self.current_task.prio_s
                
                # Decrementa quantum (se aplicável)
                if hasattr(self.scheduler, 'decrement_quantum'):
                    self.scheduler.decrement_quantum()
                
                # Verifica eventos de I/O APÓS executar (baseado no tempo_exec_acumulado atual)
                if self._handle_io_event(self.current_task):
                    # Tarefa executou NESTE ciclo, mas entra em I/O APÓS
                    # Registra este ciclo como EXEC (pois ela executou antes de entrar em I/O)
                    self.gantt_data.append((self.time, self.current_task.id, self.current_task.RGB, "EXEC"))
                    self.current_task = None
                else:
                    # Registra no Gantt como execução normal
                    self.gantt_data.append((self.time, self.current_task.id, self.current_task.RGB, "EXEC"))
                    
                    # DEPOIS: Verifica eventos de Mutex Unlock APÓS executar
                    self._handle_mutex_unlock_event(self.current_task)
                    
                    # Verifica se a tarefa terminou
                    if self.current_task.tempo_restante <= 0:
                        self.current_task.state = STATE_TERMINATED
                        self.current_task.fim = self.time + 1
                        self.current_task.fimExec = self.time + 1
                        self.current_task.somaExec += ((self.time + 1) - self.current_task.inicioExec)
                        
                        # Aplica envelhecimento quando tarefa TERMINA (PRIOPEnv)
                        if isinstance(self.scheduler, PRIOPEnvScheduler):
                            self.scheduler.age_tasks(self.ready_queue)
                        
                        # Se a tarefa ainda tinha mutex(es), libera todos
                        if self.current_task.held_mutexes:
                            for mutex_id in list(self.current_task.held_mutexes):
                                mutex = self._get_mutex(mutex_id)
                                unblocked = mutex.unlock(self.current_task)
                                if unblocked:
                                    self.blocked_mutex_queue.remove(unblocked)
                                    unblocked.state = STATE_READY
                                    self.ready_queue.push_back(unblocked)
                        
                        self.done_tasks.append(self.current_task)
                        self.ready_queue.remove(self.current_task)
                        self.current_task = None
        else:
            # CPU ociosa (IDLE)
            self.gantt_data.append((self.time, "IDLE", [200, 200, 200], "IDLE"))
        
        # Atualiza tempo de espera por mutex para tarefas bloqueadas
        for task in self.blocked_mutex_queue:
            task.mutex_wait_time += 1
        
        # Envelhecimento por tick (PRIOPEnv-T): aplica a cada ciclo de clock
        if isinstance(self.scheduler, PRIOPEnvTickScheduler):
            self.scheduler.age_tasks_tick(self.ready_queue, self.current_task)

        # 11. Incrementa o relógio
        self.time += 1

    def run_full(self) -> bool:
        """
        Executa a simulação completa até todas as tarefas terminarem ou deadlock.
        
        Returns:
            True se terminou normalmente, False se detectou deadlock
        """
        max_iterations = 10000  # Limite de segurança
        iterations = 0
        
        while not self.is_finished() and iterations < max_iterations:
            self.step()
            iterations += 1
            
            # Verifica deadlock
            if self.is_deadlocked():
                return False
        
        return self.is_finished()
    
    def get_statistics(self) -> dict:
        """
        Calcula estatísticas de todas as tarefas concluídas.
        
        Returns:
            Dicionário com estatísticas por tarefa e médias gerais
        """
        stats = {
            'tasks': [],
            'avg_turnaround': 0,
            'avg_waiting': 0,
            'avg_response': 0,
            'avg_mutex_wait': 0,  # Novo: tempo médio de espera por mutex
            'mutex_info': {       # Novo: informações sobre mutex
                'total_waits': 0,
                'total_wait_time': 0
            }
        }
        
        total_turnaround = 0
        total_waiting = 0
        total_response = 0
        total_mutex_wait = 0
        total_mutex_count = 0
        
        for task in self.all_tasks:
            turnaround = task.fim - task.inicio  # Tempo total no sistema
            waiting = turnaround - task.duracao  # Tempo esperando (inclui I/O e mutex)
            response = task.inicioExec - task.inicio if task.ativacoes > 0 else 0  # Tempo até primeira execução
            
            stats['tasks'].append({
                'id': task.id,
                'turnaround_time': turnaround,
                'waiting_time': waiting,
                'response_time': response,
                'activations': task.ativacoes,
                'arrival': task.inicio,
                'completion': task.fim,
                'mutex_wait_time': task.mutex_wait_time,     # Novo
                'mutex_wait_count': task.mutex_wait_count    # Novo
            })
            
            total_turnaround += turnaround
            total_waiting += waiting
            total_response += response
            total_mutex_wait += task.mutex_wait_time
            total_mutex_count += task.mutex_wait_count
        
        n = len(self.all_tasks)
        if n > 0:
            stats['avg_turnaround'] = total_turnaround / n
            stats['avg_waiting'] = total_waiting / n
            stats['avg_response'] = total_response / n
            stats['avg_mutex_wait'] = total_mutex_wait / n
        
        stats['mutex_info']['total_waits'] = total_mutex_count
        stats['mutex_info']['total_wait_time'] = total_mutex_wait
        
        return stats
    
    def get_mutex_status(self, mutex_id: int = 1) -> dict:
        """
        Retorna o status atual de um mutex.
        
        Args:
            mutex_id: ID do mutex (default=1 para retrocompatibilidade)
        
        Returns:
            Dicionário com informações do mutex
        """
        if mutex_id not in self.mutexes:
            return {
                'locked': False,
                'owner_id': None,
                'waiting_count': 0
            }
        mutex = self.mutexes[mutex_id]
        return {
            'locked': mutex.locked,
            'owner_id': mutex.get_owner_id(),
            'waiting_count': len(mutex.waiting_queue)
        }
    
    def get_all_mutex_status(self) -> dict:
        """
        Retorna o status de todos os mutexes.
        
        Returns:
            Dicionário com informações de todos os mutexes
        """
        result = {}
        for mutex_id, mutex in self.mutexes.items():
            result[mutex_id] = {
                'locked': mutex.locked,
                'owner_id': mutex.get_owner_id(),
                'waiting_count': len(mutex.waiting_queue)
            }
        return result