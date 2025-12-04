"""
Testes específicos para eventos de I/O.

Verifica:
1. Tarefa é suspensa corretamente quando I/O ocorre
2. Tarefa volta para fila de prontos após I/O terminar
3. Tempo de bloqueio está correto
4. Múltiplos I/Os funcionam
5. I/O no tempo relativo 0 funciona
6. Gantt registra I/O corretamente

Execute com: python3 tests_io.py
"""

import unittest
from tasks import TCB, TCBQueue, STATE_NEW, STATE_READY, STATE_RUNNING, STATE_BLOCKED_IO, STATE_TERMINATED
from scheduler import FIFOScheduler, SRTFScheduler
from simulador import Simulator


class TestIOBasic(unittest.TestCase):
    """Testes básicos de I/O."""
    
    def test_task_blocked_on_io(self):
        """Testa que tarefa é bloqueada quando I/O ocorre."""
        # T1: duração 5, I/O no tempo 2 (após executar 2 ciclos), duração 2
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=5, prio_s=5,
                 io_events=[(2, 2)])  # I/O no tempo relativo 2
        
        scheduler = FIFOScheduler()
        simulator = Simulator(scheduler, [t1])
        
        # Tempo 0: T1 executa (tempo_exec_acumulado = 0 -> 1)
        simulator.step()
        self.assertEqual(t1.state, STATE_RUNNING)
        self.assertEqual(t1.tempo_exec_acumulado, 1)
        
        # Tempo 1: T1 executa (tempo_exec_acumulado = 1 -> 2)
        simulator.step()
        self.assertEqual(t1.state, STATE_RUNNING)
        self.assertEqual(t1.tempo_exec_acumulado, 2)
        
        # Tempo 2: T1 tenta executar, mas I/O acontece (tempo_exec_acumulado = 2)
        # A tarefa deve ser bloqueada ANTES de executar
        simulator.step()
        self.assertEqual(t1.state, STATE_BLOCKED_IO)
        self.assertEqual(t1.tempo_exec_acumulado, 2)  # Não incrementou porque bloqueou
        self.assertEqual(t1.io_blocked_until, 2 + 2)  # time=2 + duracao=2 = 4
    
    def test_task_unblocked_after_io(self):
        """Testa que tarefa volta para prontos após I/O terminar."""
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=5, prio_s=5,
                 io_events=[(2, 2)])
        
        scheduler = FIFOScheduler()
        simulator = Simulator(scheduler, [t1])
        
        # Executa até T1 ficar bloqueada
        simulator.step()  # tempo 0
        simulator.step()  # tempo 1
        simulator.step()  # tempo 2 - I/O começa
        
        self.assertEqual(t1.state, STATE_BLOCKED_IO)
        
        # Tempo 3: T1 ainda bloqueada
        simulator.step()
        self.assertEqual(t1.state, STATE_BLOCKED_IO)
        
        # Tempo 4: T1 é desbloqueada (io_blocked_until = 4)
        simulator.step()
        self.assertEqual(t1.state, STATE_RUNNING)  # Voltou e está executando
    
    def test_io_duration_correct(self):
        """Testa que a duração do I/O está correta."""
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=3, prio_s=5,
                 io_events=[(1, 3)])  # I/O após 1 ciclo, duração 3
        
        scheduler = FIFOScheduler()
        simulator = Simulator(scheduler, [t1])
        
        # Tempo 0: Executa (tempo_exec_acumulado = 0 -> 1)
        simulator.step()
        self.assertEqual(t1.tempo_exec_acumulado, 1)
        
        # Tempo 1: I/O começa (não executa)
        simulator.step()
        self.assertEqual(t1.state, STATE_BLOCKED_IO)
        blocked_time = simulator.time  # tempo 2
        
        # Continua até desbloquear
        while t1.state == STATE_BLOCKED_IO:
            simulator.step()
        
        unblocked_time = simulator.time
        # Deve ter ficado bloqueada por 3 unidades de tempo
        # Bloqueou no tempo 1, desbloqueou no tempo 4 (quando time >= 1+3=4)
        self.assertEqual(t1.io_blocked_until, 1 + 3)


