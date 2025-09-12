from dataclasses import dataclass,field
from typing import Optional

"""// Estrutura que define um Task Control Block (TCB)
typedef struct task_t
{
   struct task_t *prev, *next ;     // ponteiros para usar em filas
   int id ;             // identificador da tarefa
   int RGB[3];
   ucontext_t context ;         // contexto armazenado da tarefa
   unsigned char state;  // indica o estado de uma tarefa (ver defines no final do arquivo ppos.h):
                          // n - nova, r - pronta, x - executando, s - suspensa, e - terminada
   struct task_t* queue;
   struct task_t* joinQueue;
   int exitCode;
   unsigned int awakeTime; // used to store the time when it should be waked up


   // ... (outros campos deve ser adicionados APOS esse comentario)
   int prio_s; //prioridade estatica
   int prio_d; //prioridade dinamica
   int flag; //se 0 é uma tarefa de sistema como main e dispatcher
   int quantum; // quantum = 20
   unsigned int inicio;
   unsigned int fim;
   unsigned int inicioexec;
   unsigned int fimexec;
   unsigned int somaexec;
   int ativacoes;
} task_t ;
"""
@dataclass
class TCB:
    #Classe para a task do escalonador
    id:int
    #variáveis para a cor da task
    R:int
    G:int
    B:int
    
    #indica o estado de uma tarefa (ver defines no final do arquivo ppos.h):
    #n - nova, r - pronta, x - executando, s - suspensa, e - terminada
    state: str

    # códigos / timers / prioridades / estatísticas
    exitCode: int = 0
    awakeTime: int = 0  # quando deve ser acordada (timestamp ou tick)

    # campos adicionais
    prio_s: int = 0     # prioridade estática
    prio_d: int = 0     # prioridade dinâmica
    quantum: int = 20   # quantum padrão = 20

    inicio: int = 0
    fim: int = 0
    inicioexec: int = 0
    fimexec: int = 0
    somaexec: int = 0
    ativacoes: int = 0
    duracao: int = 0

    # campos para lista duplamente encadeada
    prev: Optional["TCB"] = field(default=None, repr=False)
    next: Optional["TCB"] = field(default=None, repr=False)






class TCBQueue:
    def __init__(self):
        self.head: Optional[TCB] = None
        self.tail: Optional[TCB] = None
        self._size = 0

    def is_empty(self) -> bool:
        return self.head is None

    def push_back(self, task: TCB):
        """Insere no final da fila"""
        if self.tail is None:
            self.head = self.tail = task
        else:
            self.tail.next = task
            task.prev = self.tail
            self.tail = task
        self._size += 1

    def pop_front(self) -> Optional[TCB]:
        """Remove do início da fila"""
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
        """Remove um nó específico"""
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
        cur = self.head
        while cur:
            yield cur
            cur = cur.next

    def __len__(self):
        return self._size
