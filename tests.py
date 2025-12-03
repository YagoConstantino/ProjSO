"""
Suite de Testes Completa para o Simulador de Escalonamento de Processos.

Testa:
1. Salvamento e edição de arquivos TXT
2. Funcionamento dos escalonadores (FIFO, SRTF, PRIO, RR, PRIOPEnv)
3. Geração aleatória de tarefas
4. Execução da simulação e dados do Gantt
5. Parsing de configuração e eventos
6. Conversão de cores hex para RGB

Execute com: python3 tests.py
"""

import unittest
import os
import tempfile
import random
from typing import List

# Importações do projeto
from config_loader import load_simulation_config, hex_to_rgb, parse_events
from tasks import TCB, TCBQueue, STATE_NEW, STATE_READY, STATE_RUNNING, STATE_TERMINATED
from scheduler import (
    FIFOScheduler, SRTFScheduler, PriorityScheduler, 
    RoundRobinScheduler, PRIOPEnvScheduler
)
from simulador import Simulator


# =============================================================================
# TESTES DE PARSING E CONFIGURAÇÃO
# =============================================================================

class TestHexToRGB(unittest.TestCase):
    """Testes para conversão de cores hexadecimais para RGB."""
    
    def test_uppercase(self):
        """Testa conversão com letras maiúsculas."""
        self.assertEqual(hex_to_rgb("FF0000"), [255, 0, 0])
        self.assertEqual(hex_to_rgb("00FF00"), [0, 255, 0])
        self.assertEqual(hex_to_rgb("0000FF"), [0, 0, 255])
    
    def test_lowercase(self):
        """Testa conversão com letras minúsculas."""
        self.assertEqual(hex_to_rgb("ff0000"), [255, 0, 0])
        self.assertEqual(hex_to_rgb("00ff00"), [0, 255, 0])
    
    def test_mixed_case(self):
        """Testa conversão com letras mistas."""
        self.assertEqual(hex_to_rgb("FfAa00"), [255, 170, 0])
    
    def test_with_hash(self):
        """Testa conversão com prefixo #."""
        self.assertEqual(hex_to_rgb("#00FF00"), [0, 255, 0])
        self.assertEqual(hex_to_rgb("#ffffff"), [255, 255, 255])
    
    def test_black_white(self):
        """Testa cores extremas."""
        self.assertEqual(hex_to_rgb("000000"), [0, 0, 0])
        self.assertEqual(hex_to_rgb("FFFFFF"), [255, 255, 255])
    
    def test_invalid_length(self):
        """Testa que formato inválido gera erro."""
        with self.assertRaises(ValueError):
            hex_to_rgb("FFF")
        with self.assertRaises(ValueError):
            hex_to_rgb("FFFFFFF")
    
    def test_invalid_chars(self):
        """Testa que caracteres inválidos geram erro."""
        with self.assertRaises(ValueError):
            hex_to_rgb("GGGGGG")
        with self.assertRaises(ValueError):
            hex_to_rgb("ZZZZZZ")


class TestParseEvents(unittest.TestCase):
    """Testes para parsing de eventos (I/O, ML, MU)."""
    
    def test_io_only(self):
        """Testa parsing apenas de eventos I/O."""
        io, ml, mu = parse_events("IO:2-1;IO:5-3")
        self.assertEqual(io, [(2, 1), (5, 3)])
        self.assertEqual(ml, [])
        self.assertEqual(mu, [])
    
    def test_mutex_only(self):
        """Testa parsing apenas de eventos mutex."""
        io, ml, mu = parse_events("ML:1;ML:4;MU:3;MU:6")
        self.assertEqual(io, [])
        self.assertEqual(ml, [1, 4])
        self.assertEqual(mu, [3, 6])
    
    def test_mixed_events(self):
        """Testa parsing de eventos mistos."""
        io, ml, mu = parse_events("ML:0;IO:2-1;MU:4;IO:5-2")
        self.assertEqual(io, [(2, 1), (5, 2)])
        self.assertEqual(ml, [0])
        self.assertEqual(mu, [4])
    
    def test_empty_string(self):
        """Testa parsing de string vazia."""
        io, ml, mu = parse_events("")
        self.assertEqual(io, [])
        self.assertEqual(ml, [])
        self.assertEqual(mu, [])
    
    def test_single_event(self):
        """Testa parsing de evento único."""
        io, ml, mu = parse_events("IO:3-2")
        self.assertEqual(io, [(3, 2)])