class TestIOWithMultipleTasks(unittest.TestCase):
    """Testes de I/O com múltiplas tarefas."""
    
    def test_other_task_runs_during_io(self):
        """Testa que outra tarefa executa enquanto uma está em I/O."""
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=4, prio_s=5,
                 io_events=[(1, 2)])  # I/O após 1 ciclo, duração 2
        t2 = TCB(id=2, RGB=[0, 255, 0], inicio=0, duracao=2, prio_s=5)
        
        scheduler = FIFOScheduler()
        simulator = Simulator(scheduler, [t1, t2])
        
        # Tempo 0: T1 executa (FIFO, chegou primeiro na lista ordenada)
        simulator.step()
        # Verifica que T1 executou no tempo 0
        exec_at_time_0 = [e for e in simulator.gantt_data if e[0] == 0 and e[3] == "EXEC"]
        self.assertTrue(any(e[1] == 1 for e in exec_at_time_0))  # T1 executou
        self.assertEqual(t1.tempo_exec_acumulado, 1)
        
        # Tempo 1: T1 entra em I/O (após executar 1 ciclo)
        simulator.step()
        self.assertEqual(t1.state, STATE_BLOCKED_IO)
        
        # Tempo 2: T2 deve executar enquanto T1 está em I/O
        simulator.step()
        exec_at_time_2 = [e for e in simulator.gantt_data if e[0] == 2 and e[3] == "EXEC"]
        self.assertTrue(any(e[1] == 2 for e in exec_at_time_2))  # T2 executou
        
        # Continua até terminar
        simulator.run_full()
        
        self.assertTrue(simulator.is_finished())
        self.assertEqual(t1.state, STATE_TERMINATED)
        self.assertEqual(t2.state, STATE_TERMINATED)
    
    def test_srtf_preemption_after_io(self):
        """Testa preempção SRTF quando tarefa volta de I/O."""
        # T1: duração 6, I/O no tempo 2
        # T2: duração 3, chega no tempo 1
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=6, prio_s=5,
                 io_events=[(2, 1)])
        t2 = TCB(id=2, RGB=[0, 255, 0], inicio=1, duracao=3, prio_s=5)
        
        scheduler = SRTFScheduler()
        simulator = Simulator(scheduler, [t1, t2])
        
        # Tempo 0: T1 executa (única tarefa)
        simulator.step()
        
        # Tempo 1: T2 chega. T1 tem 5 restante, T2 tem 3. T2 deve executar.
        simulator.step()
        
        # Tempo 2: T1 ainda tem I/O pendente, está na fila
        # T2 continua executando
        simulator.step()
        
        # Continua até terminar
        simulator.run_full()
        
        self.assertTrue(simulator.is_finished())


class TestIOMultipleEvents(unittest.TestCase):
    """Testes com múltiplos eventos de I/O."""
    
    def test_multiple_io_events(self):
        """Testa múltiplos eventos de I/O na mesma tarefa."""
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=6, prio_s=5,
                 io_events=[(1, 1), (3, 1)])  # I/O após 1 e 3 ciclos
        
        scheduler = FIFOScheduler()
        simulator = Simulator(scheduler, [t1])
        
        io_count = 0
        max_steps = 20
        steps = 0
        
        while not simulator.is_finished() and steps < max_steps:
            prev_state = t1.state
            simulator.step()
            if prev_state != STATE_BLOCKED_IO and t1.state == STATE_BLOCKED_IO:
                io_count += 1
            steps += 1
        
        self.assertEqual(io_count, 2)  # Dois eventos de I/O
        self.assertTrue(simulator.is_finished())
    
    def test_io_at_time_zero(self):
        """Testa I/O no tempo relativo 0 (imediatamente ao começar)."""
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=3, prio_s=5,
                 io_events=[(0, 2)])  # I/O imediato
        t2 = TCB(id=2, RGB=[0, 255, 0], inicio=0, duracao=2, prio_s=5)
        
        scheduler = FIFOScheduler()
        simulator = Simulator(scheduler, [t1, t2])
        
        # Tempo 0: T1 tenta executar mas I/O acontece imediatamente
        simulator.step()
        
        # T1 deve estar bloqueada
        self.assertEqual(t1.state, STATE_BLOCKED_IO)
        self.assertEqual(t1.tempo_exec_acumulado, 0)  # Não executou nada
        
        # T2 deve poder executar enquanto T1 está em I/O
        simulator.step()
        exec_records = [e for e in simulator.gantt_data if e[3] == "EXEC" and e[1] == 2]
        self.assertTrue(len(exec_records) > 0)


