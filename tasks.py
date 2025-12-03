"""
Módulo de estruturas de dados para controle de tarefas (TCB - Task Control Block).
Define a estrutura TCB e a fila de tarefas TCBQueue.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

# Estados da tarefa
STATE_NEW = 1           # Novo - tarefa criada mas não chegou
STATE_READY = 2         # Pronto - aguardando na fila de prontos
STATE_RUNNING = 3       # Executando - usando a CPU
STATE_BLOCKED_IO = 4    # Bloqueado - aguardando I/O
STATE_TERMINATED = 5    # Terminado - execução completa
STATE_BLOCKED_MUTEX = 6 # Bloqueado - aguardando mutex

@dataclass
class TCB:
    """
    Task Control Block - Estrutura que representa uma tarefa no sistema.
    
    Atributos:
        id (int): Identificador único da tarefa
        RGB (List[int]): Cor RGB [R, G, B] para visualização no Gantt
        state (int): Estado da tarefa (1=Novo, 2=Pronto, 3=Executando, 4=Bloqueado I/O, 5=Terminado, 6=Bloqueado Mutex)
        prio_s (int): Prioridade estática da tarefa (maior = mais prioritária)
        prio_d (int): Prioridade dinâmica (pode mudar durante execução)
        inicio (int): Tempo de chegada/ingresso da tarefa no sistema
        duracao (int): Tempo total de CPU necessário para completar a tarefa
        tempo_restante (int): Tempo de CPU restante para completar
        io_events (List[Tuple[int, int]]): Lista de eventos I/O [(tempo_relativo, duracao), ...]
        io_blocked_until (int): Timestamp até quando a tarefa fica bloqueada em I/O
        tempo_exec_acumulado (int): Tempo total já executado pela tarefa
        
        # Eventos de Mutex (Entrega B)
        ml_events (List[int]): Lista de tempos relativos para tentar mutex lock
        mu_events (List[int]): Lista de tempos relativos para fazer mutex unlock
        mutex_blocked_until (int): Timestamp até quando a tarefa fica bloqueada por mutex (0 = indefinido)
        mutex_wait_time (int): Tempo total bloqueado aguardando mutex
        mutex_wait_count (int): Número de vezes que a tarefa esperou pelo mutex
        has_mutex (bool): Se a tarefa possui o mutex atualmente
        
        # Estatísticas de execução
        ativacoes (int): Número de vezes que a tarefa foi colocada em execução
        inicioExec (int): Timestamp do último início de execução
        fimExec (int): Timestamp do último fim de execução
        somaExec (int): Soma total de tempo de execução
        fim (int): Timestamp de término da tarefa
        
        # Ponteiros para lista duplamente encadeada
        prev (Optional[TCB]): Ponteiro para tarefa anterior na fila
        next (Optional[TCB]): Ponteiro para próxima tarefa na fila
    """
    id: int
    RGB: List[int]
    state: int = 1
    prio_s: int = 0
    prio_d: int = 0
    inicio: int = 0
    duracao: int = 0
    
    tempo_restante: int = field(init=False)
    io_events: List[Tuple[int, int]] = field(default_factory=list)
    io_blocked_until: int = 0
    tempo_exec_acumulado: int = 0
    
    # Campos para Mutex (Entrega B)
    ml_events: List[int] = field(default_factory=list)  # Tempos relativos para mutex lock
    mu_events: List[int] = field(default_factory=list)  # Tempos relativos para mutex unlock
    mutex_blocked_until: int = 0   # Timestamp de quando será desbloqueado (0 = indefinido, aguarda unlock de outra tarefa)
    mutex_wait_time: int = 0       # Tempo total bloqueado por mutex
    mutex_wait_count: int = 0      # Vezes que esperou pelo mutex
    has_mutex: bool = False        # Se possui o mutex
    
    # Estatísticas
    ativacoes: int = 0
    inicioExec: int = 0
    fimExec: int = 0
    somaExec: int = 0
    fim: int = 0

    prev: Optional["TCB"] = field(default=None, repr=False)
    next: Optional["TCB"] = field(default=None, repr=False)

    def __post_init__(self):
        """Inicializa o tempo restante igual à duração total."""
        self.tempo_restante = self.duracao
    
    def check_io_event(self) -> Optional[Tuple[int, int]]:
        """
        Verifica se há um evento de I/O que deve ser disparado agora.
        Remove o evento da lista após disparar para não repetir.
        
        Returns:
            Tupla (tempo_inicio, duracao) do evento I/O ou None se não houver
        """
        for i, (tempo_inicio, duracao) in enumerate(self.io_events):
            if tempo_inicio == self.tempo_exec_acumulado:
                # Remove o evento para não disparar novamente
                self.io_events.pop(i)
                return (tempo_inicio, duracao)
        return None
    
    def check_mutex_lock_event(self) -> bool:
        """
        Verifica se há um evento de mutex lock que deve ser disparado agora.
        Remove o evento da lista após disparar para não repetir.
        
        Returns:
            True se deve tentar adquirir o mutex, False caso contrário
        """
        for i, tempo in enumerate(self.ml_events):
            if tempo == self.tempo_exec_acumulado:
                self.ml_events.pop(i)
                return True
        return False
    
    def check_mutex_unlock_event(self) -> bool:
        """
        Verifica se há um evento de mutex unlock que deve ser disparado agora.
        Remove o evento da lista após disparar para não repetir.
        
        Returns:
            True se deve liberar o mutex, False caso contrário
        """
        for i, tempo in enumerate(self.mu_events):
            if tempo == self.tempo_exec_acumulado:
                self.mu_events.pop(i)
                return True
        return False
        return None

class TCBQueue:
    """
    Fila duplamente encadeada de TCBs (Task Control Blocks).
    Implementa operações de fila para gerenciar tarefas prontas para execução.
    """
    
    def __init__(self):
        """Inicializa uma fila vazia."""
        self.head: Optional[TCB] = None
        self.tail: Optional[TCB] = None
        self._size = 0

    def is_empty(self) -> bool:
        """Verifica se a fila está vazia."""
        return self.head is None

    def push_back(self, task: TCB):
        """
        Adiciona uma tarefa no final da fila.
        
        Args:
            task: Tarefa a ser adicionada
        """
        if self.tail is None:
            self.head = self.tail = task
        else:
            self.tail.next = task
            task.prev = self.tail
            self.tail = task
        self._size += 1

    def pop_front(self) -> Optional[TCB]:
        """
        Remove e retorna a tarefa do início da fila.
        
        Returns:
            Tarefa removida ou None se a fila estiver vazia
        """
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
        """
        Remove uma tarefa específica da fila.
        
        Args:
            task: Tarefa a ser removida
        """
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
        """Permite iterar sobre as tarefas na fila."""
        current = self.head
        while current:
            yield current
            current = current.next

    def __len__(self):
        """Retorna o número de tarefas na fila."""
        return self._size
    
    def find_by_id(self, task_id: int) -> Optional[TCB]:
        """
        Busca uma tarefa pelo ID.
        
        Args:
            task_id: ID da tarefa a ser buscada
            
        Returns:
            Tarefa encontrada ou None
        """
        for task in self:
            if task.id == task_id:
                return task
        return None

    def get_by_priority(self) -> List[TCB]:
        """
        Retorna lista de tarefas ordenadas por prioridade (maior primeiro).
        
        Returns:
            Lista de tarefas ordenadas por prioridade decrescente
        """
        return sorted(self, key=lambda t: t.prio_s, reverse=True)