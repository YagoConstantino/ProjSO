"""
Módulo responsável por carregar arquivos de configuração do simulador.
Lê arquivos .txt contendo definições de algoritmo, quantum e tarefas.

Formato do arquivo de configuração:
    - Linha 1: ALGORITMO;QUANTUM (ex: 'FIFO;3' ou 'SRTF;')
    - Linhas seguintes: t<ID>;cor_hex;ingresso;duracao;prioridade;[eventos]
    - Cor em formato hexadecimal: #RRGGBB ou RRGGBB (ex: #FF0000 ou ff0000)
    - Eventos podem ser: IO:tempo-duracao, ML:tempo (mutex lock), MU:tempo (mutex unlock)
    - Múltiplos eventos são separados por ';'
    - Linhas começando com '#' são ignoradas (comentários)
"""

from tasks import TCB
from typing import List, Tuple, Optional, Dict


def hex_to_rgb(hex_color: str) -> List[int]:
    """
    Converte cor hexadecimal para RGB.
    
    Args:
        hex_color: Cor em formato hexadecimal (#RRGGBB ou RRGGBB)
    
    Returns:
        Lista [R, G, B] com valores de 0 a 255
    
    Exemplo:
        >>> hex_to_rgb('#FF0000')
        [255, 0, 0]
        >>> hex_to_rgb('00ff00')
        [0, 255, 0]
    
    Raises:
        ValueError: Se o formato for inválido
    """
    # Remove '#' se presente
    hex_color = hex_color.strip().lstrip('#')
    
    # Valida comprimento (deve ser 6 caracteres)
    if len(hex_color) != 6:
        raise ValueError(f"Formato hexadecimal inválido: '{hex_color}'. Use RRGGBB ou #RRGGBB")
    
    try:
        # Converte cada par de caracteres hex para decimal
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return [r, g, b]
    except ValueError:
        raise ValueError(f"Formato hexadecimal inválido: '{hex_color}'. Use apenas caracteres 0-9 e A-F")


def parse_events(events_string: str) -> Tuple[List[Tuple[int, int]], List[Tuple[int, int]], List[Tuple[int, int]]]:
    """
    Analisa string de eventos e extrai I/O, mutex lock e mutex unlock.
    
    Args:
        events_string: String contendo eventos separados por ';'
            - IO:tempo-duracao (ex: 'IO:2-1')
            - MLxx:tempo (ex: 'ML01:1') - Mutex Lock do mutex xx no tempo
            - MUxx:tempo (ex: 'MU01:3') - Mutex Unlock do mutex xx no tempo
            - ML:tempo (formato simplificado para mutex 0)
            - MU:tempo (formato simplificado para mutex 0)
    
    Returns:
        Tupla contendo:
            - io_events: Lista de tuplas (tempo_inicio, duracao) para eventos I/O
            - ml_events: Lista de tuplas (mutex_id, tempo) para mutex lock
            - mu_events: Lista de tuplas (mutex_id, tempo) para mutex unlock
    """
    io_events = []
    ml_events = []  # Agora é lista de tuplas (mutex_id, tempo)
    mu_events = []  # Agora é lista de tuplas (mutex_id, tempo)
    
    if not events_string:
        return io_events, ml_events, mu_events
    
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
        
        elif part.startswith('ML'):
            # Evento de Mutex Lock: formato 'MLxx:tempo' ou 'ML:tempo'
            try:
                if ':' in part:
                    prefix, tempo_str = part.split(':', 1)
                    tempo = int(tempo_str)
                    # Extrai número do mutex (ex: ML01 -> 1, ML -> 0)
                    mutex_id_str = prefix[2:]  # Remove 'ML'
                    mutex_id = int(mutex_id_str) if mutex_id_str else 0
                    ml_events.append((mutex_id, tempo))
            except ValueError:
                print(f"Aviso: formato de ML inválido: '{part}'")
        
        elif part.startswith('MU'):
            # Evento de Mutex Unlock: formato 'MUxx:tempo' ou 'MU:tempo'
            try:
                if ':' in part:
                    prefix, tempo_str = part.split(':', 1)
                    tempo = int(tempo_str)
                    # Extrai número do mutex (ex: MU01 -> 1, MU -> 0)
                    mutex_id_str = prefix[2:]  # Remove 'MU'
                    mutex_id = int(mutex_id_str) if mutex_id_str else 0
                    mu_events.append((mutex_id, tempo))
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

