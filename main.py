import tkinter as tk
from tkinter import (
    filedialog, Canvas, Label, Frame, 
    Toplevel, Entry, Button, Text, messagebox
)

from config_loader import load_simulation_config
from scheduler import FIFOScheduler, SRTFScheduler, PriorityScheduler, RoundRobinScheduler
from simulador import Simulator
import random

# Mapeamento de nomes de algoritmos para classes de escalonadores
SCHEDULER_FACTORY = {
    "FIFO": FIFOScheduler,
    "FCFS": FIFOScheduler,
    "SRTF": SRTFScheduler,
    "PRIO": PriorityScheduler,
    "PRIOP": PriorityScheduler,
    "RR": RoundRobinScheduler,
}

class App(tk.Tk):
    """
    Aplicação principal do simulador de escalonamento de processos.
    Interface gráfica construída com Tkinter.
    """
    
    def __init__(self):
        super().__init__()
        self.title("Simulador de Escalonamento de Processos")
        self.geometry("900x600")

        self.simulator: Simulator | None = None

        # --- Janelas popup (para evitar múltiplas instâncias) ---
        self.create_window: Toplevel | None = None
        self.task_window: Toplevel | None = None
        
        # --- Layout da UI ---
        # Frame para os controles
        control_frame = Frame(self, pady=10)
        control_frame.pack(fill=tk.X)

        self.btn_load = tk.Button(control_frame, text="Carregar Configuração", command=self.load_file)
        self.btn_load.pack(side=tk.LEFT, padx=10)
        
        self.btn_step = tk.Button(control_frame, text="Próximo Passo", command=self.do_step, state=tk.DISABLED)
        self.btn_step.pack(side=tk.LEFT, padx=5)
        
        self.btn_run = tk.Button(control_frame, text="Executar Tudo", command=self.run_all, state=tk.DISABLED)
        self.btn_run.pack(side=tk.LEFT, padx=5)

        # Botão "Criar TXT"
        self.btn_create = tk.Button(control_frame, text="Criar TXT", command=self.open_create_txt_window)
        self.btn_create.pack(side=tk.LEFT, padx=5)
        
        # Botão "Gerar Teste Aleatório"
        self.btn_random = tk.Button(control_frame, text="🎲 Teste Aleatório", command=self.generate_random_test, bg="#FFD700")
        self.btn_random.pack(side=tk.LEFT, padx=5)
        
        # Botão "Estatísticas"
        self.btn_stats = tk.Button(control_frame, text="📊 Estatísticas", command=self.show_statistics, state=tk.DISABLED)
        self.btn_stats.pack(side=tk.LEFT, padx=5)
        
        # Botão "Exportar Gantt"
        self.btn_export_gantt = tk.Button(control_frame, text="💾 Salvar Gantt", command=self.export_gantt_ps, state=tk.DISABLED)
        self.btn_export_gantt.pack(side=tk.LEFT, padx=5)
        
        # Frame para exibir o status
        status_frame = Frame(self, pady=5)
        status_frame.pack(fill=tk.X)
        self.lbl_time = Label(status_frame, text="Tempo: 0")
        self.lbl_time.pack(side=tk.LEFT, padx=10)
        self.lbl_current_task = Label(status_frame, text="Executando: Nenhuma")
        self.lbl_current_task.pack(side=tk.LEFT, padx=10)
        self.lbl_ready_queue = Label(status_frame, text="Fila de Prontos: []")
        self.lbl_ready_queue.pack(side=tk.LEFT, padx=10)

        self.lbl_algo_name = Label(status_frame, text="Algoritmo: N/A")
        self.lbl_algo_name.pack(side=tk.LEFT, padx=10)

        # Frame para a tabela de tarefas carregadas
        table_frame = Frame(self, pady=5)
        table_frame.pack(fill=tk.BOTH, expand=False, padx=10)
        
        Label(table_frame, text="Tarefas Carregadas:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        # Texto com scroll para exibir as tarefas
        table_text_frame = Frame(table_frame)
        table_text_frame.pack(fill=tk.BOTH, expand=False)
        
        table_scrollbar = tk.Scrollbar(table_text_frame)
        table_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tasks_table = Text(table_text_frame, height=6, font=("Courier", 9), 
                                yscrollcommand=table_scrollbar.set, state=tk.DISABLED, 
                                bg="#F5F5F5")
        self.tasks_table.pack(fill=tk.BOTH, expand=True)
        table_scrollbar.config(command=self.tasks_table.yview)

        # Canvas para o Gráfico de Gantt
        self.gantt_canvas = Canvas(self, bg="white", scrollregion=(0, 0, 2000, 400))
        self.gantt_canvas.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        # Adicionar scrollbar horizontal
        hbar = tk.Scrollbar(self, orient=tk.HORIZONTAL)
        hbar.pack(side=tk.BOTTOM, fill=tk.X)
        hbar.config(command=self.gantt_canvas.xview)
        self.gantt_canvas.config(xscrollcommand=hbar.set)



    def load_file(self):
        """Carrega um arquivo de configuração e inicializa o simulador."""
        filepath = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if not filepath:
            return
        
        try:
            algo_name, quantum, tasks = load_simulation_config(filepath)
            scheduler_class = SCHEDULER_FACTORY.get(algo_name)
            if not scheduler_class:
                messagebox.showerror("Erro", f"Algoritmo '{algo_name}' não suportado.")
                self.lbl_algo_name.config(text="Algoritmo: Erro") 
                return

            # Instancia o escalonador com quantum (se aplicável)
            scheduler = scheduler_class(quantum=quantum) if quantum else scheduler_class()
            self.simulator = Simulator(scheduler, tasks)
            
            self.lbl_algo_name.config(text=f"Algoritmo: {algo_name}" + (f" (Q={quantum})" if quantum else ""))

            self.btn_step.config(state=tk.NORMAL)
            self.btn_run.config(state=tk.NORMAL)
            self.btn_stats.config(state=tk.DISABLED)
            self.btn_export_gantt.config(state=tk.DISABLED)
            
            # Atualiza a tabela de tarefas
            self.update_tasks_table(tasks)
            
            self.update_ui()
            messagebox.showinfo("Sucesso", f"Arquivo carregado.\nAlgoritmo: {algo_name}\nTarefas: {len(tasks)}")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao carregar o arquivo:\n{e}")
            self.lbl_algo_name.config(text="Algoritmo: N/A")

    def update_tasks_table(self, tasks):
        """Atualiza a tabela mostrando as tarefas carregadas."""
        self.tasks_table.config(state=tk.NORMAL)
        self.tasks_table.delete("1.0", tk.END)
        
        # Cabeçalho
        header = f"{'ID':<8} {'Cor':<5} {'Chegada':<9} {'Duração':<9} {'Prioridade':<11} {'I/O Events':<30}\n"
        self.tasks_table.insert(tk.END, header)
        self.tasks_table.insert(tk.END, "=" * 80 + "\n")
        
        # Dados das tarefas
        for task in sorted(tasks, key=lambda t: t.id):
            io_str = ""
            if task.io_events:
                io_str = ", ".join([f"{t}-{d}" for t, d in task.io_events])
            
            line = f"{task.id:<8} {task.RGB[0]:02x}{task.RGB[1]:02x}{task.RGB[2]:02x} " \
                   f"{task.inicio:<9} {task.duracao:<9} {task.prio_s:<11} {io_str:<30}\n"
            self.tasks_table.insert(tk.END, line)
        
        self.tasks_table.config(state=tk.DISABLED)

    def do_step(self):
        if self.simulator:
            self.simulator.step()
            self.update_ui()
            
            # Verifica se a simulação terminou
            if self.simulator.is_finished():
                self.btn_step.config(state=tk.DISABLED)
                self.btn_run.config(state=tk.DISABLED)
                self.btn_stats.config(state=tk.NORMAL)
                self.btn_export_gantt.config(state=tk.NORMAL)
                messagebox.showinfo("Simulação Completa", "A simulação foi concluída!")
                self.show_statistics()


    def run_all(self):
        """Executa a simulação completa até o fim."""
        if self.simulator:
            self.simulator.run_full()
            self.update_ui()
            self.btn_step.config(state=tk.DISABLED)
            self.btn_run.config(state=tk.DISABLED)
            self.btn_stats.config(state=tk.NORMAL)
            self.btn_export_gantt.config(state=tk.NORMAL)
            messagebox.showinfo("Simulação Completa", "A simulação foi concluída com sucesso!")
            self.show_statistics()


    def update_ui(self):
        if not self.simulator:
            return
        
        # Atualiza labels de status
        self.lbl_time.config(text=f"Tempo: {self.simulator.time}")
        
        current_id = self.simulator.current_task.id if self.simulator.current_task else "Nenhuma"
        self.lbl_current_task.config(text=f"Executando: {current_id}")
        
        ready_ids = [t.id for t in self.simulator.ready_queue]
        self.lbl_ready_queue.config(text=f"Fila de Prontos: {ready_ids}")
        
        self.draw_gantt()
    
    def draw_gantt(self):
        """Desenha o gráfico de Gantt mostrando a execução das tarefas."""
        self.gantt_canvas.delete("all")
        if not self.simulator or not self.simulator.all_tasks:
            return

        task_ids = sorted([t.id for t in self.simulator.all_tasks], reverse=True)
        task_y_positions = {task_id: i * 40 + 20 for i, task_id in enumerate(task_ids)}

        # Desenha labels das tarefas
        for task_id, y in task_y_positions.items():
            self.gantt_canvas.create_text(20, y, anchor=tk.W, text=f"T{task_id}")
        
        block_width = 20
        left_margin = 50

        max_time = -1
        gantt_data = getattr(self.simulator, "gantt_data", []) or []
        
        # Rastreia quais tarefas já iniciaram
        tasks_started = set()

        # Desenha os blocos de execução
        for entry in gantt_data:
            if len(entry) == 4:
                time, task_id, rgb_color, state = entry
            else:
                # Compatibilidade com formato antigo
                time, task_id, rgb_color = entry
                state = "EXEC"
            
            if time > max_time:
                max_time = time
                
            if task_id != "IDLE":
                tasks_started.add(task_id)
                if task_id not in task_y_positions:
                    continue
                y_pos = task_y_positions[task_id]
                x_start = left_margin + time * block_width
                
                # Define cor (sempre usa a cor da tarefa)
                color = f"#{rgb_color[0]:02x}{rgb_color[1]:02x}{rgb_color[2]:02x}"
                
                # Desenha retângulo com borda preta padrão
                self.gantt_canvas.create_rectangle(
                    x_start, y_pos - 15, x_start + block_width, y_pos + 15,
                    fill=color, outline="black", width=1
                )

        if max_time < 0:
            max_time = getattr(self.simulator, "time", 1)

        # Desenha eixo do tempo
        total_time = max_time + 1
        x_end = left_margin + total_time * block_width
        max_y = max(task_y_positions.values()) if task_y_positions else 0
        
        eixo_y = max_y + 40  
        self.gantt_canvas.create_line(left_margin, eixo_y, x_end, eixo_y, width=2)

        # Marcadores de tempo
        for t in range(1, total_time + 1):
            x_block_start = left_margin + (t - 1) * block_width
            x_block_end = x_block_start + block_width
            x_center = x_block_start + block_width / 2

            self.gantt_canvas.create_line(x_block_start, eixo_y - 6, x_block_start, eixo_y + 6)
            self.gantt_canvas.create_line(x_block_end, eixo_y - 6, x_block_end, eixo_y + 6)

            tag = f"time_label_{t}"
            self.gantt_canvas.create_text(x_center, eixo_y + 18, text=str(t), anchor=tk.N, font=("Arial", 9), tags=(tag,))

        self.gantt_canvas.config(scrollregion=(0, 0, x_end + 50, eixo_y + 40))

    def export_gantt_ps(self):
        """Exporta o gráfico de Gantt como arquivo PostScript (sem dependências externas)."""
        if not self.simulator:
            messagebox.showwarning("Aviso", "Nenhuma simulação carregada.")
            return
        
        try:
            # Solicita local para salvar
            filepath = filedialog.asksaveasfilename(
                defaultextension=".ps",
                filetypes=[("PostScript Files", "*.ps"), ("All Files", "*.*")],
                initialfile="gantt_chart.ps"
            )
            
            if not filepath:
                return
            
            # Atualiza a região de scroll para capturar todo o conteúdo
            self.gantt_canvas.update_idletasks()
            
            # Salva usando PostScript nativo do Tkinter (sem dependências externas)
            self.gantt_canvas.postscript(file=filepath, colormode='color')
            
            messagebox.showinfo("Sucesso", 
                f"Gantt exportado para:\n{filepath}\n\n"
                "Arquivo PostScript (.ps) pode ser:\n"
                "• Visualizado com leitores PS/PDF\n"
                "• Convertido para PNG online\n"
                "• Impresso diretamente")
        
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar Gantt:\n{e}")

    # Função para criar tarefas novas

    def open_create_txt_window(self):
        """Abre a primeira janela para definir Configs (Nome, Algo, Quantum)."""
        if self.create_window and self.create_window.winfo_exists():
            self.create_window.lift()
            return
            
        self.create_window = Toplevel(self)
        self.create_window.title("1. Criar Configuração")
        self.create_window.geometry("300x150")

        form_frame = Frame(self.create_window, padx=10, pady=10)
        form_frame.pack(fill=tk.BOTH, expand=True)

        Label(form_frame, text="Nome do Arquivo:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.entry_filename = Entry(form_frame)
        self.entry_filename.grid(row=0, column=1, sticky=tk.EW, padx=5)
        self.entry_filename.insert(0, "nova_config.txt")

        Label(form_frame, text="Algoritmo:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.entry_algo = Entry(form_frame)
        self.entry_algo.grid(row=1, column=1, sticky=tk.EW, padx=5)
        self.entry_algo.insert(0, "PRIOp")

        Label(form_frame, text="Quantum:").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.entry_quantum = Entry(form_frame)
        self.entry_quantum.grid(row=2, column=1, sticky=tk.EW, padx=5)
        self.entry_quantum.insert(0, "3")

        btn_next = Button(form_frame, text="Próximo (Add Tarefas)", command=self.process_config_and_open_tasks)
        btn_next.grid(row=3, column=0, columnspan=2, pady=10)

        form_frame.columnconfigure(1, weight=1)

    def process_config_and_open_tasks(self):
        """Lê os dados da Janela 1, fecha-a e abre a Janela 2."""
        filename = self.entry_filename.get()
        algo = self.entry_algo.get()
        quantum = self.entry_quantum.get()

        if not filename or not algo:
            messagebox.showwarning("Campos Vazios", "Nome do arquivo e Algoritmo são obrigatórios.", parent=self.create_window)
            return

        if not quantum:
            quantum = "0" # Default se vazio

        if self.create_window:
            self.create_window.destroy()
            self.create_window = None

        self.open_add_tasks_window(filename, algo, quantum)

    def open_add_tasks_window(self, filename, algo, quantum):
        """Abre a segunda janela para adicionar tarefas."""
        if self.task_window and self.task_window.winfo_exists():
            self.task_window.lift()
            return
            
        self.new_tasks_list = [] # Reseta a lista de tarefas
        self.task_window = Toplevel(self)
        self.task_window.title(f"2. Adicionar Tarefas para '{filename}'")
        self.task_window.geometry("500x600")

        # --- Frame do Formulário da Tarefa ---
        form_frame = Frame(self.task_window, padx=10, pady=10)
        form_frame.pack(fill=tk.X)

        labels = ["ID:", "Cor (0-N):", "Ingresso:", "Duração:", "Prioridade:", "I/O (Opcional):"]
        self.task_entries = {}

        for i, text in enumerate(labels):
            Label(form_frame, text=text).grid(row=i, column=0, sticky=tk.W, pady=2)
            entry = Entry(form_frame)
            entry.grid(row=i, column=1, sticky=tk.EW, padx=5)
            self.task_entries[text.split(" ")[0]] = entry
        
        form_frame.columnconfigure(1, weight=1)
        
        # Exemplo de I/O
        Label(form_frame, text="(Ex: IO:2-1 ou IO:1-2;IO:4-1)", font=("Arial", 8, "italic")).grid(row=5, column=2, sticky=tk.W, padx=5)

        # --- Frame de Botões ---
        btn_frame = Frame(self.task_window, pady=5)
        btn_frame.pack(fill=tk.X, padx=10)
        
        self.btn_add_task = Button(btn_frame, text="Salvar Tarefa", command=self.add_task_to_list)
        self.btn_add_task.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        self.btn_save_file = Button(btn_frame, text="Finalizar e Salvar TXT", command=lambda: self.save_txt_file(filename, algo, quantum))
        self.btn_save_file.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=5)

        # --- Frame de Display das Tarefas ---
        display_frame = Frame(self.task_window, padx=10, pady=10)
        display_frame.pack(fill=tk.BOTH, expand=True)

        Label(display_frame, text="Tarefas Adicionadas:").pack(anchor=tk.W)
        self.tasks_display = Text(display_frame, height=10, bg="#f0f0f0", state=tk.DISABLED)
        self.tasks_display.pack(fill=tk.BOTH, expand=True)

    def add_task_to_list(self):
        """Coleta dados dos entries da Janela 2, valida e adiciona na lista/display."""
        try:
            id_val = self.task_entries["ID:"].get()
            cor_val = self.task_entries["Cor"].get()
            ingresso_val = self.task_entries["Ingresso:"].get()
            duracao_val = self.task_entries["Duração:"].get()
            pri_val = self.task_entries["Prioridade:"].get()
            io_val = self.task_entries["I/O"].get()

            if not all([id_val, cor_val, ingresso_val, duracao_val, pri_val]):
                messagebox.showwarning("Campos Obrigatórios", 
                                       "ID, Cor, Ingresso, Duração e Prioridade são obrigatórios.", 
                                       parent=self.task_window)
                return
            
            # Validações
            try:
                task_id = int(id_val)
                if task_id < 0:
                    raise ValueError("ID deve ser não-negativo")
                
                ingresso = int(ingresso_val)
                if ingresso < 0:
                    raise ValueError("Tempo de ingresso deve ser >= 0")
                
                duracao = int(duracao_val)
                if duracao <= 0:
                    raise ValueError("Duração deve ser > 0")
                
                prioridade = int(pri_val)
                
            except ValueError as ve:
                messagebox.showerror("Valor Inválido", str(ve), parent=self.task_window)
                return

            task_parts = [id_val, cor_val, ingresso_val, duracao_val, pri_val]
            if io_val:
                task_parts.append(io_val)
            
            task_line = ";".join(task_parts)
            self.new_tasks_list.append(task_line)
            
            # Atualiza o display
            self.tasks_display.config(state=tk.NORMAL)
            self.tasks_display.insert(tk.END, task_line + "\n")
            self.tasks_display.config(state=tk.DISABLED)

            # Limpa os campos
            self.task_entries["ID:"].delete(0, tk.END)
            self.task_entries["Cor"].delete(0, tk.END)
            self.task_entries["Ingresso:"].delete(0, tk.END)
            self.task_entries["Duração:"].delete(0, tk.END)
            self.task_entries["Prioridade:"].delete(0, tk.END)
            self.task_entries["I/O"].delete(0, tk.END)
            
            # Foca no ID para a próxima tarefa
            self.task_entries["ID:"].focus()

        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao adicionar tarefa: {e}", parent=self.task_window)

    def save_txt_file(self, filename, algo, quantum):
        """Formata o conteúdo e abre a janela de 'Salvar Como'."""
        
        header = f"{algo};{quantum}"
        comment = "#id;cor_id;ingresso;duracao;prioridade;"
        
        content = header + "\n"
        content += comment + "\n"
        content += "\n".join(self.new_tasks_list)

        filepath = filedialog.asksaveasfilename(
            initialfile=filename,
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            parent=self.task_window
        )

        if not filepath:
            return # Usuário cancelou

        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            
            messagebox.showinfo("Sucesso", f"Arquivo '{filepath}' salvo com sucesso!", parent=self.task_window)
            
            if self.task_window:
                self.task_window.destroy()
                self.task_window = None

        except Exception as e:
            messagebox.showerror("Erro ao Salvar", f"Não foi possível salvar o arquivo:\n{e}", parent=self.task_window)

    def show_statistics(self):
        """Exibe janela com estatísticas da simulação concluída."""
        if not self.simulator:
            messagebox.showwarning("Aviso", "Nenhuma simulação carregada.")
            return
        
        if not self.simulator.is_finished():
            messagebox.showwarning("Aviso", "Execute a simulação completa antes de ver as estatísticas.")
            return
        
        stats = self.simulator.get_statistics()
        
        # Cria janela de estatísticas
        stats_window = Toplevel(self)
        stats_window.title("📊 Estatísticas da Simulação")
        stats_window.geometry("700x500")
        
        # Frame superior com médias
        summary_frame = Frame(stats_window, bg="#E8F4F8", padx=20, pady=15)
        summary_frame.pack(fill=tk.X)
        
        Label(summary_frame, text="Estatísticas Gerais", font=("Arial", 14, "bold"), bg="#E8F4F8").pack()
        Label(summary_frame, text=f"Tempo Médio de Turnaround: {stats['avg_turnaround']:.2f}", 
              font=("Arial", 11), bg="#E8F4F8").pack(anchor=tk.W, padx=20)
        Label(summary_frame, text=f"Tempo Médio de Espera: {stats['avg_waiting']:.2f}", 
              font=("Arial", 11), bg="#E8F4F8").pack(anchor=tk.W, padx=20)
        Label(summary_frame, text=f"Tempo Médio de Resposta: {stats['avg_response']:.2f}", 
              font=("Arial", 11), bg="#E8F4F8").pack(anchor=tk.W, padx=20)
        
        # Frame inferior com tabela de tarefas
        table_frame = Frame(stats_window, padx=10, pady=10)
        table_frame.pack(fill=tk.BOTH, expand=True)
        
        Label(table_frame, text="Estatísticas por Tarefa", font=("Arial", 12, "bold")).pack(anchor=tk.W)
        
        # Área de texto com scroll
        text_frame = Frame(table_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(text_frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        stats_text = Text(text_frame, font=("Courier", 10), yscrollcommand=scrollbar.set)
        stats_text.pack(fill=tk.BOTH, expand=True)
        scrollbar.config(command=stats_text.yview)
        
        # Cabeçalho da tabela
        header = f"{'ID':<6} {'Chegada':<10} {'Término':<10} {'Turnaround':<12} {'Espera':<10} {'Resposta':<10} {'Ativações':<10}\n"
        stats_text.insert(tk.END, header)
        stats_text.insert(tk.END, "=" * 85 + "\n")
        
        # Dados das tarefas
        for task_stat in sorted(stats['tasks'], key=lambda x: x['id']):
            line = f"{task_stat['id']:<6} {task_stat['arrival']:<10} {task_stat['completion']:<10} " \
                   f"{task_stat['turnaround_time']:<12} {task_stat['waiting_time']:<10} " \
                   f"{task_stat['response_time']:<10} {task_stat['activations']:<10}\n"
            stats_text.insert(tk.END, line)
        
        stats_text.config(state=tk.DISABLED)
        
        # Botão de exportar
        Button(stats_window, text="Exportar Estatísticas", 
               command=lambda: self.export_statistics(stats)).pack(pady=10)
    
    def export_statistics(self, stats):
        """Exporta estatísticas para arquivo de texto."""
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            initialfile="estatisticas.txt"
        )
        
        if not filepath:
            return
        
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("=" * 80 + "\n")
                f.write("ESTATÍSTICAS DA SIMULAÇÃO\n")
                f.write("=" * 80 + "\n\n")
                
                f.write("MÉDIAS GERAIS:\n")
                f.write(f"  Tempo Médio de Turnaround: {stats['avg_turnaround']:.2f}\n")
                f.write(f"  Tempo Médio de Espera: {stats['avg_waiting']:.2f}\n")
                f.write(f"  Tempo Médio de Resposta: {stats['avg_response']:.2f}\n\n")
                
                f.write("=" * 80 + "\n")
                f.write(f"{'ID':<6} {'Chegada':<10} {'Término':<10} {'Turnaround':<12} {'Espera':<10} {'Resposta':<10} {'Ativações':<10}\n")
                f.write("=" * 80 + "\n")
                
                for task_stat in sorted(stats['tasks'], key=lambda x: x['id']):
                    f.write(f"{task_stat['id']:<6} {task_stat['arrival']:<10} {task_stat['completion']:<10} "
                           f"{task_stat['turnaround_time']:<12} {task_stat['waiting_time']:<10} "
                           f"{task_stat['response_time']:<10} {task_stat['activations']:<10}\n")
            
            messagebox.showinfo("Sucesso", f"Estatísticas exportadas para '{filepath}'")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao exportar estatísticas:\n{e}")
    
    def generate_random_test(self):
        """Gera um arquivo de teste com tarefas e parâmetros aleatórios."""
        # Janela de configuração do teste aleatório
        random_window = Toplevel(self)
        random_window.title("🎲 Gerar Teste Aleatório")
        random_window.geometry("400x350")
        
        form_frame = Frame(random_window, padx=20, pady=20)
        form_frame.pack(fill=tk.BOTH, expand=True)
        
        Label(form_frame, text="Configuração do Teste Aleatório", font=("Arial", 12, "bold")).grid(row=0, column=0, columnspan=2, pady=10)
        
        # Campos de configuração
        Label(form_frame, text="Número de Tarefas:").grid(row=1, column=0, sticky=tk.W, pady=5)
        entry_num_tasks = Entry(form_frame)
        entry_num_tasks.grid(row=1, column=1, sticky=tk.EW, padx=5)
        entry_num_tasks.insert(0, "5")
        
        Label(form_frame, text="Algoritmo:").grid(row=2, column=0, sticky=tk.W, pady=5)
        entry_algo = Entry(form_frame)
        entry_algo.grid(row=2, column=1, sticky=tk.EW, padx=5)
        entry_algo.insert(0, "SRTF")
        
        Label(form_frame, text="Quantum (0=N/A):").grid(row=3, column=0, sticky=tk.W, pady=5)
        entry_quantum = Entry(form_frame)
        entry_quantum.grid(row=3, column=1, sticky=tk.EW, padx=5)
        entry_quantum.insert(0, "0")
        
        Label(form_frame, text="Duração Min:").grid(row=4, column=0, sticky=tk.W, pady=5)
        entry_dur_min = Entry(form_frame)
        entry_dur_min.grid(row=4, column=1, sticky=tk.EW, padx=5)
        entry_dur_min.insert(0, "1")
        
        Label(form_frame, text="Duração Max:").grid(row=5, column=0, sticky=tk.W, pady=5)
        entry_dur_max = Entry(form_frame)
        entry_dur_max.grid(row=5, column=1, sticky=tk.EW, padx=5)
        entry_dur_max.insert(0, "10")
        
        Label(form_frame, text="Chegada Max:").grid(row=6, column=0, sticky=tk.W, pady=5)
        entry_arrival_max = Entry(form_frame)
        entry_arrival_max.grid(row=6, column=1, sticky=tk.EW, padx=5)
        entry_arrival_max.insert(0, "20")
        
        Label(form_frame, text="Prob. I/O (%):").grid(row=7, column=0, sticky=tk.W, pady=5)
        entry_io_prob = Entry(form_frame)
        entry_io_prob.grid(row=7, column=1, sticky=tk.EW, padx=5)
        entry_io_prob.insert(0, "30")
        
        form_frame.columnconfigure(1, weight=1)
        
        def generate():
            try:
                num_tasks = int(entry_num_tasks.get())
                algo = entry_algo.get().upper()
                quantum = entry_quantum.get()
                dur_min = int(entry_dur_min.get())
                dur_max = int(entry_dur_max.get())
                arrival_max = int(entry_arrival_max.get())
                io_prob = int(entry_io_prob.get())
                
                if num_tasks <= 0 or dur_min <= 0 or dur_max < dur_min:
                    raise ValueError("Valores inválidos")
                
                # Gera o conteúdo
                content = f"{algo};{quantum}\n"
                content += "#id;cor_id;ingresso;duracao;prioridade;io_events\n"
                
                for i in range(num_tasks):
                    task_id = i + 1
                    cor_id = i  # Cores distintas sequenciais: 0, 1, 2, 3...
                    ingresso = random.randint(0, arrival_max)
                    duracao = random.randint(dur_min, dur_max)
                    prioridade = random.randint(1, 10)
                    
                    # Gera eventos de I/O aleatórios
                    io_events = ""
                    if random.randint(0, 100) < io_prob:
                        num_io_events = random.randint(1, 2)
                        io_list = []
                        for _ in range(num_io_events):
                            io_time = random.randint(1, duracao - 1)
                            io_dur = random.randint(1, 3)
                            io_list.append(f"IO:{io_time}-{io_dur}")
                        io_events = ";".join(io_list)
                    
                    line = f"t{task_id:02d};{cor_id};{ingresso};{duracao};{prioridade}"
                    if io_events:
                        line += f";{io_events}"
                    content += line + "\n"
                
                # Salva o arquivo
                filepath = filedialog.asksaveasfilename(
                    defaultextension=".txt",
                    filetypes=[("Text Files", "*.txt")],
                    initialfile=f"teste_aleatorio_{num_tasks}tasks.txt"
                )
                
                if filepath:
                    with open(filepath, "w", encoding="utf-8") as f:
                        f.write(content)
                    
                    messagebox.showinfo("Sucesso", f"Teste aleatório gerado:\n{filepath}\n\nDeseja carregar agora?")
                    random_window.destroy()
                    
                    # Carrega automaticamente
                    try:
                        algo_name, quantum_val, tasks = load_simulation_config(filepath)
                        scheduler_class = SCHEDULER_FACTORY.get(algo_name)
                        if scheduler_class:
                            scheduler = scheduler_class(quantum=quantum_val) if quantum_val else scheduler_class()
                            self.simulator = Simulator(scheduler, tasks)
                            self.lbl_algo_name.config(text=f"Algoritmo: {algo_name}" + (f" (Q={quantum_val})" if quantum_val else ""))
                            self.btn_step.config(state=tk.NORMAL)
                            self.btn_run.config(state=tk.NORMAL)
                            self.btn_stats.config(state=tk.DISABLED)
                            self.btn_export_gantt.config(state=tk.DISABLED)
                            self.update_tasks_table(tasks)
                            self.update_ui()
                    except Exception as e:
                        messagebox.showerror("Erro", f"Erro ao carregar teste gerado:\n{e}")
            
            except ValueError as e:
                messagebox.showerror("Erro", f"Valores inválidos:\n{e}", parent=random_window)
            except Exception as e:
                messagebox.showerror("Erro", f"Erro ao gerar teste:\n{e}", parent=random_window)
        
        Button(form_frame, text="Gerar e Carregar", command=generate, bg="#4CAF50", fg="white", font=("Arial", 10, "bold")).grid(row=8, column=0, columnspan=2, pady=20, sticky=tk.EW)


if __name__ == "__main__":
    app = App()
    app.mainloop()

