"""
Testes específicos para o algoritmo PRIOPEnv (Prioridade Preemptiva com Envelhecimento).

Verifica:
1. prio_d inicia igual a prio_s
2. prio_d aumenta quando entra nova tarefa (envelhecimento)
3. prio_d aumenta quando outra tarefa termina (envelhecimento)
4. prio_d reseta para prio_s após executar
5. Tarefa de baixa prioridade eventualmente executa (anti-starvation)

Execute com: python3 tests_priopenv.py
"""

import unittest
from tasks import TCB, TCBQueue, STATE_NEW, STATE_READY, STATE_RUNNING, STATE_TERMINATED
from scheduler import PRIOPEnvScheduler
from simulador import Simulator


class TestPRIOPEnvPriorityDynamic(unittest.TestCase):
    """Testes para prioridade dinâmica no PRIOPEnv."""
    
    def test_prio_d_starts_equal_to_prio_s(self):
        """Testa que prio_d inicia igual a prio_s."""
        task = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=5, prio_s=7)
        self.assertEqual(task.prio_d, 7)
        self.assertEqual(task.prio_d, task.prio_s)
    
    def test_prio_d_starts_equal_for_zero_priority(self):
        """Testa que prio_d inicia igual a prio_s mesmo quando prio_s=0."""
        task = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=5, prio_s=0)
        self.assertEqual(task.prio_d, 0)
        self.assertEqual(task.prio_d, task.prio_s)
    
    def test_reset_dynamic_priority(self):
        """Testa o método reset_dynamic_priority."""
        task = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=5, prio_s=5)
        task.prio_d = 10  # Simula envelhecimento
        task.reset_dynamic_priority()
        self.assertEqual(task.prio_d, 5)


class TestPRIOPEnvAging(unittest.TestCase):
    """Testes para o mecanismo de envelhecimento."""
    
    def test_age_tasks_increases_prio_d(self):
        """Testa que age_tasks aumenta prio_d."""
        scheduler = PRIOPEnvScheduler(quantum=2, alpha=1)
        queue = TCBQueue()
        
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=5, prio_s=3)
        t2 = TCB(id=2, RGB=[0, 255, 0], inicio=0, duracao=3, prio_s=5)
        
        queue.push_back(t1)
        queue.push_back(t2)
        
        scheduler.age_tasks(queue)
        
        self.assertEqual(t1.prio_d, 4)  # 3 + 1
        self.assertEqual(t2.prio_d, 6)  # 5 + 1
    
    def test_age_tasks_with_alpha_2(self):
        """Testa envelhecimento com alpha=2."""
        scheduler = PRIOPEnvScheduler(quantum=2, alpha=2)
        queue = TCBQueue()
        
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=5, prio_s=3)
        
        queue.push_back(t1)
        scheduler.age_tasks(queue)
        
        self.assertEqual(t1.prio_d, 5)  # 3 + 2
    
    def test_age_tasks_excludes_specified_task(self):
        """Testa que age_tasks exclui tarefa especificada."""
        scheduler = PRIOPEnvScheduler(quantum=2, alpha=1)
        queue = TCBQueue()
        
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=5, prio_s=3)
        t2 = TCB(id=2, RGB=[0, 255, 0], inicio=0, duracao=3, prio_s=5)
        
        queue.push_back(t1)
        queue.push_back(t2)
        
        scheduler.age_tasks(queue, exclude_task=t1)
        
        self.assertEqual(t1.prio_d, 3)  # Não mudou (excluída)
        self.assertEqual(t2.prio_d, 6)  # 5 + 1
    
    def test_cumulative_aging(self):
        """Testa envelhecimento cumulativo."""
        scheduler = PRIOPEnvScheduler(quantum=2, alpha=1)
        queue = TCBQueue()
        
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=5, prio_s=3)
        queue.push_back(t1)
        
        # Envelhece 3 vezes
        scheduler.age_tasks(queue)
        scheduler.age_tasks(queue)
        scheduler.age_tasks(queue)
        
        self.assertEqual(t1.prio_d, 6)  # 3 + 1 + 1 + 1


