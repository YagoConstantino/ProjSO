from tasks import TCB, TCBQueue
from scheduler import Scheduler

class Simulator:
    def __init__(self, scheduler: Scheduler, all_tasks: list[TCB]):
        self.scheduler = scheduler
        self.all_tasks = sorted(all_tasks, key=lambda t: t.inicio)
        
        self.time = 0
        self.current_task: TCB | None = None
        
        self.ready_queue = TCBQueue()
        self.done_tasks = []
        
        self.gantt_data = []

    def _check_for_new_arrivals(self):
        for task in self.all_tasks:
            if task.inicio == self.time:
                task.state = 2
                self.ready_queue.push_back(task)

    def is_finished(self) -> bool:
        return len(self.done_tasks) == len(self.all_tasks)

    def step(self):
        if self.is_finished():
            return

        self._check_for_new_arrivals()
        
        next_task = self.scheduler.select_next_task(self.ready_queue, self.current_task)
        
        if self.current_task != next_task:
            if self.current_task:
                self.current_task.state = 2
            self.current_task = next_task
            if self.current_task:
                self.current_task.state = 3
        
        if self.current_task:
            self.current_task.tempo_restante -= 1
            self.gantt_data.append((self.time, self.current_task.id, self.current_task.RGB))
            
            if self.current_task.tempo_restante <= 0:
                self.current_task.state = 5
                self.done_tasks.append(self.current_task)
                self.ready_queue.remove(self.current_task)
                self.current_task = None
        else:
            self.gantt_data.append((self.time, "IDLE", [200, 200, 200]))

        self.time += 1

    def run_full(self):
        while not self.is_finished():
            self.step()