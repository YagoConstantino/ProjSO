from dataclasses import dataclass, field
from typing import List, Optional, ClassVar

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
    """
    Conversão do TCB C++ para Python.
    - state mantido como int (1=nova,2=pronta,3=executando,4=suspensa,5=terminada)
    - RGB como lista de 3 ints
    """
    id: int
    RGB: List[int]

    # estado: usar inteiros como no C++
    state: int = 1

    # códigos / timers / prioridades / estatísticas
    exitCode: int = 0
    awakeTime: int = 0  # quando deve ser acordada (timestamp ou tick)

    # campos adicionais
    prio_s: int = 0     # prioridade estática
    prio_d: int = 0     # prioridade dinâmica
    # quantum comentado no C++ original — não incluído por padrão

    inicio: int = 0
    fim: int = 0
    inicioExec: int = 0
    fimExec: int = 0
    somaExec: int = 0
    ativacoes: int = 0
    duracao: int = 0

    # ponteiros para listas (manter para compatibilidade conceitual)
    prev: Optional["TCB"] = field(default=None, repr=False)
    next: Optional["TCB"] = field(default=None, repr=False)

    # ---------- construtores alternativos (espelham os overloads do C++) ----------
    @classmethod
    def from_id_state_rgb(cls, ID: int, sta: int, rgb: List[int]) -> "TCB":
        """Equivalente: TCB(int ID,int sta,const array<int,3> v)"""
        if len(rgb) != 3:
            raise ValueError("RGB deve ter exatamente 3 inteiros")
        return cls(id=ID, RGB=list(rgb), state=sta)

    @classmethod
    def from_params(cls, ID: int, rgb: List[int], pris: int, ini: int, dura: int) -> "TCB":
        """
        Equivalente:
        TCB(int ID,const array<int,3> v,int pris,int ini,int dura)
        Define prio_d = prio_s e state = 1 (nova).
        """
        if len(rgb) != 3:
            raise ValueError("RGB deve ter exatamente 3 inteiros")
        obj = cls(id=ID, RGB=list(rgb))
        obj.prio_s = pris
        obj.prio_d = pris
        obj.inicio = ini
        obj.duracao = dura
        obj.exitCode = 0
        obj.awakeTime = 0
        obj.state = 1
        return obj

    # -------------------- GETTERS --------------------
    def getState(self) -> int:
        return self.state

    def getExitCode(self) -> int:
        return self.exitCode

    def getAwakeTime(self) -> int:
        return self.awakeTime

    def getPrioD(self) -> int:
        return self.prio_d

    def getFim(self) -> int:
        return self.fim

    def getInicioExec(self) -> int:
        return self.inicioExec

    def getFimExec(self) -> int:
        return self.fimExec

    def getSomaExec(self) -> int:
        return self.somaExec

    def getAtivacoes(self) -> int:
        return self.ativacoes

    # -------------------- SETTERS --------------------
    def setState(self, s: int) -> None:
        self.state = int(s)

    def setExitCode(self, code: int) -> None:
        self.exitCode = int(code)

    def setAwakeTime(self, t: int) -> None:
        self.awakeTime = int(t)

    def setPrioD(self, p: int) -> None:
        self.prio_d = int(p)

    def setFim(self, f: int) -> None:
        self.fim = int(f)

    def setInicioExec(self, v: int) -> None:
        self.inicioExec = int(v)

    def setFimExec(self, v: int) -> None:
        self.fimExec = int(v)

    def setSomaExec(self, s: int) -> None:
        self.somaExec = int(s)

    def setAtivacoes(self, a: int) -> None:
        self.ativacoes = int(a)

    def __repr__(self) -> str:
        return (f"TCB(id={self.id}, state={self.state}, RGB={self.RGB}, "
                f"prio_s={self.prio_s}, prio_d={self.prio_d}, inicio={self.inicio}, duracao={self.duracao})")



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