# =============================================================================
# TESTES DE SALVAMENTO E CARREGAMENTO DE ARQUIVOS
# =============================================================================

class TestFileOperations(unittest.TestCase):
    """Testes para operações de salvamento e carregamento de arquivos."""
    
    def setUp(self):
        """Cria diretório temporário para testes."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test_config.txt")
    
    def tearDown(self):
        """Remove arquivos temporários."""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        if os.path.exists(self.temp_dir):
            os.rmdir(self.temp_dir)
    
    def _create_config_file(self, content: str):
        """Cria arquivo de configuração com conteúdo especificado."""
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write(content)
    
    def _save_config(self, algo: str, quantum, alpha, tasks: List[TCB]) -> str:
        """Simula salvamento de configuração (como no main.py)."""
        header_parts = [algo]
        if quantum:
            header_parts.append(str(quantum))
        if alpha:
            if not quantum:
                header_parts.append("")
            header_parts.append(str(alpha))
        
        while header_parts and header_parts[-1] == "":
            header_parts.pop()
        
        header = ";".join(header_parts)
        content = header + "\n"
        content += "#id;cor_hex;ingresso;duracao;prioridade;eventos\n"
        
        for task in sorted(tasks, key=lambda t: t.id if isinstance(t.id, int) else 0):
            tid = f"t{task.id:02d}" if isinstance(task.id, int) else f"t{task.id}"
            cor = f"{task.RGB[0]:02x}{task.RGB[1]:02x}{task.RGB[2]:02x}"
            
            events = []
            if task.io_events:
                for t, d in task.io_events:
                    events.append(f"IO:{t}-{d}")
            if task.ml_events:
                for t in task.ml_events:
                    events.append(f"ML:{t}")
            if task.mu_events:
                for t in task.mu_events:
                    events.append(f"MU:{t}")
            
            line = f"{tid};{cor};{task.inicio};{task.duracao};{task.prio_s}"
            if events:
                line += ";" + ";".join(events)
            content += line + "\n"
        
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write(content)
        
        return content
    
    def test_save_and_load_basic(self):
        """Testa salvamento e carregamento básico."""
        tasks = [
            TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=5, prio_s=10),
            TCB(id=2, RGB=[0, 255, 0], inicio=2, duracao=3, prio_s=5),
        ]
        
        self._save_config("FIFO", None, None, tasks)
        algo, quantum, alpha, loaded = load_simulation_config(self.test_file)
        
        self.assertEqual(algo, "FIFO")
        self.assertIsNone(quantum)
        self.assertIsNone(alpha)
        self.assertEqual(len(loaded), 2)
    
    def test_save_and_load_with_quantum(self):
        """Testa salvamento e carregamento com quantum."""
        tasks = [TCB(id=1, RGB=[128, 128, 128], inicio=0, duracao=4, prio_s=5)]
        
        self._save_config("RR", 3, None, tasks)
        algo, quantum, alpha, loaded = load_simulation_config(self.test_file)
        
        self.assertEqual(algo, "RR")
        self.assertEqual(quantum, 3)
    
    def test_save_and_load_with_alpha(self):
        """Testa salvamento e carregamento com alpha (PRIOPEnv)."""
        tasks = [TCB(id=1, RGB=[100, 150, 200], inicio=0, duracao=6, prio_s=8)]
        
        self._save_config("PRIOPENV", 2, 1, tasks)
        algo, quantum, alpha, loaded = load_simulation_config(self.test_file)
        
        self.assertEqual(algo, "PRIOPENV")
        self.assertEqual(quantum, 2)
        self.assertEqual(alpha, 1)
    
    def test_save_and_load_with_io_events(self):
        """Testa salvamento e carregamento com eventos I/O."""
        tasks = [
            TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=10, prio_s=5,
                io_events=[(2, 1), (5, 2)])
        ]
        
        self._save_config("SRTF", None, None, tasks)
        algo, quantum, alpha, loaded = load_simulation_config(self.test_file)
        
        self.assertEqual(len(loaded), 1)
        self.assertEqual(len(loaded[0].io_events), 2)
        self.assertIn((2, 1), loaded[0].io_events)
    
    def test_save_and_load_with_mutex_events(self):
        """Testa salvamento e carregamento com eventos mutex."""
        tasks = [
            TCB(id=1, RGB=[0, 255, 0], inicio=0, duracao=8, prio_s=5,
                ml_events=[1, 4], mu_events=[3, 6])
        ]
        
        self._save_config("PRIO", None, None, tasks)
        algo, quantum, alpha, loaded = load_simulation_config(self.test_file)
        
        self.assertEqual(loaded[0].ml_events, [1, 4])
        self.assertEqual(loaded[0].mu_events, [3, 6])
    
    def test_color_preservation(self):
        """Testa que cores são preservadas corretamente."""
        colors = [
            [255, 0, 0], [0, 255, 0], [0, 0, 255],
            [255, 255, 0], [128, 64, 32], [0, 0, 0], [255, 255, 255]
        ]
        tasks = [TCB(id=i+1, RGB=c, inicio=0, duracao=1, prio_s=1) for i, c in enumerate(colors)]
        
        self._save_config("FIFO", None, None, tasks)
        algo, quantum, alpha, loaded = load_simulation_config(self.test_file)
        
        for i, original_color in enumerate(colors):
            loaded_task = next(t for t in loaded if t.id == i+1)
            self.assertEqual(loaded_task.RGB, original_color)
    
    def test_comments_ignored(self):
        """Testa que comentários são ignorados."""
        content = """FIFO;
