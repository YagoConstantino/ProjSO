import tkinter as tk
from tkinter import filedialog, Canvas, Label, Frame
from config_loader import load_simulation_config
from scheduler import FIFOScheduler, SRTFScheduler, PriorityScheduler
from simulador import Simulator
from config_loader import load_simulation_config
from scheduler import FIFOScheduler, SRTFScheduler, PriorityScheduler


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

        # Frame para exibir o status
        status_frame = Frame(self, pady=5)
        status_frame.pack(fill=tk.X)
        self.lbl_time = Label(status_frame, text="Tempo: 0")
        self.lbl_time.pack(side=tk.LEFT, padx=10)
        self.lbl_current_task = Label(status_frame, text="Executando: Nenhuma")
        self.lbl_current_task.pack(side=tk.LEFT, padx=10)
        self.lbl_ready_queue = Label(status_frame, text="Fila de Prontos: []")
        self.lbl_ready_queue.pack(side=tk.LEFT, padx=10)

        #Adicionando o label para o nome do algoritmo ---
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
                return

            self.simulator = Simulator(scheduler_class(), tasks)

            # Atualiza o texto do label com o algo_name ---
            self.lbl_algo_name.config(text=f"Algoritmo: {algo_name}")
           

            self.btn_step.config(state=tk.NORMAL)
            self.btn_run.config(state=tk.NORMAL)
            self.update_ui()
            print(f"Arquivo '{filepath}' carregado. Algoritmo: {algo_name}, Tarefas: {len(tasks)}")
        except Exception as e:
            print(f"Erro ao carregar o arquivo: {e}")
            #Reseta o label em caso de falha ---
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

        # Desenha as linhas de base e os IDs das tarefas
        for task_id, y in task_y_positions.items():
            self.gantt_canvas.create_text(20, y, anchor=tk.W, text=f"T{task_id}")
        
         # ----------------- parâmetros do Gantt -----------------
        block_width = 20        # largura de cada unidade de tempo em pixels
        left_margin = 50        # margem esquerda antes do primeiro bloco

        # ----------------- desenha blocos de execução e encontra tempo máximo -----------------
        max_time = -1
        gantt_data = getattr(self.simulator, "gantt_data", []) or []

        for time, task_id, rgb_color in gantt_data:
            if time > max_time:
                max_time = time
            if task_id != "IDLE":
                # garante que a task existe no mapeamento (segurança)
                if task_id not in task_y_positions:
                    continue
                y_pos = task_y_positions[task_id]
                x_start = left_margin + time * block_width
                color = f"#{rgb_color[0]:02x}{rgb_color[1]:02x}{rgb_color[2]:02x}"
                self.gantt_canvas.create_rectangle(
                    x_start, y_pos - 15, x_start + block_width, y_pos + 15,
                    fill=color, outline="black"
                )

                # se não houver dados, usa tempo atual do simulador
        if max_time < 0:
            max_time = getattr(self.simulator, "time", 1)

        total_time = max_time + 1   # número de unidades de tempo a desenhar
        x_end = left_margin + total_time * block_width
        max_y = max(task_y_positions.values()) if task_y_positions else 0

        # ----------------- desenha a linha do tempo / contador embaixo -----------------
        # eixo_y agora fica logo abaixo do último bloco
        eixo_y = max_y + 40  

        # linha principal do eixo X (fica no fim do gráfico)
        # começa na margem esquerda e termina exatamente na borda direita (x_end)
        self.gantt_canvas.create_line(left_margin, eixo_y, x_end, eixo_y, width=2)

        # desenha ticks e rótulos 0..total_time (centralizados nos blocos)
            # percorrer t = 1..total_time (cada t corresponde ao bloco t-1)
        for t in range(1, total_time + 1):
            x_block_start = left_margin + (t - 1) * block_width
            x_block_end = x_block_start + block_width
            x_center = x_block_start + block_width / 2

            # linha no início e no fim do bloco
            self.gantt_canvas.create_line(x_block_start, eixo_y - 6, x_block_start, eixo_y + 6)
            self.gantt_canvas.create_line(x_block_end, eixo_y - 6, x_block_end, eixo_y + 6)

            # texto do tempo (começando em 1), com tag única para cada label
            tag = f"time_label_{t}"
            self.gantt_canvas.create_text(x_center, eixo_y + 18, text=str(t), anchor=tk.N, font=("Arial", 9), tags=(tag,))

        # ----------------- ajusta área de rolagem -----------------
        # adiciona margem extra à direita para o último rótulo caber
        self.gantt_canvas.config(scrollregion=(0, 0, x_end + 50, eixo_y + 40))

if __name__ == "__main__":
    app = App()
    app.mainloop()