def load_simulation_config(filepath: str) -> Tuple[str, Optional[int], Optional[int], List[TCB]]:
    """
    Carrega a configuração da simulação a partir de um arquivo de texto.
    
    Formato do arquivo:
        - Linha 1: ALGORITMO;QUANTUM;ALPHA (ex: 'PRIOPEnv;5;1' ou 'FIFO;3' ou 'SRTF;')
        - Linhas seguintes: t<ID>;cor_hex;ingresso;duracao;prioridade;[eventos]
    
    Args:
        filepath: Caminho para o arquivo de configuração
    
    Returns:
        Tupla contendo:
            - scheduler_type (str): Nome do algoritmo
            - quantum (Optional[int]): Valor do quantum ou None
            - alpha (Optional[int]): Valor do alpha para envelhecimento ou None
            - tasks (List[TCB]): Lista de tarefas carregadas
    """
    tasks = []
    scheduler_type = ""
    quantum = None
    alpha = None

    with open(filepath, 'r') as f:
        first_line = f.readline().strip().split(';')
        scheduler_type = first_line[0].strip().upper()
        
        if len(first_line) > 1 and first_line[1].strip():
            quantum = int(first_line[1].strip())
        
        if len(first_line) > 2 and first_line[2].strip():
            alpha = int(first_line[2].strip())

        for line in f:
            try:
                if not line.strip() or line.strip().startswith('#'):
                    continue
                
                parts = line.strip().split(';')
                
                task_id_str = parts[0].strip().lower().replace('t', '')
                task_id = int(task_id_str)
                
                cor_hex = parts[1].strip()
                try:
                    rgb_color = hex_to_rgb(cor_hex)
                except ValueError as ve:
                    print(f"Aviso: {ve}. Usando cinza padrão para tarefa {task_id}.")
                    rgb_color = [128, 128, 128]

                ingresso = int(parts[2])
                duracao = int(parts[3])
                
                prioridade = 0
                events_start_index = 5
                
                if len(parts) > 4:
                    part4 = parts[4].strip()
                    if part4 and not any(part4.startswith(prefix) for prefix in ['IO:', 'ML', 'MU']):
                        try:
                            prioridade = int(part4)
                        except ValueError:
                            prioridade = 0
                    else:
                        events_start_index = 4
                
                events_str = ""
                if len(parts) > events_start_index:
                    events_str = ';'.join(parts[events_start_index:])
                
                io_events, ml_events_raw, mu_events_raw = parse_events(events_str)
                
                # Converte para formato usado internamente (apenas tempos, ignora mutex_id por enquanto)
                # TODO: Suportar múltiplos mutexes
                ml_events = [tempo for (mutex_id, tempo) in ml_events_raw]
                mu_events = [tempo for (mutex_id, tempo) in mu_events_raw]
                
                task = TCB(
                    id=task_id,
                    RGB=rgb_color,
                    state=1,
                    inicio=ingresso,
                    duracao=duracao,
                    prio_s=prioridade,
                    prio_d=prioridade,
                    io_events=io_events,
                    ml_events=ml_events,
                    mu_events=mu_events
                )
                tasks.append(task)
            except (ValueError, IndexError) as e:
                print(f"Aviso: ignorando linha mal formatada: '{line.strip()}' - Erro: {e}")
                continue
            
    return scheduler_type, quantum, alpha, tasks