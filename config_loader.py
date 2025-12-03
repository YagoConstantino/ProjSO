"""
Módulo responsável por carregar arquivos de configuração do simulador.
Lê arquivos .txt contendo definições de algoritmo, quantum e tarefas.

Formato do arquivo de configuração:
    - Linha 1: ALGORITMO;QUANTUM (ex: 'FIFO;3' ou 'SRTF;')
    - Linhas seguintes: t<ID>;cor_id;ingresso;duracao;prioridade;[eventos]
    - Eventos podem ser: IO:tempo-duracao, ML:tempo (mutex lock), MU:tempo (mutex unlock)
    - Múltiplos eventos são separados por ';'
    - Linhas começando com '#' são ignoradas (comentários)
"""

from tasks import TCB
from typing import List, Tuple, Optional, Dict

# Mapeamento de IDs de cores para valores RGB
# Usado para colorir as tarefas no gráfico de Gantt
COLOR_MAP = {
    "0": [255, 0, 0],      # Vermelho
    "1": [0, 255, 0],      # Verde
    "2": [0, 0, 255],      # Azul
    "3": [255, 255, 0],    # Amarelo
    "4": [0, 255, 255],    # Ciano
    "5": [255, 0, 255],    # Magenta
    "6": [125, 22, 123]    # Roxo customizado
}


def parse_events(events_string: str) -> Tuple[List[Tuple[int, int]], List[int], List[int]]:
    """
    Analisa string de eventos e extrai I/O, mutex lock e mutex unlock.
    
    Args:
        events_string: String contendo eventos separados por ';'
            - IO:tempo-duracao (ex: 'IO:2-1')
            - ML:tempo (ex: 'ML:1') - Mutex Lock
            - MU:tempo (ex: 'MU:3') - Mutex Unlock
    
    Returns:
        Tupla contendo:
            - io_events: Lista de tuplas (tempo_inicio, duracao) para eventos I/O
            - ml_events: Lista de tempos relativos para mutex lock
            - mu_events: Lista de tempos relativos para mutex unlock
    
    Exemplo:
        >>> parse_events('ML:1;IO:2-1;MU:3')
        ([(2, 1)], [1], [3])
    """
    io_events = []
    ml_events = []
    mu_events = []
    
    if not events_string:
        return io_events, ml_events, mu_events
    
    # Divide múltiplos eventos separados por ';'
    parts = events_string.split(';')
    
    for part in parts:
        part = part.strip()
        if not part:
            continue
            
        if part.startswith('IO:'):
            # Evento de I/O: formato 'IO:tempo-duracao'
            io_data = part[3:].split('-')
            if len(io_data) == 2:
                try:
                    tempo_inicio = int(io_data[0])
                    duracao = int(io_data[1])
                    io_events.append((tempo_inicio, duracao))
                except ValueError:
                    print(f"Aviso: formato de I/O inválido: '{part}'")
        
        elif part.startswith('ML:'):
            # Evento de Mutex Lock: formato 'ML:tempo'
            try:
                tempo = int(part[3:])
                ml_events.append(tempo)
            except ValueError:
                print(f"Aviso: formato de ML inválido: '{part}'")
        
        elif part.startswith('MU:'):
            # Evento de Mutex Unlock: formato 'MU:tempo'
            try:
                tempo = int(part[3:])
                mu_events.append(tempo)
            except ValueError:
                print(f"Aviso: formato de MU inválido: '{part}'")
    
    return io_events, ml_events, mu_events


def parse_io_events(io_string: str) -> List[Tuple[int, int]]:
    """
    Analisa string de eventos de I/O no formato 'IO:tempo-duracao' ou múltiplos separados por ';'.
    (Mantido para compatibilidade com código legado)
    
    Args:
        io_string: String contendo eventos de I/O (ex: 'IO:2-1' ou 'IO:2-1;IO:5-2')
    
    Returns:
        Lista de tuplas (tempo_inicio, duracao) para cada evento de I/O
    
    Exemplo:
        >>> parse_io_events('IO:2-1;IO:5-2')
        [(2, 1), (5, 2)]
    """
    io_events, _, _ = parse_events(io_string)
    return io_events

