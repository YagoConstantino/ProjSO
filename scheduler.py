"""
Módulo de algoritmos de escalonamento de processos.
Implementa diferentes políticas de escalonamento: FIFO, SRTF, Priority e Round-Robin.
"""

from abc import ABC, abstractmethod
from typing import Optional
from tasks import TCB, TCBQueue

class Scheduler(ABC):
    """
    Classe abstrata base para todos os escalonadores.
    Define a interface que todos os algoritmos de escalonamento devem implementar.
    """
    
    def __init__(self, quantum: Optional[int] = None):
        """
        Inicializa o escalonador.
        
        Args:
            quantum: Quantum de tempo para escalonadores preemptivos (Round-Robin)
        """
        self.quantum = quantum
        self.time_slice_remaining = quantum if quantum else 0
    
    @abstractmethod
    def select_next_task(self, ready_queue: TCBQueue, current_task: Optional[TCB], time: int) -> Optional[TCB]:
        """
        Seleciona a próxima tarefa a ser executada.
        
        Args:
            ready_queue: Fila de tarefas prontas para execução
            current_task: Tarefa atualmente em execução (ou None)
            time: Tempo atual da simulação
            
        Returns:
            Próxima tarefa a executar ou None se não houver tarefas
        """
        pass
    
    def reset_quantum(self):
        """Reseta o contador de quantum para o valor inicial."""
        self.time_slice_remaining = self.quantum if self.quantum else 0
    
    def decrement_quantum(self):
        """Decrementa o contador de quantum."""
        if self.time_slice_remaining > 0:
            self.time_slice_remaining -= 1


class FIFOScheduler(Scheduler):
    """
    Escalonador FIFO (First In, First Out) / FCFS (First Come, First Served).
    Executa as tarefas na ordem de chegada, sem preempção.
    """
    
    def select_next_task(self, ready_queue: TCBQueue, current_task: Optional[TCB], time: int) -> Optional[TCB]:
        """
        Seleciona a próxima tarefa seguindo a política FIFO.
        Mantém a tarefa atual até completar, depois pega a primeira da fila.
        """
        # Se há uma tarefa em execução e ela ainda tem trabalho, continua com ela
        if current_task and current_task.tempo_restante > 0:
            return current_task
        
        # Caso contrário, pega a primeira tarefa da fila (se houver)
        if not ready_queue.is_empty():
            return ready_queue.head
        
        return None


class SRTFScheduler(Scheduler):
    """
    Escalonador SRTF (Shortest Remaining Time First).
    Executa sempre a tarefa com menor tempo restante, com preempção.
    """
    
    def select_next_task(self, ready_queue: TCBQueue, current_task: Optional[TCB], time: int) -> Optional[TCB]:
        """
        Seleciona a tarefa com menor tempo restante.
        Pode preemptar a tarefa atual se chegar uma com tempo menor.
        """
        if ready_queue.is_empty():
            return None
        
        # Encontra a tarefa com menor tempo restante na fila
        shortest_task = min(ready_queue, key=lambda task: task.tempo_restante)
        return shortest_task


class PriorityScheduler(Scheduler):
    """
    Escalonador por Prioridade.
    Executa sempre a tarefa de maior prioridade, com preempção.
    """
    
    def select_next_task(self, ready_queue: TCBQueue, current_task: Optional[TCB], time: int) -> Optional[TCB]:
        """
        Seleciona a tarefa com maior prioridade estática.
        Pode preemptar a tarefa atual se chegar uma com prioridade maior.
        """
        if ready_queue.is_empty():
            return None
        
        # Encontra a tarefa com maior prioridade na fila
        highest_prio_task = max(ready_queue, key=lambda task: task.prio_s)
        return highest_prio_task


class RoundRobinScheduler(Scheduler):
    """
    Escalonador Round-Robin.
    Executa cada tarefa por um quantum de tempo, depois passa para a próxima.
    """
    
    def select_next_task(self, ready_queue: TCBQueue, current_task: Optional[TCB], time: int) -> Optional[TCB]:
        """
        Seleciona a próxima tarefa seguindo a política Round-Robin.
        Preempta quando o quantum se esgota.
        """
        if ready_queue.is_empty():
            return None
        
        # Se há tarefa em execução e ainda tem quantum, continua
        if current_task and current_task in ready_queue and self.time_slice_remaining > 0:
            return current_task
        
        # Quantum esgotado ou sem tarefa atual: pega a próxima da fila
        # A tarefa atual preemptada já foi movida para o fim da fila pelo simulador
        return ready_queue.head


class PRIOPEnvScheduler(Scheduler):
    """
    Escalonador Preemptivo por Prioridades com Envelhecimento (PRIOPEnv).
    
    Características:
    - Preemptivo: tarefa de maior prioridade sempre executa
    - Envelhecimento: tarefas prontas ganham +alpha na prioridade dinâmica
    - Evita starvation de tarefas de baixa prioridade
    
    Atributos:
        quantum (int): Quantum para cada tarefa (slice de tempo)
        alpha (int): Valor adicionado à prioridade dinâmica no envelhecimento
        time_slice_remaining (int): Tempo restante do quantum atual
    """
    
    def __init__(self, quantum: int = 1, alpha: int = 1):
        """
        Inicializa o escalonador PRIOPEnv.
        
        Args:
            quantum: Fatia de tempo para cada tarefa
            alpha: Incremento de prioridade no envelhecimento
        """
        self.quantum = quantum
        self.alpha = alpha
        self.time_slice_remaining = quantum
    
    def select_next_task(self, ready_queue, current_task, current_time) -> Optional[TCB]:
        """
        Seleciona a tarefa com maior prioridade dinâmica.
        É preemptivo: se uma tarefa de maior prioridade estiver pronta, ela executa.
        
        Args:
            ready_queue: Fila de tarefas prontas
            current_task: Tarefa atualmente em execução (pode ser None)
            current_time: Tempo atual da simulação
            
        Returns:
            Tarefa com maior prioridade dinâmica, ou None se fila vazia
        """
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
        if current_task and best_task:
            if best_task.prio_d > current_task.prio_d:
                return best_task
            elif best_task.prio_d == current_task.prio_d:
                # Mantém a tarefa atual se prioridades iguais
                return current_task
            else:
                return current_task
        
        return best_task
    
    def reset_quantum(self):
        """Reseta o quantum quando uma nova tarefa começa a executar."""
        self.time_slice_remaining = self.quantum
    
    def decrement_quantum(self):
        """Decrementa o quantum a cada unidade de tempo executada."""
        self.time_slice_remaining -= 1
    
    def age_tasks(self, ready_queue, exclude_task=None):
        """
        Aplica envelhecimento a todas as tarefas na fila de prontos.
        Incrementa prio_d em +alpha para cada tarefa.
        
        Args:
            ready_queue: Fila de tarefas prontas
            exclude_task: Tarefa a ser excluída do envelhecimento (ex: a que acabou de chegar)
        """
        for task in ready_queue:
            if task != exclude_task:
                task.prio_d += self.alpha


# Alias para compatibilidade
PRIOPEnv = PRIOPEnvScheduler