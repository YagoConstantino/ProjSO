"""
Testes automatizados para o simulador de escalonamento de processos.

Testes incluídos:
1. Algoritmos de escalonamento (FIFO, SRTF, Priority, RR, PRIOPEnv)
2. Desenho de tarefas READY no Gantt (quadrados transparentes)
3. Conversão de cores hexadecimais
4. Eventos de I/O
5. Eventos de Mutex
"""

import unittest
import sys
import os

# Adiciona o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tasks import TCB, TCBQueue, STATE_NEW, STATE_READY, STATE_RUNNING, STATE_BLOCKED_IO, STATE_TERMINATED
from scheduler import (
    FIFOScheduler, SRTFScheduler, PriorityScheduler, 
    RoundRobinScheduler, PRIOPEnvScheduler
)
from simulador import Simulator
from config_loader import hex_to_rgb, parse_events, load_simulation_config


class TestHexToRGB(unittest.TestCase):
    """Testes para conversão de cores hexadecimais."""
    
    def test_hex_red(self):
        """Testa cor vermelha."""
        result = hex_to_rgb("FF0000")
        self.assertEqual(result, [255, 0, 0])
    
    def test_hex_green(self):
        """Testa cor verde."""
        result = hex_to_rgb("00FF00")
        self.assertEqual(result, [0, 255, 0])
    
    def test_hex_blue(self):
        """Testa cor azul."""
        result = hex_to_rgb("0000FF")
        self.assertEqual(result, [0, 0, 255])
    
    def test_hex_with_hash(self):
        """Testa cor com # no início."""
        result = hex_to_rgb("#FF5500")
        self.assertEqual(result, [255, 85, 0])
    
    def test_hex_lowercase(self):
        """Testa cor em minúsculas."""
        result = hex_to_rgb("aabbcc")
        self.assertEqual(result, [170, 187, 204])
    
    def test_hex_mixed_case(self):
        """Testa cor com maiúsculas e minúsculas."""
        result = hex_to_rgb("AaBbCc")
        self.assertEqual(result, [170, 187, 204])
    
    def test_hex_white(self):
        """Testa cor branca."""
        result = hex_to_rgb("FFFFFF")
        self.assertEqual(result, [255, 255, 255])
    
    def test_hex_black(self):
        """Testa cor preta."""
        result = hex_to_rgb("000000")
        self.assertEqual(result, [0, 0, 0])
    
    def test_hex_invalid_short(self):
        """Testa erro com cor curta demais."""
        with self.assertRaises(ValueError):
            hex_to_rgb("FFF")
    
    def test_hex_invalid_long(self):
        """Testa erro com cor longa demais."""
        with self.assertRaises(ValueError):
            hex_to_rgb("FFFFFFF")
    
    def test_hex_invalid_chars(self):
        """Testa erro com caracteres inválidos."""
        with self.assertRaises(ValueError):
            hex_to_rgb("GGGGGG")


class TestFIFOScheduler(unittest.TestCase):
    """Testes para o escalonador FIFO."""
    
    def setUp(self):
        """Configura tarefas de teste."""
        self.task1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=3, prio_s=1)
        self.task2 = TCB(id=2, RGB=[0, 255, 0], inicio=0, duracao=2, prio_s=5)
        self.task3 = TCB(id=3, RGB=[0, 0, 255], inicio=1, duracao=1, prio_s=3)
    
    def test_fifo_order(self):
        """Testa que FIFO executa na ordem de chegada."""
        scheduler = FIFOScheduler()
        tasks = [self.task1, self.task2, self.task3]
        simulator = Simulator(scheduler, tasks)
        
        simulator.run_full()
        
        # Verifica ordem de término (FIFO: T1 termina antes de T2)
        # T1 chega em 0, dura 3 -> termina em 3
        # T2 chega em 0, mas espera T1 -> termina em 5
        # T3 chega em 1, espera T1 e T2 -> termina em 6
        self.assertEqual(self.task1.fim, 3)
        self.assertEqual(self.task2.fim, 5)
        self.assertEqual(self.task3.fim, 6)
    
    def test_fifo_no_preemption(self):
        """Testa que FIFO não tem preempção."""
        scheduler = FIFOScheduler()
        tasks = [self.task1, self.task2]
        simulator = Simulator(scheduler, tasks)
        
        # Executa passo a passo
        for _ in range(3):  # T1 deve executar por 3 unidades
            simulator.step()
        
        # T1 deve ter terminado
        self.assertEqual(self.task1.state, STATE_TERMINATED)
        # T2 ainda não terminou
        self.assertNotEqual(self.task2.state, STATE_TERMINATED)