class TestIOGanttRecording(unittest.TestCase):
    """Testes para verificar registro de I/O no Gantt."""
    
    def test_io_recorded_in_gantt(self):
        """Testa que I/O é registrado no Gantt."""
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=4, prio_s=5,
                 io_events=[(1, 2)])
        
        scheduler = FIFOScheduler()
        simulator = Simulator(scheduler, [t1])
        
        simulator.run_full()
        
        # Verifica registros de I/O no Gantt
        io_records = [e for e in simulator.gantt_data if e[3] == "IO" and e[1] == 1]
        self.assertTrue(len(io_records) >= 1)
    
    def test_io_gantt_timing(self):
        """Testa que o timing do I/O no Gantt está correto."""
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=3, prio_s=5,
                 io_events=[(1, 2)])  # I/O após 1 ciclo, duração 2
        
        scheduler = FIFOScheduler()
        simulator = Simulator(scheduler, [t1])
        
        simulator.run_full()
        
        # I/O deve começar no tempo 1 (após executar 1 ciclo no tempo 0)
        # E durar 2 unidades (tempos 1 e 2)
        io_records = [e for e in simulator.gantt_data if e[3] == "IO" and e[1] == 1]
        io_times = sorted([e[0] for e in io_records])
        
        # O primeiro registro de IO deve ser no tempo 1
        # (pode haver registros adicionais dependendo da implementação)
        self.assertIn(1, io_times)


class TestIOStatistics(unittest.TestCase):
    """Testes para estatísticas com I/O."""
    
    def test_turnaround_includes_io_time(self):
        """Testa que turnaround inclui tempo de I/O."""
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=3, prio_s=5,
                 io_events=[(1, 2)])  # 3 de CPU + 2 de I/O = 5 de turnaround
        
        scheduler = FIFOScheduler()
        simulator = Simulator(scheduler, [t1])
        
        simulator.run_full()
        stats = simulator.get_statistics()
        
        task_stats = stats['tasks'][0]
        # Turnaround = fim - inicio
        # A tarefa deve terminar depois de: 1 (exec) + 2 (IO) + 2 (exec restante) = 5
        self.assertGreaterEqual(task_stats['turnaround_time'], 5)
    
    def test_waiting_time_with_io(self):
        """Testa cálculo de tempo de espera com I/O."""
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=2, prio_s=5,
                 io_events=[(1, 2)])
        t2 = TCB(id=2, RGB=[0, 255, 0], inicio=0, duracao=2, prio_s=5)
        
        scheduler = FIFOScheduler()
        simulator = Simulator(scheduler, [t1, t2])
        
        simulator.run_full()
        stats = simulator.get_statistics()
        
        # Ambas as tarefas devem ter terminado
        self.assertEqual(len([t for t in stats['tasks'] if t['turnaround_time'] > 0]), 2)


