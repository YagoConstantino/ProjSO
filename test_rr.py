"""Script para testar o algoritmo Round-Robin"""

from config_loader import load_simulation_config
from scheduler import RoundRobinScheduler
from simulador import Simulator

# Carrega o teste Round-Robin
algo, quantum, tasks = load_simulation_config('tests/teste_round_robin.txt')

print(f"Algoritmo: {algo}")
print(f"Quantum: {quantum}")
print(f"Tarefas: {len(tasks)}")
for t in tasks:
    print(f"  - {t.id}: duração={t.duracao}, chegada={t.inicio}")

# Cria o escalonador e simulador
scheduler = RoundRobinScheduler(quantum=quantum)
sim = Simulator(scheduler, tasks)

# Executa a simulação
print("\nExecutando simulação...\n")
sim.run_full()

# Mostra o Gantt (primeiros 30 ciclos)
print("Gantt (primeiros 30 ciclos):")
for i, (time, task_id, rgb, state) in enumerate(sim.gantt_data[:30]):
    print(f"  t={time}: {task_id} ({state})")

# Mostra estatísticas
stats = sim.get_statistics()
print(f"\n📊 Estatísticas:")
print(f"  Turnaround médio: {stats['avg_turnaround']:.2f}")
print(f"  Espera médio: {stats['avg_waiting']:.2f}")
print(f"  Resposta médio: {stats['avg_response']:.2f}")

print("\nPor tarefa:")
for task_stat in stats['tasks']:
    print(f"  {task_stat['id']}: Turnaround={task_stat['turnaround']}, "
          f"Espera={task_stat['waiting']}, Ativações={task_stat['activations']}")
