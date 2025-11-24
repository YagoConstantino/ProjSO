"""Script para debugar o algoritmo Round-Robin"""

from config_loader import load_simulation_config
from scheduler import RoundRobinScheduler
from simulador import Simulator

# Carrega o teste Round-Robin
algo, quantum, tasks = load_simulation_config('tests/teste_round_robin.txt')

print(f"Algoritmo: {algo}, Quantum: {quantum}\n")

# Cria o escalonador e simulador
scheduler = RoundRobinScheduler(quantum=quantum)
sim = Simulator(scheduler, tasks)

# Executa passo a passo e mostra o estado do quantum
for i in range(20):
    print(f"=== Passo {i} (t={sim.time}) ===")
    print(f"  Quantum restante: {scheduler.time_slice_remaining}")
    print(f"  Tarefa atual: {sim.current_task.id if sim.current_task else 'None'}")
    print(f"  Fila: {[t.id for t in sim.ready_queue]}")
    
    sim.step()
    
    if sim.is_finished():
        print("\nSimulação finalizada!")
        break