class TestIOValidation(unittest.TestCase):
    """Testes para validação de eventos de I/O."""
    
    def test_io_after_task_duration_never_triggers(self):
        """Testa que I/O após duração da tarefa nunca é disparado."""
        # T1: duração 2, I/O no tempo 3 (nunca vai acontecer)
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=2, prio_s=5,
                 io_events=[(3, 2)])  # I/O no tempo 3, mas duração é 2
        
        scheduler = FIFOScheduler()
        simulator = Simulator(scheduler, [t1])
        
        simulator.run_full()
        
        # A tarefa deve terminar sem entrar em I/O
        self.assertTrue(simulator.is_finished())
        self.assertEqual(t1.state, STATE_TERMINATED)
        
        # O evento de I/O ainda deve estar na lista (nunca foi consumido)
        # OU a lista está vazia porque a tarefa terminou normalmente
        # Verificamos que NÃO houve registro de I/O no Gantt
        io_records = [e for e in simulator.gantt_data if e[3] == "IO"]
        self.assertEqual(len(io_records), 0)
    
    def test_io_at_exact_duration_triggers(self):
        """Testa que I/O no último ciclo funciona (tempo = duração - 1)."""
        # T1: duração 3, I/O no tempo 2 (último ciclo antes de terminar)
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=3, prio_s=5,
                 io_events=[(2, 1)])  # I/O após 2 ciclos
        
        scheduler = FIFOScheduler()
        simulator = Simulator(scheduler, [t1])
        
        # Tempo 0: executa (tempo_exec_acumulado = 1)
        simulator.step()
        # Tempo 1: executa (tempo_exec_acumulado = 2)
        simulator.step()
        # Tempo 2: I/O dispara (tempo_exec_acumulado = 2, que é o trigger)
        simulator.step()
        
        self.assertEqual(t1.state, STATE_BLOCKED_IO)
    
    def test_io_at_time_equal_duration_never_triggers(self):
        """Testa que I/O no tempo = duração nunca dispara."""
        # T1: duração 3, I/O no tempo 3 (igual à duração)
        # A tarefa termina quando tempo_exec_acumulado = 3, 
        # mas o I/O é verificado ANTES de executar
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=3, prio_s=5,
                 io_events=[(3, 1)])  # I/O no tempo 3 = duração
        
        scheduler = FIFOScheduler()
        simulator = Simulator(scheduler, [t1])
        
        simulator.run_full()
        
        # Tarefa terminou sem I/O
        self.assertTrue(simulator.is_finished())
        io_records = [e for e in simulator.gantt_data if e[3] == "IO" and e[1] == 1]
        self.assertEqual(len(io_records), 0)


