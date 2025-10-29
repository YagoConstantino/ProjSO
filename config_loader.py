from tasks import TCB
from typing import List, Tuple, Optional

COLOR_MAP = {
    "0": [255, 0, 0],
    "1": [0, 255, 0],
    "2": [0, 0, 255],
    "3": [255, 255, 0],
    "4": [0, 255, 255],
    "5": [255, 0, 255],
    "6": [125,22,123]
}

def load_simulation_config(filepath: str) -> Tuple[str, Optional[int], List[TCB]]:
    tasks = []
    scheduler_type = ""
    quantum = None

    with open(filepath, 'r') as f:
        # A primeira linha define o algoritmo e o quantum.
        first_line = f.readline().strip().split(';')
        scheduler_type = first_line[0].strip().upper()
        if len(first_line) > 1 and first_line[1].strip():
            quantum = int(first_line[1].strip())

        # As linhas seguintes definem cada tarefa.
        for line in f:
            try:
                if not line.strip() or line.strip().startswith('#'):
                    continue
                
                parts = line.strip().split(';')
                
                task_id_str = parts[0].strip().lower().replace('t', '')
                task_id = int(task_id_str)
                
                color_id = parts[1].strip()
                rgb_color = COLOR_MAP.get(color_id, [128, 128, 128])

                ingresso = int(parts[2])
                duracao = int(parts[3])
                prioridade = int(parts[4])
                
                task = TCB(
                    id=task_id,
                    RGB=rgb_color,
                    state=1,
                    inicio=ingresso,
                    duracao=duracao,
                    prio_s=prioridade
                )
                tasks.append(task)
            except (ValueError, IndexError):
                print(f"Aviso: ignorando linha mal formatada no arquivo de configuração: '{line.strip()}'")
                continue
            
    return scheduler_type, quantum, tasks