class TestSRTFScheduler(unittest.TestCase):
    """Testes para o escalonador SRTF."""
    
    def setUp(self):
        """Configura tarefas de teste."""
        self.task1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=5)
        self.task2 = TCB(id=2, RGB=[0, 255, 0], inicio=2, duracao=2)
    
    def test_srtf_preemption(self):
        """Testa que SRTF faz preempção corretamente."""
        scheduler = SRTFScheduler()
        tasks = [self.task1, self.task2]
        simulator = Simulator(scheduler, tasks)
        
        # T1 começa em 0, executa até T2 chegar em 2
        # T2 tem tempo restante 2, T1 tem 3 -> T2 preempta
        simulator.run_full()
        
        # T2 (menor tempo) deve terminar antes
        # T2 chega em 2, executa 2 unidades -> termina em 4
        # T1 executa 2 unidades (0-2), pausa, depois mais 3 -> termina em 7
        self.assertEqual(self.task2.fim, 4)
        self.assertEqual(self.task1.fim, 7)
    
    def test_srtf_shortest_first(self):
        """Testa que SRTF escolhe a tarefa com menor tempo restante."""
        task_long = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=10)
        task_short = TCB(id=2, RGB=[0, 255, 0], inicio=0, duracao=2)
        
        scheduler = SRTFScheduler()
        tasks = [task_long, task_short]
        simulator = Simulator(scheduler, tasks)
        
        simulator.run_full()
        
        # T2 (mais curta) deve terminar primeiro
        self.assertEqual(task_short.fim, 2)
        self.assertEqual(task_long.fim, 12)


class TestPriorityScheduler(unittest.TestCase):
    """Testes para o escalonador por Prioridade."""
    
    def setUp(self):
        """Configura tarefas de teste."""
        self.task_low = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=3, prio_s=1)
        self.task_high = TCB(id=2, RGB=[0, 255, 0], inicio=0, duracao=2, prio_s=10)
    
    def test_priority_high_first(self):
        """Testa que tarefa de maior prioridade executa primeiro."""
        scheduler = PriorityScheduler()
        tasks = [self.task_low, self.task_high]
        simulator = Simulator(scheduler, tasks)
        
        simulator.run_full()
        
        # T2 (alta prioridade) deve terminar primeiro
        self.assertEqual(self.task_high.fim, 2)
        self.assertEqual(self.task_low.fim, 5)
    
    def test_priority_preemption(self):
        """Testa preempção por prioridade."""
        task_low = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=5, prio_s=1)
        task_high = TCB(id=2, RGB=[0, 255, 0], inicio=2, duracao=2, prio_s=10)
        
        scheduler = PriorityScheduler()
        tasks = [task_low, task_high]
        simulator = Simulator(scheduler, tasks)
        
        simulator.run_full()
        
        # T2 chega em 2 e preempta T1
        self.assertEqual(task_high.fim, 4)
        self.assertEqual(task_low.fim, 7)


class TestRoundRobinScheduler(unittest.TestCase):
    """Testes para o escalonador Round-Robin."""
    
    def test_rr_quantum_rotation(self):
        """Testa rotação por quantum."""
        task1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=4)
        task2 = TCB(id=2, RGB=[0, 255, 0], inicio=0, duracao=4)
        
        scheduler = RoundRobinScheduler(quantum=2)
        tasks = [task1, task2]
        simulator = Simulator(scheduler, tasks)
        
        simulator.run_full()
        
        # Com quantum=2:
        # T1 executa 0-2, T2 executa 2-4, T1 executa 4-6, T2 executa 6-8
        self.assertEqual(task1.fim, 6)
        self.assertEqual(task2.fim, 8)
    
    def test_rr_short_task(self):
        """Testa tarefa que termina antes do quantum."""
        task1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=1)
        task2 = TCB(id=2, RGB=[0, 255, 0], inicio=0, duracao=3)
        
        scheduler = RoundRobinScheduler(quantum=2)
        tasks = [task1, task2]
        simulator = Simulator(scheduler, tasks)
        
        simulator.run_full()
        
        # T1 termina em 1, T2 executa resto
        self.assertEqual(task1.fim, 1)
        self.assertEqual(task2.fim, 4)