#Este é um comentário
#id;cor;chegada;duracao;prioridade
t01;ff0000;0;5;10
#Outro comentário
t02;00ff00;2;3;5
"""
        self._create_config_file(content)
        algo, quantum, alpha, tasks = load_simulation_config(self.test_file)
        
        self.assertEqual(len(tasks), 2)


# =============================================================================
# TESTES DOS ESCALONADORES
# =============================================================================

class TestFIFOScheduler(unittest.TestCase):
    """Testes para o escalonador FIFO."""
    
    def test_selects_first_task(self):
        """Testa que FIFO seleciona a primeira tarefa da fila."""
        scheduler = FIFOScheduler()
        queue = TCBQueue()
        
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=5, prio_s=1)
        t2 = TCB(id=2, RGB=[0, 255, 0], inicio=0, duracao=3, prio_s=10)
        
        queue.push_back(t1)
        queue.push_back(t2)
        
        selected = scheduler.select_next_task(queue, None, 0)
        self.assertEqual(selected.id, 1)
    
    def test_keeps_current_task(self):
        """Testa que FIFO mantém a tarefa atual até terminar."""
        scheduler = FIFOScheduler()
        queue = TCBQueue()
        
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=5, prio_s=1)
        t2 = TCB(id=2, RGB=[0, 255, 0], inicio=0, duracao=3, prio_s=10)
        
        queue.push_back(t1)
        queue.push_back(t2)
        
        selected = scheduler.select_next_task(queue, t1, 0)
        self.assertEqual(selected.id, 1)
    
    def test_no_preemption(self):
        """Testa que FIFO não faz preempção."""
        scheduler = FIFOScheduler()
        queue = TCBQueue()
        
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=10, prio_s=1)
        t2 = TCB(id=2, RGB=[0, 255, 0], inicio=0, duracao=1, prio_s=100)
        
        queue.push_back(t1)
        queue.push_back(t2)
        
        # Mesmo com t2 tendo prioridade maior, t1 continua
        selected = scheduler.select_next_task(queue, t1, 5)
        self.assertEqual(selected.id, 1)


class TestSRTFScheduler(unittest.TestCase):
    """Testes para o escalonador SRTF."""
    
    def test_selects_shortest_remaining(self):
        """Testa que SRTF seleciona a tarefa com menor tempo restante."""
        scheduler = SRTFScheduler()
        queue = TCBQueue()
        
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=10, prio_s=1)
        t2 = TCB(id=2, RGB=[0, 255, 0], inicio=0, duracao=3, prio_s=1)
        
        queue.push_back(t1)
        queue.push_back(t2)
        
        selected = scheduler.select_next_task(queue, None, 0)
        self.assertEqual(selected.id, 2)
    
    def test_preemption_on_shorter_arrival(self):
        """Testa preempção quando chega tarefa mais curta."""
        scheduler = SRTFScheduler()
        queue = TCBQueue()
        
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=10, prio_s=1)
        t1.tempo_restante = 8  # Já executou 2 unidades
        
        t2 = TCB(id=2, RGB=[0, 255, 0], inicio=2, duracao=3, prio_s=1)
        
        queue.push_back(t1)
        queue.push_back(t2)
        
        # t2 tem tempo_restante=3, menor que t1.tempo_restante=8
        selected = scheduler.select_next_task(queue, t1, 2)
        self.assertEqual(selected.id, 2)


class TestPriorityScheduler(unittest.TestCase):
    """Testes para o escalonador por Prioridade."""
    
    def test_selects_highest_priority(self):
        """Testa que seleciona a tarefa com maior prioridade."""
        scheduler = PriorityScheduler()
        queue = TCBQueue()
        
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=5, prio_s=5)
        t2 = TCB(id=2, RGB=[0, 255, 0], inicio=0, duracao=5, prio_s=10)
        
        queue.push_back(t1)
        queue.push_back(t2)
        
        selected = scheduler.select_next_task(queue, None, 0)
        self.assertEqual(selected.id, 2)
    
    def test_preemption_on_higher_priority(self):
        """Testa preempção quando chega tarefa de maior prioridade."""
        scheduler = PriorityScheduler()
        queue = TCBQueue()
        
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=10, prio_s=5)
        t2 = TCB(id=2, RGB=[0, 255, 0], inicio=2, duracao=3, prio_s=10)
        
        queue.push_back(t1)
        queue.push_back(t2)
        
        selected = scheduler.select_next_task(queue, t1, 2)
        self.assertEqual(selected.id, 2)


class TestRoundRobinScheduler(unittest.TestCase):
    """Testes para o escalonador Round-Robin."""
    
    def test_quantum_initialization(self):
        """Testa inicialização do quantum."""
        scheduler = RoundRobinScheduler(quantum=3)
        self.assertEqual(scheduler.quantum, 3)
        self.assertEqual(scheduler.time_slice_remaining, 3)
    
    def test_selects_first_when_no_current(self):
        """Testa seleção da primeira tarefa quando não há tarefa atual."""
        scheduler = RoundRobinScheduler(quantum=2)
        queue = TCBQueue()
        
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=5, prio_s=1)
        t2 = TCB(id=2, RGB=[0, 255, 0], inicio=0, duracao=3, prio_s=1)
        
        queue.push_back(t1)
        queue.push_back(t2)
        
        selected = scheduler.select_next_task(queue, None, 0)
        self.assertEqual(selected.id, 1)
    
    def test_quantum_decrement(self):
        """Testa decremento do quantum."""
        scheduler = RoundRobinScheduler(quantum=3)
        scheduler.decrement_quantum()
        self.assertEqual(scheduler.time_slice_remaining, 2)
    
    def test_quantum_reset(self):
        """Testa reset do quantum."""
        scheduler = RoundRobinScheduler(quantum=3)
        scheduler.time_slice_remaining = 0
        scheduler.reset_quantum()
        self.assertEqual(scheduler.time_slice_remaining, 3)


class TestPRIOPEnvScheduler(unittest.TestCase):
    """Testes para o escalonador com Envelhecimento."""
    
    def test_initialization(self):
        """Testa inicialização com quantum e alpha."""
        scheduler = PRIOPEnvScheduler(quantum=2, alpha=1)
        self.assertEqual(scheduler.quantum, 2)
        self.assertEqual(scheduler.alpha, 1)
    
    def test_aging(self):
        """Testa envelhecimento das tarefas."""
        scheduler = PRIOPEnvScheduler(quantum=2, alpha=1)
        queue = TCBQueue()
        
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=5, prio_s=5)
        t1.prio_d = 5
        t2 = TCB(id=2, RGB=[0, 255, 0], inicio=0, duracao=3, prio_s=3)
        t2.prio_d = 3
        
        queue.push_back(t1)
        queue.push_back(t2)
        
        scheduler.age_tasks(queue, exclude_task=None)
        
        self.assertEqual(t1.prio_d, 6)  # 5 + 1
        self.assertEqual(t2.prio_d, 4)  # 3 + 1
    
    def test_exclude_from_aging(self):
        """Testa exclusão de tarefa do envelhecimento."""
        scheduler = PRIOPEnvScheduler(quantum=2, alpha=2)
        queue = TCBQueue()
        
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=5, prio_s=5)
        t1.prio_d = 5
        t2 = TCB(id=2, RGB=[0, 255, 0], inicio=0, duracao=3, prio_s=3)
        t2.prio_d = 3
        
        queue.push_back(t1)
        queue.push_back(t2)
        
        scheduler.age_tasks(queue, exclude_task=t1)
        
        self.assertEqual(t1.prio_d, 5)  # Não mudou
        self.assertEqual(t2.prio_d, 5)  # 3 + 2


# =============================================================================
# TESTES DA SIMULAÇÃO
# =============================================================================

class TestSimulator(unittest.TestCase):
    """Testes para o simulador."""
    
    def test_basic_execution(self):
        """Testa execução básica de uma tarefa."""
        tasks = [TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=3, prio_s=5)]
        scheduler = FIFOScheduler()
        simulator = Simulator(scheduler, tasks)
        
        simulator.run_full()
        
        self.assertTrue(simulator.is_finished())
        self.assertEqual(len(simulator.done_tasks), 1)
    
    def test_multiple_tasks(self):
        """Testa execução de múltiplas tarefas."""
        tasks = [
            TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=2, prio_s=5),
            TCB(id=2, RGB=[0, 255, 0], inicio=0, duracao=3, prio_s=5),
        ]
        scheduler = FIFOScheduler()
        simulator = Simulator(scheduler, tasks)
        
        simulator.run_full()
        
        self.assertTrue(simulator.is_finished())
        self.assertEqual(len(simulator.done_tasks), 2)
    
    def test_gantt_data_generated(self):
        """Testa que dados do Gantt são gerados."""
        tasks = [TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=3, prio_s=5)]
        scheduler = FIFOScheduler()
        simulator = Simulator(scheduler, tasks)
        
        simulator.run_full()
        
        self.assertTrue(len(simulator.gantt_data) > 0)
    
    def test_task_arrival(self):
        """Testa chegada de tarefas em tempos diferentes."""
        tasks = [
            TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=2, prio_s=5),
            TCB(id=2, RGB=[0, 255, 0], inicio=3, duracao=2, prio_s=5),
        ]
        scheduler = FIFOScheduler()
        simulator = Simulator(scheduler, tasks)
        
        simulator.run_full()
        
        self.assertTrue(simulator.is_finished())
        self.assertEqual(simulator.time, 5)  # 0-2 para t1, 3-5 para t2
    
    def test_statistics_calculation(self):
        """Testa cálculo de estatísticas."""
        tasks = [
            TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=3, prio_s=5),
            TCB(id=2, RGB=[0, 255, 0], inicio=0, duracao=2, prio_s=5),
        ]
        scheduler = FIFOScheduler()
        simulator = Simulator(scheduler, tasks)
        
        simulator.run_full()
        stats = simulator.get_statistics()
        
        self.assertIn('avg_turnaround', stats)
        self.assertIn('avg_waiting', stats)
        self.assertIn('avg_response', stats)
        self.assertIn('tasks', stats)
        self.assertEqual(len(stats['tasks']), 2)
    
    def test_srtf_preemption(self):
        """Testa preempção no SRTF."""
        tasks = [
            TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=5, prio_s=5),
            TCB(id=2, RGB=[0, 255, 0], inicio=1, duracao=2, prio_s=5),
        ]
        scheduler = SRTFScheduler()
        simulator = Simulator(scheduler, tasks)
        
        simulator.run_full()
        
        # T2 deve terminar antes de T1 (preempção)
        t1 = next(t for t in simulator.all_tasks if t.id == 1)
        t2 = next(t for t in simulator.all_tasks if t.id == 2)
        self.assertLess(t2.fim, t1.fim)
    
    def test_round_robin_fairness(self):
        """Testa que Round-Robin alterna entre tarefas."""
        tasks = [
            TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=4, prio_s=5),
            TCB(id=2, RGB=[0, 255, 0], inicio=0, duracao=4, prio_s=5),
        ]
        scheduler = RoundRobinScheduler(quantum=2)
        simulator = Simulator(scheduler, tasks)
        
        simulator.run_full()
        
        # Verifica que ambas as tarefas foram executadas
        self.assertEqual(len(simulator.done_tasks), 2)
        
        # Verifica alternância no Gantt (simplificado)
        exec_data = [e for e in simulator.gantt_data if e[3] == "EXEC"]
        self.assertTrue(len(exec_data) >= 4)


class TestIOEvents(unittest.TestCase):
    """Testes para eventos de I/O."""
    
    def test_io_blocking(self):
        """Testa que I/O bloqueia a tarefa."""
        tasks = [
            TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=5, prio_s=5,
                io_events=[(2, 2)])  # I/O no tempo relativo 2, duração 2
        ]
        scheduler = FIFOScheduler()
        simulator = Simulator(scheduler, tasks)
        
        simulator.run_full()
        
        # Tempo total = 5 (duração) + 2 (I/O) = 7
        self.assertEqual(simulator.time, 7)


# =============================================================================
# TESTES DE GERAÇÃO ALEATÓRIA
# =============================================================================

class TestRandomGeneration(unittest.TestCase):
    """Testes para geração aleatória de tarefas."""
    
    def test_random_task_generation(self):
        """Testa geração de tarefas aleatórias."""
        num_tasks = 5
        tasks = []
        
        for i in range(num_tasks):
            task = TCB(
                id=i+1,
                RGB=[random.randint(0, 255) for _ in range(3)],
                inicio=random.randint(0, 20),
                duracao=random.randint(1, 10),
                prio_s=random.randint(1, 10)
            )
            tasks.append(task)
        
        self.assertEqual(len(tasks), num_tasks)
        
        # Verifica que todas as tarefas têm valores válidos
        for task in tasks:
            self.assertGreaterEqual(task.duracao, 1)
            self.assertLessEqual(task.duracao, 10)
            self.assertGreaterEqual(task.inicio, 0)
            self.assertLessEqual(task.inicio, 20)
            self.assertTrue(all(0 <= c <= 255 for c in task.RGB))
    
    def test_random_tasks_simulation(self):
        """Testa que tarefas aleatórias podem ser simuladas."""
        tasks = []
        for i in range(3):
            task = TCB(
                id=i+1,
                RGB=[random.randint(0, 255) for _ in range(3)],
                inicio=random.randint(0, 5),
                duracao=random.randint(1, 5),
                prio_s=random.randint(1, 10)
            )
            tasks.append(task)
        
        scheduler = FIFOScheduler()
        simulator = Simulator(scheduler, tasks)
        
        # Não deve lançar exceção
        simulator.run_full()
        
        self.assertTrue(simulator.is_finished())
    
    def test_random_file_generation_and_load(self):
        """Testa geração de arquivo aleatório e carregamento."""
        temp_dir = tempfile.mkdtemp()
        test_file = os.path.join(temp_dir, "random_test.txt")
        
        try:
            # Gera conteúdo aleatório
            num_tasks = 4
            content = "SRTF;2\n#id;cor;chegada;duracao;prioridade\n"
            for i in range(num_tasks):
                cor = f"{random.randint(0,255):02x}{random.randint(0,255):02x}{random.randint(0,255):02x}"
                content += f"t{i+1:02d};{cor};{random.randint(0,10)};{random.randint(1,5)};{random.randint(1,10)}\n"
            
            # Salva
            with open(test_file, "w") as f:
                f.write(content)
            
            # Carrega
            algo, quantum, alpha, tasks = load_simulation_config(test_file)
            
            self.assertEqual(algo, "SRTF")
            self.assertEqual(quantum, 2)
            self.assertEqual(len(tasks), num_tasks)
            
        finally:
            if os.path.exists(test_file):
                os.remove(test_file)
            os.rmdir(temp_dir)


# =============================================================================
# TESTES DA FILA TCBQueue
# =============================================================================

class TestTCBQueue(unittest.TestCase):
    """Testes para a fila de tarefas."""
    
    def test_push_and_pop(self):
        """Testa inserção e remoção."""
        queue = TCBQueue()
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=5, prio_s=5)
        t2 = TCB(id=2, RGB=[0, 255, 0], inicio=0, duracao=3, prio_s=5)
        
        queue.push_back(t1)
        queue.push_back(t2)
        
        self.assertEqual(len(queue), 2)
        
        popped = queue.pop_front()
        self.assertEqual(popped.id, 1)
        self.assertEqual(len(queue), 1)
    
    def test_remove_specific(self):
        """Testa remoção de elemento específico."""
        queue = TCBQueue()
        t1 = TCB(id=1, RGB=[255, 0, 0], inicio=0, duracao=5, prio_s=5)
        t2 = TCB(id=2, RGB=[0, 255, 0], inicio=0, duracao=3, prio_s=5)
        t3 = TCB(id=3, RGB=[0, 0, 255], inicio=0, duracao=4, prio_s=5)
        
        queue.push_back(t1)
        queue.push_back(t2)
        queue.push_back(t3)
        
        queue.remove(t2)
        
        self.assertEqual(len(queue), 2)
        ids = [t.id for t in queue]
        self.assertNotIn(2, ids)
    
    def test_is_empty(self):
        """Testa verificação de fila vazia."""
        queue = TCBQueue()
        self.assertTrue(queue.is_empty())
        
        queue.push_back(TCB(id=1, RGB=[0, 0, 0], inicio=0, duracao=1, prio_s=1))
        self.assertFalse(queue.is_empty())
    
    def test_iteration(self):
        """Testa iteração sobre a fila."""
        queue = TCBQueue()
        for i in range(5):
            queue.push_back(TCB(id=i, RGB=[0, 0, 0], inicio=0, duracao=1, prio_s=1))
        
        ids = [t.id for t in queue]
        self.assertEqual(ids, [0, 1, 2, 3, 4])


# =============================================================================
# RUNNER PRINCIPAL
# =============================================================================

def run_all_tests():
    """Executa todos os testes e exibe relatório."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Adiciona todas as classes de teste
    test_classes = [
        TestHexToRGB,
        TestParseEvents,
        TestFileOperations,
        TestFIFOScheduler,
        TestSRTFScheduler,
        TestPriorityScheduler,
        TestRoundRobinScheduler,
        TestPRIOPEnvScheduler,
        TestSimulator,
        TestIOEvents,
        TestRandomGeneration,
        TestTCBQueue,
    ]
    
    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))
    
    # Executa os testes
    print("=" * 70)
    print("🧪 SUITE DE TESTES - SIMULADOR DE ESCALONAMENTO")
    print("=" * 70)
    print()
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Relatório final
    print()
    print("=" * 70)
    print("📊 RELATÓRIO FINAL")
    print("=" * 70)
    print(f"  ✅ Testes executados: {result.testsRun}")
    print(f"  ❌ Falhas: {len(result.failures)}")
    print(f"  💥 Erros: {len(result.errors)}")
    print(f"  ⏭️  Ignorados: {len(result.skipped)}")
    print()
    
    if result.wasSuccessful():
        print("🎉 TODOS OS TESTES PASSARAM!")
    else:
        print("⚠️  ALGUNS TESTES FALHARAM:")
        for test, trace in result.failures:
            print(f"    ❌ {test}")
        for test, trace in result.errors:
            print(f"    💥 {test}")
    
    print("=" * 70)
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