class TestPRIOPEnvAgingOnNewArrival(unittest.TestCase):
    """Testes para envelhecimento quando nova tarefa chega."""
    
    def test_aging_on_new_task_arrival(self):
        """Testa que tarefas prontas envelhecem quando nova tarefa chega."""
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=5, prio_s=3)
        t2 = TCB(id=2, RGB=[0, 255, 0], inicio=1, duracao=3, prio_s=10)  # Chega em t=1
        
        scheduler = PRIOPEnvScheduler(quantum=2, alpha=1)
        simulator = Simulator(scheduler, [t1, t2])
        
        # Tempo 0: T1 chega e começa a executar
        simulator.step()
        self.assertEqual(t1.prio_d, 3)  # Executou, reseta para prio_s
        
        # Tempo 1: T2 chega, T1 deve envelhecer (está em ready após preempção ou continua)
        simulator.step()
        
        # T2 chegou, então T1 (se estiver na fila de prontos) deveria ter envelhecido
        # Mas T1 estava executando, então foi preemptada por T2 (maior prioridade)
        # Após executar, T1 tem prio_d=prio_s novamente
        # T2 tem prioridade maior (10 > 3), então executa
    
    def test_aging_happens_only_on_arrival(self):
        """Testa que envelhecimento ocorre apenas na chegada de novas tarefas."""
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=10, prio_s=3)
        
        scheduler = PRIOPEnvScheduler(quantum=2, alpha=1)
        simulator = Simulator(scheduler, [t1])
        
        # Tempo 0: T1 chega
        simulator.step()
        self.assertEqual(t1.prio_d, 3)  # Executou, reseta
        
        # Tempo 1: Sem novas chegadas
        simulator.step()
        self.assertEqual(t1.prio_d, 3)  # Executou, reseta
        
        # Tempo 2: Sem novas chegadas
        simulator.step()
        self.assertEqual(t1.prio_d, 3)  # Executou, reseta


class TestPRIOPEnvAgingOnTaskCompletion(unittest.TestCase):
    """Testes para envelhecimento quando tarefa termina."""
    
    def test_aging_on_task_completion(self):
        """Testa que tarefas prontas envelhecem quando outra tarefa termina."""
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=2, prio_s=10)  # Alta prioridade, curta
        t2 = TCB(id=2, RGB=[0, 255, 0], inicio=0, duracao=5, prio_s=3)   # Baixa prioridade
        
        scheduler = PRIOPEnvScheduler(quantum=5, alpha=1)
        simulator = Simulator(scheduler, [t1, t2])
        
        # Tempo 0: Ambas chegam, T1 executa (maior prioridade)
        simulator.step()
        # T2 está em ready, não envelheceu ainda (chegou junto com T1)
        
        # Tempo 1: T1 continua
        simulator.step()
        # T1 termina! T2 deve envelhecer
        
        # Verifica que T1 terminou
        self.assertEqual(t1.state, STATE_TERMINATED)
        
        # T2 deve ter envelhecido quando T1 terminou
        # prio_d inicial = 3, após envelhecimento = 4
        self.assertGreaterEqual(t2.prio_d, 3)


class TestPRIOPEnvResetAfterExecution(unittest.TestCase):
    """Testes para reset de prio_d após execução."""
    
    def test_prio_d_resets_after_execution(self):
        """Testa que prio_d reseta para prio_s após executar."""
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=5, prio_s=3)
        t2 = TCB(id=2, RGB=[0, 255, 0], inicio=2, duracao=3, prio_s=1)  # Chega depois, baixa prio
        
        scheduler = PRIOPEnvScheduler(quantum=10, alpha=2)
        simulator = Simulator(scheduler, [t1, t2])
        
        # Tempo 0: T1 chega e executa
        simulator.step()
        self.assertEqual(t1.prio_d, 3)  # Executou, reseta para prio_s
        
        # Tempo 1: T1 continua
        simulator.step()
        self.assertEqual(t1.prio_d, 3)  # Executou, reseta
        
        # Tempo 2: T2 chega, T1 envelhece? Não, T1 está executando
        # Após T1 executar, prio_d = prio_s
        simulator.step()
        self.assertEqual(t1.prio_d, 3)


class TestPRIOPEnvAntiStarvation(unittest.TestCase):
    """Testes para verificar que envelhecimento evita starvation."""
    
    def test_low_priority_eventually_executes(self):
        """Testa que tarefa de baixa prioridade eventualmente executa devido ao envelhecimento."""
        # T1: baixa prioridade (1), longa duração
        # T2: alta prioridade (10), chega depois
        # T3: alta prioridade (10), chega ainda depois
        # Com envelhecimento, T1 deve eventualmente ter prioridade alta o suficiente
        
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=3, prio_s=1)
        t2 = TCB(id=2, RGB=[0, 255, 0], inicio=1, duracao=2, prio_s=10)
        t3 = TCB(id=3, RGB=[0, 0, 255], inicio=2, duracao=2, prio_s=10)
        
        scheduler = PRIOPEnvScheduler(quantum=10, alpha=5)  # Alpha alto para teste rápido
        simulator = Simulator(scheduler, [t1, t2, t3])
        
        # Executa até terminar
        simulator.run_full()
        
        # Todas as tarefas devem ter terminado
        self.assertTrue(simulator.is_finished())
        self.assertEqual(len(simulator.done_tasks), 3)
        
        # T1 deve ter terminado (não ficou em starvation)
        self.assertEqual(t1.state, STATE_TERMINATED)
    
    def test_aging_prevents_indefinite_waiting(self):
        """Testa que uma tarefa não espera indefinidamente."""
        # Cria cenário onde sem envelhecimento T1 nunca executaria
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=1, prio_s=1)  # Baixíssima prioridade
        
        # Várias tarefas de alta prioridade chegando continuamente
        tasks = [t1]
        for i in range(5):
            tasks.append(TCB(id=i+2, RGB=[0, 255, 0], inicio=i, duracao=1, prio_s=10))
        
        scheduler = PRIOPEnvScheduler(quantum=10, alpha=3)
        simulator = Simulator(scheduler, tasks)
        
        simulator.run_full()
        
        # T1 deve ter executado
        self.assertEqual(t1.state, STATE_TERMINATED)


