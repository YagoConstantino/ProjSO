from abc import ABC, abstractmethod
from typing import Optional
from tasks import TCB, TCBQueue # <<< LINHA ATUALIZADA

class Scheduler(ABC):
    @abstractmethod
    def select_next_task(self, ready_queue: TCBQueue, current_task: Optional[TCB]) -> Optional[TCB]:
        pass

class FIFOScheduler(Scheduler):
    def select_next_task(self, ready_queue: TCBQueue, current_task: Optional[TCB]) -> Optional[TCB]:
        if current_task and current_task.tempo_restante > 0:
            return current_task
        
        if not ready_queue.is_empty():
            return ready_queue.head
        
        return None

class SRTFScheduler(Scheduler):
    def select_next_task(self, ready_queue: TCBQueue, current_task: Optional[TCB]) -> Optional[TCB]:
        if ready_queue.is_empty():
            return None
        
        shortest_task = min(ready_queue, key=lambda task: task.tempo_restante)
        return shortest_task

class PriorityScheduler(Scheduler):
    def select_next_task(self, ready_queue: TCBQueue, current_task: Optional[TCB]) -> Optional[TCB]:
        if ready_queue.is_empty():
            return None
            
        highest_prio_task = max(ready_queue, key=lambda task: task.prio_s)
        return highest_prio_task