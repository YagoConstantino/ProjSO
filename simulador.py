"""
Módulo principal do simulador de escalonamento de processos.
Gerencia a execução das tarefas, eventos de I/O e coleta de estatísticas.
"""

from tasks import TCB, TCBQueue
from scheduler import Scheduler, RoundRobinScheduler
from typing import List, Optional

class Simulator:
    """
    Simulador de escalonamento de processos.
    
    Gerencia o ciclo de vida das tarefas, incluindo:
    - Chegada de novas tarefas
    - Escalonamento de CPU
    - Eventos de I/O
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
        
        self.ready_queue = TCBQueue()  # Fila de tarefas prontas
        self.blocked_queue = TCBQueue()  # Fila de tarefas bloqueadas em I/O
        self.done_tasks = []  # Lista de tarefas concluídas
        
        self.gantt_data = []  # Dados para o gráfico de Gantt: [(time, task_id, color, state), ...]

    def _check_for_new_arrivals(self):
        """
        Verifica se há tarefas chegando no tempo atual.
        Move tarefas novas (state=1) para a fila de prontos (state=2).
        """
        for task in self.all_tasks:
            if task.inicio == self.time and task.state == 1:
                task.state = 2  # Estado: Pronto
                self.ready_queue.push_back(task)
    
    def _check_io_unblock(self):
        """
        Verifica se há tarefas bloqueadas que completaram seu I/O.
        Move tarefas da fila de bloqueadas para a fila de prontos.
        """
        tasks_to_unblock = []
        for task in self.blocked_queue:
            if self.time >= task.io_blocked_until:
                tasks_to_unblock.append(task)
        
        for task in tasks_to_unblock:
            self.blocked_queue.remove(task)
            task.state = 2  # Estado: Pronto
            self.ready_queue.push_back(task)
    
    def _handle_io_event(self, task: TCB):
        """
        Trata um evento de I/O da tarefa.
        
        Args:
            task: Tarefa que disparou o evento de I/O
        """
        io_event = task.check_io_event()
        if io_event:
            _, duracao = io_event
            # Bloqueia a tarefa por 'duracao' unidades de tempo
            task.io_blocked_until = self.time + duracao
            task.state = 4  # Estado: Bloqueado
            self.ready_queue.remove(task)
            self.blocked_queue.push_back(task)
            
            # Registra o bloqueio no Gantt
            for t in range(duracao):
                self.gantt_data.append((self.time + t, task.id, task.RGB, "IO"))  # Usa cor da tarefa, marca como IO
            
            return True
        return False

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
        3. Seleciona próxima tarefa a executar
        4. Executa a tarefa por 1 unidade de tempo
        5. Verifica eventos de I/O
        6. Atualiza estatísticas
        7. Incrementa o tempo
        """
        if self.is_finished():
            return

        # 1. Processa chegada de novas tarefas
        self._check_for_new_arrivals()
        
        # 2. Desbloqueia tarefas que completaram I/O
        self._check_io_unblock()
        
        # 3. Verifica preempção por quantum esgotado (Round-Robin)
        if isinstance(self.scheduler, RoundRobinScheduler):
            if self.current_task and self.scheduler.time_slice_remaining <= 0 and self.current_task.tempo_restante > 0:
                # Quantum esgotado: move tarefa atual para o fim da fila
                self.ready_queue.remove(self.current_task)
                self.ready_queue.push_back(self.current_task)
                # Força troca de contexto
                self.current_task.state = 2  # Volta para pronto
                self.current_task.fimExec = self.time
                self.current_task.somaExec += (self.time - self.current_task.inicioExec)
                self.current_task = None
        
        # 4. Seleciona a próxima tarefa a executar
        next_task = self.scheduler.select_next_task(self.ready_queue, self.current_task, self.time)
        
        # 5. Gerencia troca de contexto
        if self.current_task != next_task:
            # Tarefa atual foi preemptada ou terminou
            if self.current_task:
                self.current_task.state = 2  # Volta para pronto
                self.current_task.fimExec = self.time
                self.current_task.somaExec += (self.time - self.current_task.inicioExec)
            
            # Nova tarefa entra em execução
            self.current_task = next_task
            if self.current_task:
                self.current_task.state = 3  # Estado: Executando
                self.current_task.inicioExec = self.time
                self.current_task.ativacoes += 1
                
                # Reseta quantum para a nova tarefa
                if hasattr(self.scheduler, 'reset_quantum'):
                    self.scheduler.reset_quantum()
        
        # 6. Executa a tarefa atual
        if self.current_task:
            # Executa por 1 unidade de tempo
            self.current_task.tempo_restante -= 1
            self.current_task.tempo_exec_acumulado += 1
            
            # Decrementa quantum (se aplicável)
            if hasattr(self.scheduler, 'decrement_quantum'):
                self.scheduler.decrement_quantum()
            
            # Registra no Gantt
            self.gantt_data.append((self.time, self.current_task.id, self.current_task.RGB, "EXEC"))
            
            # 6. Verifica eventos de I/O
            if self._handle_io_event(self.current_task):
                # Tarefa foi bloqueada, limpa current_task
                self.current_task = None
            
            # 7. Verifica se a tarefa terminou
            elif self.current_task and self.current_task.tempo_restante <= 0:
                self.current_task.state = 5  # Estado: Terminado
                self.current_task.fim = self.time + 1  # Marca o tempo de término
                self.current_task.fimExec = self.time + 1
                self.current_task.somaExec += ((self.time + 1) - self.current_task.inicioExec)
                
                self.done_tasks.append(self.current_task)
                self.ready_queue.remove(self.current_task)
                self.current_task = None
        else:
            # CPU ociosa (IDLE)
            self.gantt_data.append((self.time, "IDLE", [200, 200, 200], "IDLE"))

        # 8. Incrementa o relógio
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
            'avg_response': 0
        }
        
        total_turnaround = 0
        total_waiting = 0
        total_response = 0
        
        for task in self.all_tasks:
            turnaround = task.fim - task.inicio  # Tempo total no sistema
            waiting = turnaround - task.duracao  # Tempo esperando
            response = task.inicioExec - task.inicio if task.ativacoes > 0 else 0  # Tempo até primeira execução
            
            stats['tasks'].append({
                'id': task.id,
                'turnaround_time': turnaround,
                'waiting_time': waiting,
                'response_time': response,
                'activations': task.ativacoes,
                'arrival': task.inicio,
                'completion': task.fim
            })
            
            total_turnaround += turnaround
            total_waiting += waiting
            total_response += response
        
        n = len(self.all_tasks)
        if n > 0:
            stats['avg_turnaround'] = total_turnaround / n
            stats['avg_waiting'] = total_waiting / n
            stats['avg_response'] = total_response / n
        
        return stats