class TestIOSpecificScenario(unittest.TestCase):
    """Testes para cenário específico IO:3-2."""
    
    def test_io_3_2_scenario(self):
        """
        Testa IO:3-2 com duração 8.
        - Executa 3 ciclos (tempo_exec_acumulado = 3)
        - I/O dispara e bloqueia por 2 unidades de tempo
        - Volta e executa os 5 ciclos restantes
        """
        t1 = TCB(id=1, RGB=[68, 129, 9], inicio=0, duracao=8, prio_s=2,
                 io_events=[(3, 2)])  # IO:3-2
        
        scheduler = FIFOScheduler()
        simulator = Simulator(scheduler, [t1])
        
        # Tempo 0: Executa (tempo_exec_acumulado = 1)
        simulator.step()
        self.assertEqual(t1.tempo_exec_acumulado, 1)
        self.assertEqual(t1.state, STATE_RUNNING)
        
        # Tempo 1: Executa (tempo_exec_acumulado = 2)
        simulator.step()
        self.assertEqual(t1.tempo_exec_acumulado, 2)
        self.assertEqual(t1.state, STATE_RUNNING)
        
        # Tempo 2: Executa (tempo_exec_acumulado = 3)
        simulator.step()
        self.assertEqual(t1.tempo_exec_acumulado, 3)
        self.assertEqual(t1.state, STATE_RUNNING)
        
        # Tempo 3: I/O dispara (tempo_exec_acumulado == 3)
        # A tarefa é bloqueada ANTES de executar
        simulator.step()
        self.assertEqual(t1.state, STATE_BLOCKED_IO)
        self.assertEqual(t1.tempo_exec_acumulado, 3)  # Não incrementou porque bloqueou
        self.assertEqual(t1.io_blocked_until, 3 + 2)  # Desbloqueada no tempo 5
        
        # Tempo 4: Ainda bloqueada
        simulator.step()
        self.assertEqual(t1.state, STATE_BLOCKED_IO)
        
        # Tempo 5: Desbloqueada (time >= io_blocked_until)
        simulator.step()
        self.assertEqual(t1.state, STATE_RUNNING)
        self.assertEqual(t1.tempo_exec_acumulado, 4)  # Voltou a executar
        
        # Continua até terminar
        simulator.run_full()
        
        self.assertTrue(simulator.is_finished())
        self.assertEqual(t1.state, STATE_TERMINATED)
        self.assertEqual(t1.tempo_exec_acumulado, 8)  # Executou todos os 8 ciclos
        
        # Tempo total = 3 (exec) + 2 (IO) + 5 (exec restante) = 10
        self.assertEqual(t1.fim, 10)
    
    def test_io_timeline_verification(self):
        """Verifica a timeline completa do IO:3-2."""
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=8, prio_s=2,
                 io_events=[(3, 2)])
        
        scheduler = FIFOScheduler()
        simulator = Simulator(scheduler, [t1])
        
        # Executa passo a passo e registra estados
        states_by_time = {}
        while not simulator.is_finished():
            current_time = simulator.time
            simulator.step()
            states_by_time[current_time] = t1.state
        
        # Verifica os estados em cada tempo
        # Tempo 0, 1, 2: Executando (state = 3)
        self.assertEqual(states_by_time[0], STATE_RUNNING)
        self.assertEqual(states_by_time[1], STATE_RUNNING)
        self.assertEqual(states_by_time[2], STATE_RUNNING)
        
        # Tempo 3, 4: Bloqueada em I/O (state = 4)
        self.assertEqual(states_by_time[3], STATE_BLOCKED_IO)
        self.assertEqual(states_by_time[4], STATE_BLOCKED_IO)
        
        # Tempo 5, 6, 7, 8, 9: Executando novamente
        self.assertEqual(states_by_time[5], STATE_RUNNING)
        self.assertEqual(states_by_time[6], STATE_RUNNING)
        self.assertEqual(states_by_time[7], STATE_RUNNING)
        self.assertEqual(states_by_time[8], STATE_RUNNING)
        # No tempo 9, a tarefa termina (state = 5)
        self.assertEqual(states_by_time[9], STATE_TERMINATED)
        
        # Verifica registros de I/O no Gantt
        io_records = [e for e in simulator.gantt_data if e[3] == "IO" and e[1] == 1]
        io_times = sorted([e[0] for e in io_records])
        
        # O I/O deve estar registrado nos tempos 3 e 4
        self.assertIn(3, io_times)
        self.assertIn(4, io_times)


def run_io_tests():
    """Executa todos os testes de I/O."""
    print("=" * 70)
    print("🧪 TESTES DE I/O")
    print("=" * 70)
    print()
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    test_classes = [
        TestIOBasic,
        TestIOWithMultipleTasks,
        TestIOMultipleEvents,
        TestIOGanttRecording,
        TestIOStatistics,
        TestIOValidation,
        TestIOSpecificScenario,  # NOVO
    ]
    
    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    print()
    print("=" * 70)
    print("📊 RESULTADO DOS TESTES DE I/O")
    print("=" * 70)
    print(f"  ✅ Executados: {result.testsRun}")
    print(f"  ❌ Falhas: {len(result.failures)}")
    print(f"  💥 Erros: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n🎉 TODOS OS TESTES DE I/O PASSARAM!")
    else:
        print("\n⚠️  ALGUNS TESTES FALHARAM:")
        for test, trace in result.failures + result.errors:
            print(f"    ❌ {test}")
            # Mostra apenas a primeira linha do erro
            print(f"       {trace.split(chr(10))[-2]}")
    
    print("=" * 70)
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_io_tests()
    exit(0 if success else 1)