class TestPRIOPEnvScheduler(unittest.TestCase):
    """Testes para o escalonador PRIOPEnv (Prioridade com Envelhecimento)."""
    
    def test_priopenv_aging(self):
        """Testa envelhecimento de prioridade."""
        task_low = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=2, prio_s=1)
        task_high = TCB(id=2, RGB=[0, 255, 0], inicio=1, duracao=2, prio_s=5)
        
        scheduler = PRIOPEnvScheduler(quantum=2, alpha=2)
        tasks = [task_low, task_high]
        simulator = Simulator(scheduler, tasks)
        
        # Antes de T2 chegar, T1 está executando
        # Quando T2 chega (tempo 1), T1 envelhece: prio_d = 1 + 2 = 3
        # Mas T2 tem prio_d = 5, então T2 preempta
        
        simulator.run_full()
        
        # Verifica que envelhecimento foi aplicado
        self.assertTrue(task_low.prio_d >= task_low.prio_s)
    
    def test_priopenv_prevents_starvation(self):
        """Testa que envelhecimento previne starvation."""
        # Tarefa de baixa prioridade chega primeiro
        task_low = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=3, prio_s=1)
        # Várias tarefas de alta prioridade chegam depois
        task_high1 = TCB(id=2, RGB=[0, 255, 0], inicio=1, duracao=2, prio_s=10)
        task_high2 = TCB(id=3, RGB=[0, 0, 255], inicio=2, duracao=2, prio_s=10)
        
        scheduler = PRIOPEnvScheduler(quantum=1, alpha=5)
        tasks = [task_low, task_high1, task_high2]
        simulator = Simulator(scheduler, tasks)
        
        simulator.run_full()
        
        # Todas as tarefas devem terminar
        self.assertEqual(task_low.state, STATE_TERMINATED)
        self.assertEqual(task_high1.state, STATE_TERMINATED)
        self.assertEqual(task_high2.state, STATE_TERMINATED)


class TestGanttREADYStates(unittest.TestCase):
    """Testes para verificar que tarefas READY são registradas no Gantt."""
    
    def test_ready_tasks_in_gantt(self):
        """Testa que tarefas READY aparecem no gantt_data."""
        task1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=3)
        task2 = TCB(id=2, RGB=[0, 255, 0], inicio=0, duracao=3)
        
        scheduler = FIFOScheduler()
        tasks = [task1, task2]
        simulator = Simulator(scheduler, tasks)
        
        # Executa um passo
        simulator.step()
        
        # Verifica que há entradas READY no gantt_data
        ready_entries = [e for e in simulator.gantt_data if len(e) == 4 and e[3] == "READY"]
        
        # Deve haver pelo menos uma entrada READY
        self.assertGreater(len(ready_entries), 0)
    
    def test_ready_task_has_correct_format(self):
        """Testa que entradas READY têm formato correto."""
        task1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=3)
        task2 = TCB(id=2, RGB=[0, 255, 0], inicio=0, duracao=3)
        
        scheduler = FIFOScheduler()
        tasks = [task1, task2]
        simulator = Simulator(scheduler, tasks)
        
        simulator.step()
        
        # Verifica formato das entradas
        for entry in simulator.gantt_data:
            self.assertEqual(len(entry), 4)  # (time, task_id, RGB, state)
            time, task_id, rgb, state = entry
            self.assertIsInstance(time, int)
            self.assertIn(state, ["READY", "EXEC", "IO", "MUTEX", "IDLE"])
            if state != "IDLE":
                self.assertIsInstance(rgb, list)
                self.assertEqual(len(rgb), 3)
    
    def test_multiple_ready_tasks(self):
        """Testa que múltiplas tarefas READY são registradas."""
        task1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=5)
        task2 = TCB(id=2, RGB=[0, 255, 0], inicio=0, duracao=5)
        task3 = TCB(id=3, RGB=[0, 0, 255], inicio=0, duracao=5)
        
        scheduler = FIFOScheduler()
        tasks = [task1, task2, task3]
        simulator = Simulator(scheduler, tasks)
        
        simulator.step()
        
        # No tempo 0, TODAS as tarefas chegam e são registradas como READY
        # ANTES de selecionar qual vai executar
        # Portanto, T1, T2 e T3 são registradas como READY
        ready_at_time_0 = [e for e in simulator.gantt_data 
                          if len(e) == 4 and e[0] == 0 and e[3] == "READY"]
        
        # Deve haver 3 tarefas READY (todas chegam no tempo 0)
        self.assertEqual(len(ready_at_time_0), 3)


