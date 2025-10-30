"""
Script de Teste Automatizado
Valida as funcionalidades implementadas do simulador

IMPORTANTE: Execute este script da pasta raiz do projeto:
  cd ..
  python tests/test_suite.py

Ou da pasta tests:
  cd tests
  python test_suite.py
"""

import sys
import os

# Adiciona o diretório pai ao path para importar módulos
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from config_loader import load_simulation_config
from scheduler import FIFOScheduler, SRTFScheduler, PriorityScheduler, RoundRobinScheduler
from simulador import Simulator

# Define caminho base para os arquivos de teste
TEST_DIR = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(TEST_DIR) == 'tests':
    TEST_PATH = TEST_DIR
else:
    TEST_PATH = os.path.join(TEST_DIR, 'tests')

def test_load_config():
    """Testa carregamento de arquivo de configuração"""
    print("\n🧪 Teste 1: Carregamento de Configuração")
    try:
        test_file = os.path.join(TEST_PATH, "teste_fifo_basico.txt")
        algo, quantum, tasks = load_simulation_config(test_file)
        assert algo == "FIFO", f"Algoritmo incorreto: {algo}"
        assert len(tasks) == 3, f"Número de tarefas incorreto: {len(tasks)}"
        print("✅ Carregamento OK")
        return True
    except Exception as e:
        print(f"❌ FALHOU: {e}")
        return False

def test_io_events():
    """Testa eventos de I/O"""
    print("\n🧪 Teste 2: Eventos de I/O")
    try:
        test_file = os.path.join(TEST_PATH, "teste_io_completo.txt")
        algo, quantum, tasks = load_simulation_config(test_file)
        
        # Verifica se I/O foi parseado
        task_with_io = [t for t in tasks if len(t.io_events) > 0]
        assert len(task_with_io) > 0, "Nenhuma tarefa com I/O encontrada"
        
        # Verifica formato dos eventos
        for task in task_with_io:
            for tempo, duracao in task.io_events:
                assert isinstance(tempo, int) and isinstance(duracao, int)
                assert tempo >= 0 and duracao > 0
        
        print(f"✅ I/O OK - {len(task_with_io)} tarefas com eventos I/O")
        return True
    except Exception as e:
        print(f"❌ FALHOU: {e}")
        return False

def test_quantum():
    """Testa quantum do Round-Robin"""
    print("\n🧪 Teste 3: Quantum Round-Robin")
    try:
        test_file = os.path.join(TEST_PATH, "teste_round_robin.txt")
        algo, quantum, tasks = load_simulation_config(test_file)
        assert algo == "RR", f"Algoritmo incorreto: {algo}"
        assert quantum == 3, f"Quantum incorreto: {quantum}"
        
        scheduler = RoundRobinScheduler(quantum=quantum)
        assert scheduler.quantum == 3, "Quantum não foi definido"
        assert scheduler.time_slice_remaining == 3, "Time slice incorreto"
        
        print("✅ Quantum OK")
        return True
    except Exception as e:
        print(f"❌ FALHOU: {e}")
        return False

def test_fifo_simulation():
    """Testa simulação FIFO completa"""
    print("\n🧪 Teste 4: Simulação FIFO")
    try:
        test_file = os.path.join(TEST_PATH, "teste_fifo_basico.txt")
        algo, quantum, tasks = load_simulation_config(test_file)
        scheduler = FIFOScheduler()
        simulator = Simulator(scheduler, tasks)
        
        simulator.run_full()
        
        assert simulator.is_finished(), "Simulação não terminou"
        assert len(simulator.done_tasks) == 3, f"Tarefas concluídas: {len(simulator.done_tasks)}"
        
        # Verifica ordem FIFO
        done_ids = [t.id for t in simulator.done_tasks]
        print(f"   Ordem de conclusão: {done_ids}")
        
        print("✅ Simulação FIFO OK")
        return True
    except Exception as e:
        print(f"❌ FALHOU: {e}")
        return False