def load_simulation_config(filepath: str) -> Tuple[str, Optional[int], List[TCB]]:
    """
    Carrega a configuração da simulação a partir de um arquivo de texto.
    
    Formato do arquivo:
        - Linha 1: ALGORITMO;QUANTUM (ex: 'FIFO;3' ou 'SRTF;')
        - Linhas seguintes: t<ID>;cor_id;ingresso;duracao;prioridade;[eventos]
        - Eventos podem incluir: IO:tempo-duracao, ML:tempo, MU:tempo
        - Linhas começando com '#' são ignoradas (comentários)
    
    Args:
        filepath: Caminho para o arquivo de configuração
    
    Returns:
        Tupla contendo:
            - scheduler_type (str): Nome do algoritmo (FIFO, SRTF, PRIO, PRIOP, RR, etc.)
            - quantum (Optional[int]): Valor do quantum (para Round-Robin) ou None
            - tasks (List[TCB]): Lista de tarefas carregadas
    
    Raises:
        FileNotFoundError: Se o arquivo não for encontrado
        ValueError: Se houver erro no formato dos dados
    """
    tasks = []
    scheduler_type = ""
    quantum = None

    with open(filepath, 'r') as f:
        # A primeira linha define o algoritmo e o quantum (ex: "FIFO;3" ou "SRTF;")
        first_line = f.readline().strip().split(';')
        scheduler_type = first_line[0].strip().upper()
        if len(first_line) > 1 and first_line[1].strip():
            quantum = int(first_line[1].strip())

        # As linhas seguintes definem cada tarefa
        for line in f:
            try:
                # Ignora linhas vazias ou comentários que começam com '#'
                if not line.strip() or line.strip().startswith('#'):
                    continue
                
                # Divide a linha pelos delimitadores ';'
                parts = line.strip().split(';')
                
                # Extrai o ID da tarefa (remove o 't' do início)
                task_id_str = parts[0].strip().lower().replace('t', '')
                task_id = int(task_id_str)
                
                # Busca a cor no mapeamento ou usa cinza padrão
                color_id = parts[1].strip()
                rgb_color = COLOR_MAP.get(color_id, [128, 128, 128])

                # Extrai os parâmetros temporais e de prioridade
                ingresso = int(parts[2])
                duracao = int(parts[3])
                
                # Prioridade: pode estar em parts[4] ou pode ser um evento
                prioridade = 0
                events_start_index = 5  # Índice onde começam os eventos
                
                # Verifica se parts[4] é prioridade ou evento
                if len(parts) > 4:
                    part4 = parts[4].strip()
                    if part4 and not any(part4.startswith(prefix) for prefix in ['IO:', 'ML:', 'MU:']):
                        # É um número de prioridade
                        try:
                            prioridade = int(part4)
                        except ValueError:
                            # Se não conseguir converter, assume 0
                            prioridade = 0
                    else:
                        # parts[4] é um evento, não prioridade
                        events_start_index = 4
                
                # Concatena todos os campos de eventos a partir do índice correto
                events_str = ""
                if len(parts) > events_start_index:
                    events_str = ';'.join(parts[events_start_index:])
                
                # Faz o parsing dos eventos (I/O, ML, MU)
                io_events, ml_events, mu_events = parse_events(events_str)
                
                # Cria o TCB (Task Control Block) com todos os parâmetros
                task = TCB(
                    id=task_id,
                    RGB=rgb_color,
                    state=1,              # Estado inicial: 1 (Novo)
                    inicio=ingresso,      # Tempo de chegada da tarefa
                    duracao=duracao,      # Tempo de CPU necessário
                    prio_s=prioridade,    # Prioridade estática
                    io_events=io_events,  # Lista de eventos de I/O
                    ml_events=ml_events,  # Lista de eventos de mutex lock
                    mu_events=mu_events   # Lista de eventos de mutex unlock
                )
                tasks.append(task)
            except (ValueError, IndexError) as e:
                # Em caso de erro no formato, exibe aviso mas continua processando outras linhas
                print(f"Aviso: ignorando linha mal formatada no arquivo de configuração: '{line.strip()}' - Erro: {e}")
                continue
            
    return scheduler_type, quantum, tasks