class TestIOEvents(unittest.TestCase):
    """Testes para eventos de I/O."""
    
    def test_io_blocks_task(self):
        """Testa que evento de I/O bloqueia a tarefa."""
        # Tarefa com evento de I/O no tempo de execução 1
        task = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=5, io_events=[(1, 2)])
        
        scheduler = FIFOScheduler()
        simulator = Simulator(scheduler, [task])
        
        # Executa até o I/O
        simulator.step()  # T=0: executa
        simulator.step()  # T=1: I/O (tempo_exec_acumulado = 1)
        
        # Tarefa deve estar bloqueada
        self.assertEqual(task.state, STATE_BLOCKED_IO)
    
    def test_io_in_gantt(self):
        """Testa que I/O aparece no gantt_data."""
        task = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=5, io_events=[(1, 2)])
        
        scheduler = FIFOScheduler()
        simulator = Simulator(scheduler, [task])
        
        simulator.run_full()
        
        # Verifica que há entradas IO no gantt_data
        io_entries = [e for e in simulator.gantt_data if len(e) == 4 and e[3] == "IO"]
        self.assertGreater(len(io_entries), 0)


class TestParseEvents(unittest.TestCase):
    """Testes para parsing de eventos."""
    
    def test_parse_io_event(self):
        """Testa parsing de evento de I/O."""
        io_events, ml_events, mu_events = parse_events("IO:2-3")
        
        self.assertEqual(io_events, [(2, 3)])
        self.assertEqual(ml_events, [])
        self.assertEqual(mu_events, [])
    
    def test_parse_mutex_events(self):
        """Testa parsing de eventos de mutex."""
        io_events, ml_events, mu_events = parse_events("ML:1;MU:3")
        
        self.assertEqual(io_events, [])
        self.assertEqual(ml_events, [1])
        self.assertEqual(mu_events, [3])
    
    def test_parse_mixed_events(self):
        """Testa parsing de eventos misturados."""
        io_events, ml_events, mu_events = parse_events("ML:0;IO:2-1;MU:4")
        
        self.assertEqual(io_events, [(2, 1)])
        self.assertEqual(ml_events, [0])
        self.assertEqual(mu_events, [4])
    
    def test_parse_empty_string(self):
        """Testa parsing de string vazia."""
        io_events, ml_events, mu_events = parse_events("")
        
        self.assertEqual(io_events, [])
        self.assertEqual(ml_events, [])
        self.assertEqual(mu_events, [])


class TestSimulatorBasics(unittest.TestCase):
    """Testes básicos do simulador."""
    
    def test_simulation_completes(self):
        """Testa que simulação termina."""
        task = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=3)
        
        scheduler = FIFOScheduler()
        simulator = Simulator(scheduler, [task])
        
        simulator.run_full()
        
        self.assertTrue(simulator.is_finished())
        self.assertEqual(task.state, STATE_TERMINATED)
    
    def test_time_increments(self):
        """Testa que tempo incrementa corretamente."""
        task = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=3)
        
        scheduler = FIFOScheduler()
        simulator = Simulator(scheduler, [task])
        
        self.assertEqual(simulator.time, 0)
        simulator.step()
        self.assertEqual(simulator.time, 1)
        simulator.step()
        self.assertEqual(simulator.time, 2)
    
    def test_task_arrival(self):
        """Testa chegada de tarefa no tempo correto."""
        task = TCB(id=1, RGB=[255, 0, 0], inicio=3, duracao=2)
        
        scheduler = FIFOScheduler()
        simulator = Simulator(scheduler, [task])
        
        # Antes do tempo 3, tarefa está NEW
        for i in range(3):
            self.assertEqual(task.state, STATE_NEW, f"Tarefa deveria estar NEW no tempo {i}")
            simulator.step()
        
        # Após 3 steps (tempo atual = 3), a tarefa foi processada no step anterior
        # e agora deve estar READY ou RUNNING
        # Precisamos executar mais um step para processar a chegada no tempo 3
        simulator.step()
        
        # Agora a tarefa deve estar READY ou RUNNING (já foi processada)
        self.assertIn(task.state, [STATE_READY, STATE_RUNNING])


