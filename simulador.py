"""
Módulo principal do simulador de escalonamento de processos.
Gerencia a execução das tarefas, eventos de I/O, sincronização com mutex e coleta de estatísticas.
"""

from tasks import TCB, TCBQueue, STATE_NEW, STATE_READY, STATE_RUNNING, STATE_BLOCKED_IO, STATE_TERMINATED, STATE_BLOCKED_MUTEX
from scheduler import Scheduler, RoundRobinScheduler
from typing import List, Optional


class Mutex:
    """
    Representa um mutex para sincronização de tarefas.
    
    O mutex permite que apenas uma tarefa por vez acesse uma seção crítica.
    Tarefas que tentam adquirir um mutex já bloqueado entram numa fila de espera.
    """
    
    def __init__(self):
        """Inicializa o mutex como livre."""
        self.locked = False               # Estado do mutex: True = bloqueado, False = livre
        self.owner: Optional[TCB] = None  # Tarefa que possui o lock
        self.waiting_queue = TCBQueue()   # Fila de tarefas aguardando o mutex
    
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
            task.has_mutex = True
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
            task.has_mutex = False
            
            # Verifica se há tarefas aguardando na fila
            if not self.waiting_queue.is_empty():
                # Passa o mutex para a próxima tarefa na fila
                next_task = self.waiting_queue.pop_front()
                self.owner = next_task
                next_task.has_mutex = True
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
        
        # Mutex global para sincronização (Entrega B)
        self.mutex = Mutex()
        
        self.gantt_data = []  # Dados para o gráfico de Gantt: [(time, task_id, color, state), ...]
    
    # Alias para compatibilidade com código existente
    @property
    def blocked_queue(self):
        """Alias para blocked_io_queue (compatibilidade)."""
        return self.blocked_io_queue

    def _check_for_new_arrivals(self):
        """
        Verifica se há tarefas chegando no tempo atual.
        Move tarefas novas (state=1) para a fila de prontos (state=2).
        """
        for task in self.all_tasks:
            if task.inicio == self.time and task.state == STATE_NEW:
                task.state = STATE_READY
                self.ready_queue.push_back(task)
    
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
    
    def _handle_io_event(self, task: TCB) -> bool:
        """
        Trata um evento de I/O da tarefa.
        
        O I/O é verificado com base no tempo_exec_acumulado atual.
        
        Args:
            task: Tarefa que pode disparar evento de I/O
            
        Returns:
            True se a tarefa foi bloqueada por I/O, False caso contrário
        """
        io_event = task.check_io_event()
        if io_event:
            _, duracao = io_event
            # Bloqueia a tarefa por 'duracao' unidades de tempo
            # O desbloqueio acontece quando self.time >= io_blocked_until
            task.io_blocked_until = self.time + duracao
            task.state = STATE_BLOCKED_IO
            self.ready_queue.remove(task)
            self.blocked_io_queue.push_back(task)
            
            # Registra o bloqueio no Gantt para os próximos ciclos
            for t in range(1, duracao):  # Começa em 1 porque o ciclo atual já é registrado
                self.gantt_data.append((self.time + t, task.id, task.RGB, "IO"))
            
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
        if task.check_mutex_lock_event():
            if self.mutex.try_lock(task):
                # Conseguiu o lock, continua executando
                return False
            else:
                # Mutex ocupado, bloqueia a tarefa
                task.state = STATE_BLOCKED_MUTEX
                task.mutex_blocked_until = 0  # Indefinido, aguarda unlock de outra tarefa
                self.ready_queue.remove(task)
                self.mutex.add_to_waiting(task)
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
        if task.check_mutex_unlock_event():
            unblocked_task = self.mutex.unlock(task)
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

        # 1. Processa chegada de novas tarefas
        self._check_for_new_arrivals()
        
         # Registrar tarefas prontas (state = 2)
        for t in self.ready_queue:
            self.gantt_data.append((self.time, t.id, t.RGB, "READY"))
        # 2. Desbloqueia tarefas que completaram I/O
        self._check_io_unblock()
        # Registrar novamente tarefas prontas após desbloquear I/O
        for t in self.ready_queue:
            self.gantt_data.append((self.time, t.id, t.RGB, "READY"))
        
        # 3. Verifica preempção por quantum esgotado (Round-Robin)
        if isinstance(self.scheduler, RoundRobinScheduler):
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
                # Verifica eventos de I/O ANTES de executar
                if self._handle_io_event(self.current_task):
                    # Tarefa foi bloqueada por I/O, limpa current_task
                    self.gantt_data.append((self.time, self.current_task.id, self.current_task.RGB, "IO"))
                    self.current_task = None
                else:
                    # AGORA: Executa por 1 unidade de tempo
                    self.current_task.tempo_restante -= 1
                    self.current_task.tempo_exec_acumulado += 1
                    
                    # Decrementa quantum (se aplicável)
                    if hasattr(self.scheduler, 'decrement_quantum'):
                        self.scheduler.decrement_quantum()
                    
                    # Registra no Gantt
                    self.gantt_data.append((self.time, self.current_task.id, self.current_task.RGB, "EXEC"))
                    
                    # DEPOIS: Verifica eventos de Mutex Unlock APÓS executar
                    self._handle_mutex_unlock_event(self.current_task)
                    
                    # Verifica se a tarefa terminou
                    if self.current_task.tempo_restante <= 0:
                        self.current_task.state = STATE_TERMINATED
                        self.current_task.fim = self.time + 1  # Marca o tempo de término
                        self.current_task.fimExec = self.time + 1
                        self.current_task.somaExec += ((self.time + 1) - self.current_task.inicioExec)
                        
                        # Se a tarefa ainda tinha o mutex, libera
                        if self.current_task.has_mutex:
                            unblocked = self.mutex.unlock(self.current_task)
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

        # 11. Incrementa o relógio
        self.time += 1

    def run_full(self):
        """
        Executa a simulação completa até todas as tarefas terminarem.
        """
        while not self.is_finished():
            self.step()
    
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
    
    def get_mutex_status(self) -> dict:
        """
        Retorna o status atual do mutex.
        
        Returns:
            Dicionário com informações do mutex
        """
        return {
            'locked': self.mutex.locked,
            'owner_id': self.mutex.get_owner_id(),
            'waiting_count': len(self.mutex.waiting_queue)
        }