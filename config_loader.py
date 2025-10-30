"""
Módulo responsável por carregar arquivos de configuração do simulador.
Lê arquivos .txt contendo definições de algoritmo, quantum e tarefas.
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

def parse_io_events(io_string: str) -> List[Tuple[int, int]]:
    """
    Analisa string de eventos de I/O no formato 'IO:tempo-duracao' ou múltiplos separados por ';'.
    
    Args:
        io_string: String contendo eventos de I/O (ex: 'IO:2-1' ou 'IO:2-1;IO:5-2')
    
    Returns:
        Lista de tuplas (tempo_inicio, duracao) para cada evento de I/O
    
    Exemplo:
        >>> parse_io_events('IO:2-1;IO:5-2')
        [(2, 1), (5, 2)]
    """
    events = []
    if not io_string:
        return events
    
    # Divide múltiplos eventos separados por ';'
    parts = io_string.split(';')
    
    for part in parts:
        part = part.strip()
        if part.startswith('IO:'):
            # Remove o prefixo 'IO:' e divide 'tempo-duracao'
            io_data = part[3:].split('-')
            if len(io_data) == 2:
                try:
                    tempo_inicio = int(io_data[0])
                    duracao = int(io_data[1])
                    events.append((tempo_inicio, duracao))
                except ValueError:
                    print(f"Aviso: formato de I/O inválido: '{part}'")
    
    return events

def load_simulation_config(filepath: str) -> Tuple[str, Optional[int], List[TCB]]:
    """
    Carrega a configuração da simulação a partir de um arquivo de texto.
    
    Formato do arquivo:
        - Linha 1: ALGORITMO;QUANTUM (ex: 'FIFO;3' ou 'SRTF;')
        - Linhas seguintes: t<ID>;cor_id;ingresso;duracao;prioridade;[IO:X-Y] (eventos I/O opcionais)
        - Linhas começando com '#' são ignoradas (comentários)
    
    Args:
        filepath: Caminho para o arquivo de configuração
    
    Returns:
        Tupla contendo:
            - scheduler_type (str): Nome do algoritmo (FIFO, SRTF, PRIO, etc.)
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

        # As linhas seguintes definem cada tarefa (formato: t<ID>;cor;ingresso;duracao;prioridade;[IO:X-Y])
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
                prioridade = int(parts[4])
                
                # Processa eventos de I/O se existirem (campo opcional)
                io_events = []
                if len(parts) > 5 and parts[5].strip():
                    io_events = parse_io_events(parts[5].strip())
                
                # Cria o TCB (Task Control Block) com todos os parâmetros
                task = TCB(
                    id=task_id,
                    RGB=rgb_color,
                    state=1,              # Estado inicial: 1 (Novo)
                    inicio=ingresso,      # Tempo de chegada da tarefa
                    duracao=duracao,      # Tempo de CPU necessário
                    prio_s=prioridade,    # Prioridade estática
                    io_events=io_events   # Lista de eventos de I/O
                )
                tasks.append(task)
            except (ValueError, IndexError) as e:
                # Em caso de erro no formato, exibe aviso mas continua processando outras linhas
                print(f"Aviso: ignorando linha mal formatada no arquivo de configuração: '{line.strip()}' - Erro: {e}")
                continue
            
    return scheduler_type, quantum, tasks