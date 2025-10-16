from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class TCB:
    id: int
    RGB: List[int]
    state: int = 1
    prio_s: int = 0
    inicio: int = 0
    duracao: int = 0
    
    tempo_restante: int = field(init=False)

    prev: Optional["TCB"] = field(default=None, repr=False)
    next: Optional["TCB"] = field(default=None, repr=False)

    def __post_init__(self):
        self.tempo_restante = self.duracao

class TCBQueue:
    def __init__(self):
        self.head: Optional[TCB] = None
        self.tail: Optional[TCB] = None
        self._size = 0

    def is_empty(self) -> bool:
        return self.head is None

    def push_back(self, task: TCB):
        if self.tail is None:
            self.head = self.tail = task
        else:
            self.tail.next = task
            task.prev = self.tail
            self.tail = task
        self._size += 1

    def pop_front(self) -> Optional[TCB]:
        if self.head is None:
            return None
        task = self.head
        self.head = self.head.next
        if self.head is not None:
            self.head.prev = None
        else:
            self.tail = None
        task.next = task.prev = None
        self._size -= 1
        return task

    def remove(self, task: TCB):
        if task.prev:
            task.prev.next = task.next
        else:
            self.head = task.next

        if task.next:
            task.next.prev = task.prev
        else:
            self.tail = task.prev

        task.prev = task.next = None
        self._size -= 1

    def __iter__(self):
        current = self.head
        while current:
            yield current
            current = current.next

    def __len__(self):
        return self._size