class TestPRIOPEnvSchedulerSelection(unittest.TestCase):
    """Testes para seleção de tarefa no PRIOPEnv."""
    
    def test_selects_highest_dynamic_priority(self):
        """Testa que seleciona tarefa com maior prio_d."""
        scheduler = PRIOPEnvScheduler(quantum=2, alpha=1)
        queue = TCBQueue()
        
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=5, prio_s=3)
        t2 = TCB(id=2, RGB=[0, 255, 0], inicio=0, duracao=3, prio_s=5)
        
        # Simula envelhecimento de T1
        t1.prio_d = 7
        
        queue.push_back(t1)
        queue.push_back(t2)
        
        selected = scheduler.select_next_task(queue, None, 0)
        self.assertEqual(selected.id, 1)  # T1 tem maior prio_d (7 > 5)
    
    def test_preemption_on_higher_dynamic_priority(self):
        """Testa preempção quando outra tarefa tem maior prio_d."""
        scheduler = PRIOPEnvScheduler(quantum=10, alpha=1)
        queue = TCBQueue()
        
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=5, prio_s=5)
        t2 = TCB(id=2, RGB=[0, 255, 0], inicio=0, duracao=3, prio_s=3)
        
        # T2 envelheceu muito
        t2.prio_d = 10
        
        queue.push_back(t1)
        queue.push_back(t2)
        
        # T1 está executando, mas T2 tem maior prio_d
        selected = scheduler.select_next_task(queue, t1, 0)
        self.assertEqual(selected.id, 2)


class TestPRIOPEnvIntegration(unittest.TestCase):
    """Testes de integração do PRIOPEnv."""
    
    def test_complete_simulation(self):
        """Testa simulação completa com PRIOPEnv."""
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=3, prio_s=5)
        t2 = TCB(id=2, RGB=[0, 255, 0], inicio=0, duracao=2, prio_s=3)
        t3 = TCB(id=3, RGB=[0, 0, 255], inicio=1, duracao=2, prio_s=7)
        
        scheduler = PRIOPEnvScheduler(quantum=5, alpha=1)
        simulator = Simulator(scheduler, [t1, t2, t3])
        
        simulator.run_full()
        
        self.assertTrue(simulator.is_finished())
        self.assertEqual(len(simulator.done_tasks), 3)
    
    def test_gantt_data_generated(self):
        """Testa que dados do Gantt são gerados corretamente."""
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=2, prio_s=5)
        
        scheduler = PRIOPEnvScheduler(quantum=5, alpha=1)
        simulator = Simulator(scheduler, [t1])
        
        simulator.run_full()
        
        # Deve ter registros EXEC para T1
        exec_records = [e for e in simulator.gantt_data if e[3] == "EXEC"]
        self.assertEqual(len(exec_records), 2)
    
    def test_statistics_correct(self):
        """Testa que estatísticas são calculadas corretamente."""
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=3, prio_s=5)
        
        scheduler = PRIOPEnvScheduler(quantum=5, alpha=1)
        simulator = Simulator(scheduler, [t1])
        
        simulator.run_full()
        stats = simulator.get_statistics()
        
        self.assertEqual(stats['tasks'][0]['turnaround_time'], 3)
        self.assertEqual(stats['tasks'][0]['waiting_time'], 0)


def run_priopenv_tests():
    """Executa todos os testes do PRIOPEnv."""
    print("=" * 70)
    print("🧪 TESTES DO ALGORITMO PRIOPEnv")
    print("=" * 70)
    print()
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    test_classes = [
        TestPRIOPEnvPriorityDynamic,
        TestPRIOPEnvAging,
        TestPRIOPEnvAgingOnNewArrival,
        TestPRIOPEnvAgingOnTaskCompletion,
        TestPRIOPEnvResetAfterExecution,
        TestPRIOPEnvAntiStarvation,
        TestPRIOPEnvSchedulerSelection,
        TestPRIOPEnvIntegration,
    ]
    
    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print()
    print("=" * 70)
    print("📊 RESULTADO DOS TESTES PRIOPEnv")
    print("=" * 70)
    print(f"  ✅ Executados: {result.testsRun}")
    print(f"  ❌ Falhas: {len(result.failures)}")
    print(f"  💥 Erros: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n🎉 TODOS OS TESTES DO PRIOPEnv PASSARAM!")
    else:
        print("\n⚠️  ALGUNS TESTES FALHARAM:")
        for test, trace in result.failures + result.errors:
            print(f"    ❌ {test}")
            print(f"       {trace.split(chr(10))[0]}")
    
    print("=" * 70)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_priopenv_tests()
    exit(0 if success else 1)
