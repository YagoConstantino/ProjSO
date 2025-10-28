import tkinter as tk
# <--- ALTERAÇÃO: Importando mais componentes do tkinter ---
from tkinter import (
    filedialog, Canvas, Label, Frame, 
    Toplevel, Entry, Button, Text, messagebox
)
# <--- FIM DA ALTERAÇÃO ---

# Supondo que seus outros arquivos (config_loader, scheduler, simulador) 
# estão no mesmo diretório ou acessíveis.
from config_loader import load_simulation_config
from scheduler import FIFOScheduler, SRTFScheduler, PriorityScheduler
from simulador import Simulator


SCHEDULER_FACTORY = {
    "FIFO": FIFOScheduler,
    "FSCS": FIFOScheduler,
    "SRTF": SRTFScheduler,
    "PRIO": PriorityScheduler,
    "PRIOP": PriorityScheduler,
}

class App(tk.Tk):
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

        #Adicionando o botão "Criar TXT" ---
        self.btn_create = tk.Button(control_frame, text="Criar TXT", command=self.open_create_txt_window)
        self.btn_create.pack(side=tk.LEFT, padx=5)
        
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

        # Canvas para o Gráfico de Gantt
        self.gantt_canvas = Canvas(self, bg="white", scrollregion=(0, 0, 2000, 400))
        self.gantt_canvas.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        # Adicionar scrollbar horizontal
        hbar = tk.Scrollbar(self, orient=tk.HORIZONTAL)
        hbar.pack(side=tk.BOTTOM, fill=tk.X)
        hbar.config(command=self.gantt_canvas.xview)
        self.gantt_canvas.config(xscrollcommand=hbar.set)


    def load_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if not filepath:
            return
        
        try:
            algo_name, quantum, tasks = load_simulation_config(filepath)
            scheduler_class = SCHEDULER_FACTORY.get(algo_name)
            if not scheduler_class:
                print(f"Erro: Algoritmo '{algo_name}' não suportado.")
                self.lbl_algo_name.config(text="Algoritmo: Erro") 
                return

            self.simulator = Simulator(scheduler_class(), tasks)
            
            self.lbl_algo_name.config(text=f"Algoritmo: {algo_name}")

            self.btn_step.config(state=tk.NORMAL)
            self.btn_run.config(state=tk.NORMAL)
            self.update_ui()
            print(f"Arquivo '{filepath}' carregado. Algoritmo: {algo_name}, Tarefas: {len(tasks)}")
        except Exception as e:
            print(f"Erro ao carregar o arquivo: {e}")
            self.lbl_algo_name.config(text="Algoritmo: N/A")

    def do_step(self):
        if self.simulator:
            self.simulator.step()
            self.update_ui()

    def run_all(self):
        if self.simulator:
            self.simulator.run_full()
            self.update_ui()
            self.btn_step.config(state=tk.DISABLED)
            self.btn_run.config(state=tk.DISABLED)

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
        self.gantt_canvas.delete("all")
        if not self.simulator or not self.simulator.all_tasks:
            return

        task_ids = sorted([t.id for t in self.simulator.all_tasks],reverse= True)
        task_y_positions = {task_id: i * 40 + 20 for i, task_id in enumerate(task_ids)}

        for task_id, y in task_y_positions.items():
            self.gantt_canvas.create_text(20, y, anchor=tk.W, text=f"T{task_id}")
        
        block_width = 20
        left_margin = 50

        max_time = -1
        gantt_data = getattr(self.simulator, "gantt_data", []) or []

        for time, task_id, rgb_color in gantt_data:
            if time > max_time:
                max_time = time
            if task_id != "IDLE":
                if task_id not in task_y_positions:
                    continue
                y_pos = task_y_positions[task_id]
                x_start = left_margin + time * block_width
                color = f"#{rgb_color[0]:02x}{rgb_color[1]:02x}{rgb_color[2]:02x}"
                self.gantt_canvas.create_rectangle(
                    x_start, y_pos - 15, x_start + block_width, y_pos + 15,
                    fill=color, outline="black"
                )

        if max_time < 0:
            max_time = getattr(self.simulator, "time", 1)

        total_time = max_time + 1
        x_end = left_margin + total_time * block_width
        max_y = max(task_y_positions.values()) if task_y_positions else 0
        
        eixo_y = max_y + 40  
        self.gantt_canvas.create_line(left_margin, eixo_y, x_end, eixo_y, width=2)

        for t in range(1, total_time + 1):
            x_block_start = left_margin + (t - 1) * block_width
            x_block_end = x_block_start + block_width
            x_center = x_block_start + block_width / 2

            self.gantt_canvas.create_line(x_block_start, eixo_y - 6, x_block_start, eixo_y + 6)
            self.gantt_canvas.create_line(x_block_end, eixo_y - 6, x_block_end, eixo_y + 6)

            tag = f"time_label_{t}"
            self.gantt_canvas.create_text(x_center, eixo_y + 18, text=str(t), anchor=tk.N, font=("Arial", 9), tags=(tag,))

        self.gantt_canvas.config(scrollregion=(0, 0, x_end + 50, eixo_y + 40))

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



if __name__ == "__main__":
    app = App()
    app.mainloop()