class TestTCBQueue(unittest.TestCase):
    """Testes para a fila de TCBs."""
    
    def test_push_pop(self):
        """Testa push e pop."""
        queue = TCBQueue()
        task1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=1)
        task2 = TCB(id=2, RGB=[0, 255, 0], inicio=0, duracao=1)
        
        queue.push_back(task1)
        queue.push_back(task2)
        
        self.assertEqual(queue.pop_front(), task1)
        self.assertEqual(queue.pop_front(), task2)
    
    def test_remove(self):
        """Testa remoção de elemento."""
        queue = TCBQueue()
        task1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=1)
        task2 = TCB(id=2, RGB=[0, 255, 0], inicio=0, duracao=1)
        task3 = TCB(id=3, RGB=[0, 0, 255], inicio=0, duracao=1)
        
        queue.push_back(task1)
        queue.push_back(task2)
        queue.push_back(task3)
        
        queue.remove(task2)
        
        self.assertEqual(queue.pop_front(), task1)
        self.assertEqual(queue.pop_front(), task3)
    
    def test_is_empty(self):
        """Testa verificação de fila vazia."""
        queue = TCBQueue()
        self.assertTrue(queue.is_empty())
        
        task = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=1)
        queue.push_back(task)
        self.assertFalse(queue.is_empty())
        
        queue.pop_front()
        self.assertTrue(queue.is_empty())


def run_tests():
    """Executa todos os testes e exibe resultado."""
    # Cria loader de testes
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Adiciona todas as classes de teste
    suite.addTests(loader.loadTestsFromTestCase(TestHexToRGB))
    suite.addTests(loader.loadTestsFromTestCase(TestFIFOScheduler))
    suite.addTests(loader.loadTestsFromTestCase(TestSRTFScheduler))
    suite.addTests(loader.loadTestsFromTestCase(TestPriorityScheduler))
    suite.addTests(loader.loadTestsFromTestCase(TestRoundRobinScheduler))
    suite.addTests(loader.loadTestsFromTestCase(TestPRIOPEnvScheduler))
    suite.addTests(loader.loadTestsFromTestCase(TestGanttREADYStates))
    suite.addTests(loader.loadTestsFromTestCase(TestIOEvents))
    suite.addTests(loader.loadTestsFromTestCase(TestParseEvents))
    suite.addTests(loader.loadTestsFromTestCase(TestSimulatorBasics))
    suite.addTests(loader.loadTestsFromTestCase(TestTCBQueue))
    
    # Executa testes
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Resumo
    print("\n" + "=" * 70)
    print("📊 RESUMO DOS TESTES")
    print("=" * 70)
    print(f"✅ Testes executados: {result.testsRun}")
    print(f"❌ Falhas: {len(result.failures)}")
    print(f"💥 Erros: {len(result.errors)}")
    print(f"⏭️  Pulados: {len(result.skipped)}")
    
    if result.wasSuccessful():
        print("\n🎉 TODOS OS TESTES PASSARAM!")
    else:
        print("\n⚠️  ALGUNS TESTES FALHARAM!")
        
        if result.failures:
            print("\n--- Falhas ---")
            for test, trace in result.failures:
                print(f"  ❌ {test}: {trace.split(chr(10))[0]}")
        
        if result.errors:
            print("\n--- Erros ---")
            for test, trace in result.errors:
                print(f"  💥 {test}: {trace.split(chr(10))[0]}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