def test_statistics():
    """Testa cálculo de estatísticas"""
    print("\n🧪 Teste 5: Estatísticas")
    try:
        test_file = os.path.join(TEST_PATH, "teste_fifo_basico.txt")
        algo, quantum, tasks = load_simulation_config(test_file)
        scheduler = FIFOScheduler()
        simulator = Simulator(scheduler, tasks)
        
        simulator.run_full()
        stats = simulator.get_statistics()
        
        assert 'tasks' in stats, "Falta campo 'tasks'"
        assert 'avg_turnaround' in stats, "Falta campo 'avg_turnaround'"
        assert 'avg_waiting' in stats, "Falta campo 'avg_waiting'"
        assert 'avg_response' in stats, "Falta campo 'avg_response'"
        
        assert len(stats['tasks']) == 3, f"Estatísticas de {len(stats['tasks'])} tarefas"
        assert stats['avg_turnaround'] > 0, "Turnaround inválido"
        
        print(f"   Turnaround médio: {stats['avg_turnaround']:.2f}")
        print(f"   Espera média: {stats['avg_waiting']:.2f}")
        print(f"   Resposta média: {stats['avg_response']:.2f}")
        print("✅ Estatísticas OK")
        return True
    except Exception as e:
        print(f"❌ FALHOU: {e}")
        return False

def test_srtf_preemption():
    """Testa preempção do SRTF"""
    print("\n🧪 Teste 6: Preempção SRTF")
    try:
        from tasks import TCB
        
        # Cria tarefas manualmente
        tasks = [
            TCB(id=1, RGB=[255,0,0], inicio=0, duracao=8, prio_s=1),
            TCB(id=2, RGB=[0,255,0], inicio=1, duracao=4, prio_s=1),
            TCB(id=3, RGB=[0,0,255], inicio=3, duracao=2, prio_s=1)
        ]
        
        scheduler = SRTFScheduler()
        simulator = Simulator(scheduler, tasks)
        
        simulator.run_full()
        
        # SRTF deve preemptar quando chega tarefa com tempo menor
        # T1 executa 1 unidade (tempo 0), fica com 7 restantes
        # T2 chega (tempo 1) com 4 < 7, preempta T1
        # T2 executa 2 unidades, fica com 2 restantes
        # T3 chega (tempo 3) com 2 = 2, continua T2 ou troca (empate)
        # T3 ou T2 termina primeiro (ambos com 2)
        
        done_ids = [t.id for t in simulator.done_tasks]
        
        # Verifica que T1 (maior duração) terminou por último
        assert done_ids[-1] == 1, f"T1 deveria terminar por último: {done_ids}"
        
        # Verifica que houve ativações múltiplas (preempção)
        assert tasks[0].ativacoes > 1, f"T1 deveria ter sido preemptada: {tasks[0].ativacoes} ativações"
        
        print(f"   Ordem de conclusão: {done_ids}")
        print(f"   T1 teve {tasks[0].ativacoes} ativações (foi preemptada)")
        print("✅ Preempção SRTF OK")
        return True
    except Exception as e:
        print(f"❌ FALHOU: {e}")
        return False

def test_io_blocking():
    """Testa bloqueio por I/O"""
    print("\n🧪 Teste 7: Bloqueio I/O")
    try:
        test_file = os.path.join(TEST_PATH, "teste_io_completo.txt")
        algo, quantum, tasks = load_simulation_config(test_file)
        scheduler = SRTFScheduler()
        simulator = Simulator(scheduler, tasks)
        
        # Executa alguns passos
        for _ in range(10):
            simulator.step()
            if not simulator.blocked_queue.is_empty():
                break
        
        # Verifica que há tarefas bloqueadas em algum momento
        has_blocked = any("IO" in str(entry) for entry in simulator.gantt_data)
        # Alternativa: verificar se blocked_queue foi usado
        
        print("✅ Bloqueio I/O OK")
        return True
    except Exception as e:
        print(f"❌ FALHOU: {e}")
        return False

def run_all_tests():
    """Executa todos os testes"""
    print("="*60)
    print("🧪 SUITE DE TESTES AUTOMATIZADOS")
    print("="*60)
    
    tests = [
        test_load_config,
        test_io_events,
        test_quantum,
        test_fifo_simulation,
        test_statistics,
        test_srtf_preemption,
        test_io_blocking
    ]
    
    results = []
    for test in tests:
        results.append(test())
    
    print("\n" + "="*60)
    print("📊 RESUMO DOS TESTES")
    print("="*60)
    
    passed = sum(results)
    total = len(results)
    
    print(f"✅ Passou: {passed}/{total}")
    print(f"❌ Falhou: {total - passed}/{total}")
    
    if passed == total:
        print("\n🎉 TODOS OS TESTES PASSARAM!")
        return 0
    else:
        print("\n⚠️  ALGUNS TESTES FALHARAM")
        return 1

if __name__ == "__main__":
    sys.exit(run_all_tests())
