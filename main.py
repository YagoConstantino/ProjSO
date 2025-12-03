import tkinter as tk
from tkinter import (
    filedialog, Canvas, Label, Frame, 
    Toplevel, Entry, Button, Text, messagebox
)

from config_loader import load_simulation_config
from scheduler import FIFOScheduler, SRTFScheduler, PriorityScheduler, RoundRobinScheduler
from simulador import Simulator
import random
import os
import sys

# Configurar PATH do Ghostscript embutido (para executável PyInstaller)
def setup_ghostscript_path():
    """Adiciona o Ghostscript embutido ao PATH se existir."""
    if getattr(sys, 'frozen', False):
        # Executável PyInstaller
        bundle_dir = sys._MEIPASS
    else:
        # Script Python normal
        bundle_dir = os.path.dirname(os.path.abspath(__file__))
    
    gs_bin_path = os.path.join(bundle_dir, 'ghostscript', 'bin')
    
    if os.path.exists(gs_bin_path):
        # Adiciona ao PATH
        os.environ['PATH'] = gs_bin_path + os.pathsep + os.environ.get('PATH', '')
        print(f"✓ Ghostscript embutido encontrado: {gs_bin_path}")
        
        # Configura GS_LIB (necessário para o Ghostscript funcionar)
        gs_lib_path = os.path.join(bundle_dir, 'ghostscript', 'lib')
        if os.path.exists(gs_lib_path):
            os.environ['GS_LIB'] = gs_lib_path
            print(f"✓ GS_LIB configurado: {gs_lib_path}")
        
        return True
    return False

# Configura o Ghostscript ao iniciar
setup_ghostscript_path()

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
        self.geometry("1000x650")

        self.simulator: Simulator | None = None
        self.loaded_tasks = []  # Lista de tarefas carregadas para edição
        self.current_algo = None
        self.current_quantum = None

        # --- Janelas popup (para evitar múltiplas instâncias) ---
        self.create_window: Toplevel | None = None
        self.task_window: Toplevel | None = None
        self.edit_window: Toplevel | None = None
        
        # --- Layout da UI ---
        # Frame para os controles (primeira linha)
        control_frame = Frame(self, pady=5)
        control_frame.pack(fill=tk.X)

        self.btn_load = tk.Button(control_frame, text="📂 Carregar", command=self.load_file)
        self.btn_load.pack(side=tk.LEFT, padx=5)
        
        self.btn_edit = tk.Button(control_frame, text="✏️ Editar Tarefas", command=self.open_edit_tasks_window, state=tk.DISABLED)
        self.btn_edit.pack(side=tk.LEFT, padx=5)
        
        self.btn_step = tk.Button(control_frame, text="▶ Passo", command=self.do_step, state=tk.DISABLED)
        self.btn_step.pack(side=tk.LEFT, padx=5)
        
        self.btn_run = tk.Button(control_frame, text="⏩ Executar Tudo", command=self.run_all, state=tk.DISABLED)
        self.btn_run.pack(side=tk.LEFT, padx=5)
        
        self.btn_reset = tk.Button(control_frame, text="🔄 Reiniciar", command=self.reset_simulation, state=tk.DISABLED)
        self.btn_reset.pack(side=tk.LEFT, padx=5)

        # Frame para controles secundários (segunda linha)
        control_frame2 = Frame(self, pady=5)
        control_frame2.pack(fill=tk.X)

        # Botão "Criar TXT"
        self.btn_create = tk.Button(control_frame2, text="📝 Criar TXT", command=self.open_create_txt_window)
        self.btn_create.pack(side=tk.LEFT, padx=5)
        
        # Botão "Gerar Teste Aleatório"
        self.btn_random = tk.Button(control_frame2, text="🎲 Teste Aleatório", command=self.generate_random_test, bg="#FFD700")
        self.btn_random.pack(side=tk.LEFT, padx=5)
        
        # Botão "Estatísticas"
        self.btn_stats = tk.Button(control_frame2, text="📊 Estatísticas", command=self.show_statistics, state=tk.DISABLED)
        self.btn_stats.pack(side=tk.LEFT, padx=5)
        
        # Botão "Exportar Gantt"
        self.btn_export_gantt = tk.Button(control_frame2, text="💾 Salvar PNG", command=self.export_gantt_ps, state=tk.DISABLED)
        self.btn_export_gantt.pack(side=tk.LEFT, padx=5)
        self.btn_export_svg = tk.Button(control_frame2, text="🖼️ Salvar SVG", command=self.export_gantt_svg, state=tk.DISABLED)
        self.btn_export_svg.pack(side=tk.LEFT, padx=5)

        
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

       # ===== SCROLLABLE GANTT CONTAINER =====
        gantt_container = Frame(self)
        gantt_container.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

        # Canvas dentro de um frame próprio
        self.gantt_canvas = Canvas(gantt_container, bg="white")
        self.gantt_canvas.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)

        # Scrollbar vertical
        vbar = tk.Scrollbar(gantt_container, orient=tk.VERTICAL)
        vbar.pack(side=tk.RIGHT, fill=tk.Y)
        vbar.config(command=self.gantt_canvas.yview)

        # Scrollbar horizontal
        hbar = tk.Scrollbar(self, orient=tk.HORIZONTAL)
        hbar.pack(side=tk.BOTTOM, fill=tk.X)
        hbar.config(command=self.gantt_canvas.xview)

        # Vincular scroll do canvas
        self.gantt_canvas.config(
            yscrollcommand=vbar.set,
            xscrollcommand=hbar.set,
            scrollregion=(0, 0, 2000, 2000)
        )




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

            # Salva configuração para edição posterior
            self.current_algo = algo_name
            self.current_quantum = quantum
            self.loaded_tasks = tasks

            # Instancia o escalonador com quantum (se aplicável)
            scheduler = scheduler_class(quantum=quantum) if quantum else scheduler_class()
            self.simulator = Simulator(scheduler, tasks)
            
            self.lbl_algo_name.config(text=f"Algoritmo: {algo_name}" + (f" (Q={quantum})" if quantum else ""))

            self.btn_step.config(state=tk.NORMAL)
            self.btn_run.config(state=tk.NORMAL)
            self.btn_edit.config(state=tk.NORMAL)
            self.btn_reset.config(state=tk.NORMAL)
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

        self.btn_export_svg.config(state=tk.NORMAL)

    def reset_simulation(self):
        """Reinicia a simulação com as tarefas atuais (editadas ou não)."""
        if not self.loaded_tasks:
            messagebox.showwarning("Aviso", "Nenhuma configuração carregada.")
            return
        
        try:
            # Recria cópias limpas das tarefas
            from copy import deepcopy
            fresh_tasks = []
            for task in self.loaded_tasks:
                # Cria uma nova tarefa com os mesmos parâmetros
                from tasks import TCB
                new_task = TCB(
                    id=task.id,
                    RGB=task.RGB,
                    inicio=task.inicio,
                    duracao=task.duracao,
                    prio_s=task.prio_s,
                    io_events=list(task.io_events) if task.io_events else [],
                    ml_events=list(task.ml_events) if task.ml_events else [],
                    mu_events=list(task.mu_events) if task.mu_events else []
                )
                fresh_tasks.append(new_task)
            
            # Atualiza loaded_tasks com cópias frescas
            self.loaded_tasks = fresh_tasks
            
            # Recria o simulador
            scheduler_class = SCHEDULER_FACTORY.get(self.current_algo)
            if scheduler_class:
                scheduler = scheduler_class(quantum=self.current_quantum) if self.current_quantum else scheduler_class()
                self.simulator = Simulator(scheduler, self.loaded_tasks)
                
                self.btn_step.config(state=tk.NORMAL)
                self.btn_run.config(state=tk.NORMAL)
                self.btn_stats.config(state=tk.DISABLED)
                self.btn_export_gantt.config(state=tk.DISABLED)
                self.btn_export_svg.config(state=tk.DISABLED)
                
                self.update_tasks_table(self.loaded_tasks)
                self.update_ui()
                messagebox.showinfo("Reiniciado", "Simulação reiniciada com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao reiniciar simulação:\n{e}")

    def open_edit_tasks_window(self):
        """Abre janela para editar tarefas carregadas."""
        if not self.loaded_tasks:
            messagebox.showwarning("Aviso", "Nenhuma tarefa carregada para editar.")
            return
        
        if self.edit_window and self.edit_window.winfo_exists():
            self.edit_window.lift()
            return
        
        self.edit_window = Toplevel(self)
        self.edit_window.title("✏️ Editar Tarefas e Configuração")
        self.edit_window.geometry("800x600")
        
        # Frame de configuração do algoritmo
        config_frame = Frame(self.edit_window, padx=10, pady=10, bg="#E8F4F8")
        config_frame.pack(fill=tk.X)
        
        Label(config_frame, text="Configuração:", font=("Arial", 11, "bold"), bg="#E8F4F8").grid(row=0, column=0, sticky=tk.W)
        
        Label(config_frame, text="Algoritmo:", bg="#E8F4F8").grid(row=0, column=1, padx=(20, 5))
        self.edit_algo_var = tk.StringVar(value=self.current_algo)
        algo_combo = tk.OptionMenu(config_frame, self.edit_algo_var, "FIFO", "FCFS", "SRTF", "PRIO", "PRIOP", "RR")
        algo_combo.grid(row=0, column=2, padx=5)
        
        Label(config_frame, text="Quantum:", bg="#E8F4F8").grid(row=0, column=3, padx=(20, 5))
        self.edit_quantum_entry = Entry(config_frame, width=5)
        self.edit_quantum_entry.grid(row=0, column=4, padx=5)
        self.edit_quantum_entry.insert(0, str(self.current_quantum or 0))
        
        # Frame da lista de tarefas
        list_frame = Frame(self.edit_window, padx=10, pady=5)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        Label(list_frame, text="Tarefas (clique duas vezes para editar):", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        # Treeview para lista de tarefas
        from tkinter import ttk
        columns = ("ID", "Cor", "Chegada", "Duração", "Prioridade", "I/O", "ML", "MU")
        self.tasks_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=12)
        
        for col in columns:
            self.tasks_tree.heading(col, text=col)
            if col in ["I/O", "ML", "MU"]:
                self.tasks_tree.column(col, width=100, anchor=tk.CENTER)
            else:
                self.tasks_tree.column(col, width=80, anchor=tk.CENTER)
        
        scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tasks_tree.yview)
        self.tasks_tree.configure(yscrollcommand=scrollbar.set)
        
        self.tasks_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Popula a lista
        self._populate_tasks_tree()
        
        # Bind double-click para edição
        self.tasks_tree.bind("<Double-1>", self._edit_task_dialog)
        
        # Frame de botões
        btn_frame = Frame(self.edit_window, padx=10, pady=10)
        btn_frame.pack(fill=tk.X)
        
        Button(btn_frame, text="➕ Adicionar Tarefa", command=self._add_task_dialog).pack(side=tk.LEFT, padx=5)
        Button(btn_frame, text="🗑️ Remover Selecionada", command=self._remove_selected_task).pack(side=tk.LEFT, padx=5)
        Button(btn_frame, text="✅ Aplicar e Salvar", command=self._apply_edits_to_file, bg="#4CAF50", fg="white").pack(side=tk.RIGHT, padx=5)
        Button(btn_frame, text="❌ Cancelar", command=self.edit_window.destroy).pack(side=tk.RIGHT, padx=5)

    def _populate_tasks_tree(self):
        """Popula a treeview com as tarefas atuais."""
        for item in self.tasks_tree.get_children():
            self.tasks_tree.delete(item)
        
        for task in sorted(self.loaded_tasks, key=lambda t: t.id):
            io_str = ",".join([f"{t}-{d}" for t, d in task.io_events]) if task.io_events else ""
            ml_str = ",".join([str(t) for t in task.ml_events]) if task.ml_events else ""
            mu_str = ",".join([str(t) for t in task.mu_events]) if task.mu_events else ""
            cor_str = f"{task.RGB[0]:02x}{task.RGB[1]:02x}{task.RGB[2]:02x}"
            
            self.tasks_tree.insert("", tk.END, values=(
                task.id, cor_str, task.inicio, task.duracao, task.prio_s, io_str, ml_str, mu_str
            ))

    def _edit_task_dialog(self, event=None):
        """Abre diálogo para editar a tarefa selecionada."""
        selection = self.tasks_tree.selection()
        if not selection:
            return
        
        item = selection[0]
        values = self.tasks_tree.item(item, "values")
        task_id = values[0]
        
        # Encontra a tarefa
        task = next((t for t in self.loaded_tasks if str(t.id) == str(task_id)), None)
        if not task:
            return
        
        self._open_task_edit_dialog(task, item)

    def _add_task_dialog(self):
        """Abre diálogo para adicionar nova tarefa."""
        from tasks import TCB
        
        # Encontra próximo ID disponível
        max_id = max([t.id if isinstance(t.id, int) else 0 for t in self.loaded_tasks], default=0)
        new_id = max_id + 1
        
        # Gera cor hexadecimal aleatória
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        
        # Cria nova tarefa com valores padrão
        new_task = TCB(
            id=new_id,
            RGB=[r, g, b],
            inicio=0,
            duracao=1,
            prio_s=5,
            io_events=[],
            ml_events=[],
            mu_events=[]
        )
        self.loaded_tasks.append(new_task)
        self._populate_tasks_tree()
        
        # Abre diálogo de edição para a nova tarefa
        self._open_task_edit_dialog(new_task, None)

    def _open_task_edit_dialog(self, task, tree_item):
        """Abre diálogo de edição para uma tarefa."""
        dialog = Toplevel(self.edit_window)
        dialog.title(f"Editar Tarefa {task.id}")
        dialog.geometry("450x400")
        dialog.transient(self.edit_window)
        dialog.grab_set()
        
        form = Frame(dialog, padx=20, pady=20)
        form.pack(fill=tk.BOTH, expand=True)
        
        # Campos de edição
        Label(form, text="ID:", font=("Arial", 10, "bold")).grid(row=0, column=0, sticky=tk.W, pady=5)
        id_entry = Entry(form, width=20)
        id_entry.grid(row=0, column=1, sticky=tk.EW, pady=5)
        id_entry.insert(0, str(task.id))
        
        Label(form, text="Cor (hex):", font=("Arial", 10)).grid(row=1, column=0, sticky=tk.W, pady=5)
        cor_entry = Entry(form, width=20)
        cor_entry.grid(row=1, column=1, sticky=tk.EW, pady=5)
        cor_entry.insert(0, f"{task.RGB[0]:02x}{task.RGB[1]:02x}{task.RGB[2]:02x}")
        Label(form, text="Ex: ff0000 ou FF0000", font=("Arial", 8, "italic")).grid(row=1, column=2, sticky=tk.W, padx=5)
        
        Label(form, text="Chegada:", font=("Arial", 10)).grid(row=2, column=0, sticky=tk.W, pady=5)
        chegada_entry = Entry(form, width=20)
        chegada_entry.grid(row=2, column=1, sticky=tk.EW, pady=5)
        chegada_entry.insert(0, str(task.inicio))
        
        Label(form, text="Duração:", font=("Arial", 10)).grid(row=3, column=0, sticky=tk.W, pady=5)
        duracao_entry = Entry(form, width=20)
        duracao_entry.grid(row=3, column=1, sticky=tk.EW, pady=5)
        duracao_entry.insert(0, str(task.duracao))
        
        Label(form, text="Prioridade:", font=("Arial", 10)).grid(row=4, column=0, sticky=tk.W, pady=5)
        prio_entry = Entry(form, width=20)
        prio_entry.grid(row=4, column=1, sticky=tk.EW, pady=5)
        prio_entry.insert(0, str(task.prio_s))
        
        Label(form, text="I/O:", font=("Arial", 10)).grid(row=5, column=0, sticky=tk.W, pady=5)
        io_entry = Entry(form, width=20)
        io_entry.grid(row=5, column=1, sticky=tk.EW, pady=5)
        io_str = ",".join([f"{t}-{d}" for t, d in task.io_events]) if task.io_events else ""
        io_entry.insert(0, io_str)
        Label(form, text="Ex: 2-1,4-2", font=("Arial", 8, "italic")).grid(row=5, column=2, sticky=tk.W, padx=5)
        
        Label(form, text="ML (Mutex Lock):", font=("Arial", 10)).grid(row=6, column=0, sticky=tk.W, pady=5)
        ml_entry = Entry(form, width=20)
        ml_entry.grid(row=6, column=1, sticky=tk.EW, pady=5)
        ml_str = ",".join([str(t) for t in task.ml_events]) if task.ml_events else ""
        ml_entry.insert(0, ml_str)
        Label(form, text="Ex: 1,3", font=("Arial", 8, "italic")).grid(row=6, column=2, sticky=tk.W, padx=5)
        
        Label(form, text="MU (Mutex Unlock):", font=("Arial", 10)).grid(row=7, column=0, sticky=tk.W, pady=5)
        mu_entry = Entry(form, width=20)
        mu_entry.grid(row=7, column=1, sticky=tk.EW, pady=5)
        mu_str = ",".join([str(t) for t in task.mu_events]) if task.mu_events else ""
        mu_entry.insert(0, mu_str)
        Label(form, text="Ex: 2,4", font=("Arial", 8, "italic")).grid(row=7, column=2, sticky=tk.W, padx=5)
        
        form.columnconfigure(1, weight=1)
        
        def save_changes():
            try:
                # Valida e atualiza ID
                new_id = id_entry.get().strip()
                task.id = int(new_id) if new_id.isdigit() else new_id
                
                # Valida e atualiza cor hexadecimal
                cor_hex = cor_entry.get().strip()
                try:
                    from config_loader import hex_to_rgb
                    task.RGB = hex_to_rgb(cor_hex)
                except ValueError as ve:
                    messagebox.showerror("Erro", f"Cor inválida: {ve}", parent=dialog)
                    return
                
                # Valida e atualiza outros campos numéricos
                task.inicio = int(chegada_entry.get())
                task.duracao = int(duracao_entry.get())
                task.prio_s = int(prio_entry.get())
                
                # Parse I/O events
                io_text = io_entry.get().strip()
                task.io_events = []
                if io_text:
                    for part in io_text.split(","):
                        if "-" in part:
                            t, d = part.split("-")
                            task.io_events.append((int(t), int(d)))
                
                # Parse ML events
                ml_text = ml_entry.get().strip()
                task.ml_events = []
                if ml_text:
                    task.ml_events = [int(x) for x in ml_text.split(",") if x.strip()]
                
                # Parse MU events
                mu_text = mu_entry.get().strip()
                task.mu_events = []
                if mu_text:
                    task.mu_events = [int(x) for x in mu_text.split(",") if x.strip()]
                
                self._populate_tasks_tree()
                dialog.destroy()
                messagebox.showinfo("Sucesso", "Tarefa atualizada com sucesso!", parent=self.edit_window)
                
            except ValueError as e:
                messagebox.showerror("Erro", f"Valor inválido: {e}", parent=dialog)
        
        Button(form, text="💾 Salvar Alterações", command=save_changes, bg="#4CAF50", fg="white", 
               font=("Arial", 10, "bold")).grid(row=8, column=0, columnspan=3, pady=20, sticky=tk.EW)

    def _remove_selected_task(self):
        """Remove a tarefa selecionada da lista."""
        selection = self.tasks_tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione uma tarefa para remover.", parent=self.edit_window)
            return
        
        item = selection[0]
        values = self.tasks_tree.item(item, "values")
        task_id = values[0]
        
        # Confirma remoção
        resposta = messagebox.askyesno("Confirmar", f"Deseja realmente remover a tarefa {task_id}?", parent=self.edit_window)
        if not resposta:
            return
        
        # Remove da lista
        self.loaded_tasks = [t for t in self.loaded_tasks if str(t.id) != str(task_id)]
        self._populate_tasks_tree()
        messagebox.showinfo("Sucesso", f"Tarefa {task_id} removida!", parent=self.edit_window)

    def _apply_edits_to_file(self):
        """Salva as alterações de volta no arquivo TXT."""
        try:
            # Atualiza algoritmo e quantum
            self.current_algo = self.edit_algo_var.get()
            quantum_text = self.edit_quantum_entry.get().strip()
            self.current_quantum = int(quantum_text) if quantum_text and quantum_text != "0" else None
            
            # Pede caminho do arquivo
            filepath = filedialog.asksaveasfilename(
                defaultextension=".txt",
                filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
                initialfile="configuracao_editada.txt",
                parent=self.edit_window
            )
            
            if not filepath:
                return
            
            # Gera conteúdo do arquivo
            content = f"{self.current_algo};{self.current_quantum or 0}\n"
            content += "#id;cor_hex;ingresso;duracao;prioridade;eventos\n"
            
            for task in sorted(self.loaded_tasks, key=lambda t: t.id):
                # Formata linha da tarefa
                cor_hex = f"{task.RGB[0]:02x}{task.RGB[1]:02x}{task.RGB[2]:02x}"
                line = f"t{task.id:02d}" if isinstance(task.id, int) else str(task.id)
                line += f";{cor_hex};{task.inicio};{task.duracao};{task.prio_s}"
                
                # Adiciona eventos (I/O, ML, MU)
                eventos = []
                if task.io_events:
                    eventos.extend([f"IO:{t}-{d}" for t, d in task.io_events])
                if task.ml_events:
                    eventos.extend([f"ML:{t}" for t in task.ml_events])
                if task.mu_events:
                    eventos.extend([f"MU:{t}" for t in task.mu_events])
                
                if eventos:
                    line += ";" + ";".join(eventos)
                
                content += line + "\n"
            
            # Salva arquivo
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            
            messagebox.showinfo("Sucesso", f"Alterações salvas em:\n{filepath}", parent=self.edit_window)
            
            # Fecha janela de edição
            self.edit_window.destroy()
            self.edit_window = None
            
            # Pergunta se deseja carregar o arquivo editado
            resposta = messagebox.askyesno("Carregar", "Deseja carregar o arquivo editado agora?")
            if resposta:
                # Carrega o arquivo
                algo_name, quantum_val, tasks = load_simulation_config(filepath)
                scheduler_class = SCHEDULER_FACTORY.get(algo_name)
                if scheduler_class:
                    self.current_algo = algo_name
                    self.current_quantum = quantum_val
                    self.loaded_tasks = tasks
                    
                    scheduler = scheduler_class(quantum=quantum_val) if quantum_val else scheduler_class()
                    self.simulator = Simulator(scheduler, tasks)
                    
                    self.lbl_algo_name.config(text=f"Algoritmo: {algo_name}" + (f" (Q={quantum_val})" if quantum_val else ""))
                    self.btn_step.config(state=tk.NORMAL)
                    self.btn_run.config(state=tk.NORMAL)
                    self.btn_edit.config(state=tk.NORMAL)
                    self.btn_reset.config(state=tk.NORMAL)
                    self.btn_stats.config(state=tk.DISABLED)
                    self.btn_export_gantt.config(state=tk.DISABLED)
                    
                    self.update_tasks_table(tasks)
                    self.update_ui()
            
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar alterações:\n{e}", parent=self.edit_window)

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
        
        # Estatísticas de Mutex (se houver)
        if stats.get('mutex_info') and stats['mutex_info']['total_waits'] > 0:
            Label(summary_frame, text="", bg="#E8F4F8").pack()  # Espaçamento
            Label(summary_frame, text="🔒 Estatísticas de Mutex:", font=("Arial", 12, "bold"), bg="#E8F4F8").pack(anchor=tk.W, padx=10)
            Label(summary_frame, text=f"Total de Bloqueios por Mutex: {stats['mutex_info']['total_waits']}", 
                  font=("Arial", 11), bg="#E8F4F8").pack(anchor=tk.W, padx=20)
            Label(summary_frame, text=f"Tempo Total de Espera por Mutex: {stats['mutex_info']['total_wait_time']}", 
                  font=("Arial", 11), bg="#E8F4F8").pack(anchor=tk.W, padx=20)
            Label(summary_frame, text=f"Tempo Médio de Espera por Mutex: {stats['avg_mutex_wait']:.2f}", 
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
        has_mutex_data = stats.get('mutex_info') and stats['mutex_info']['total_waits'] > 0
        if has_mutex_data:
            header = f"{'ID':<6} {'Chegada':<10} {'Término':<10} {'Turnaround':<12} {'Espera':<10} {'Resposta':<10} {'Ativações':<10} {'MutexWait':<10} {'MutexCnt':<8}\n"
            stats_text.insert(tk.END, header)
            stats_text.insert(tk.END, "=" * 100 + "\n")
        else:
            header = f"{'ID':<6} {'Chegada':<10} {'Término':<10} {'Turnaround':<12} {'Espera':<10} {'Resposta':<10} {'Ativações':<10}\n"
            stats_text.insert(tk.END, header)
            stats_text.insert(tk.END, "=" * 85 + "\n")
        
        # Dados das tarefas
        for task_stat in sorted(stats['tasks'], key=lambda x: x['id']):
            if has_mutex_data:
                line = f"{task_stat['id']:<6} {task_stat['arrival']:<10} {task_stat['completion']:<10} " \
                       f"{task_stat['turnaround_time']:<12} {task_stat['waiting_time']:<10} " \
                       f"{task_stat['response_time']:<10} {task_stat['activations']:<10} " \
                       f"{task_stat.get('mutex_wait_time', 0):<10} {task_stat.get('mutex_wait_count', 0):<8}\n"
            else:
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
                
                # Estatísticas de Mutex (se houver)
                has_mutex_data = stats.get('mutex_info') and stats['mutex_info']['total_waits'] > 0
                if has_mutex_data:
                    f.write("ESTATÍSTICAS DE MUTEX:\n")
                    f.write(f"  Total de Bloqueios por Mutex: {stats['mutex_info']['total_waits']}\n")
                    f.write(f"  Tempo Total de Espera por Mutex: {stats['mutex_info']['total_wait_time']}\n")
                    f.write(f"  Tempo Médio de Espera por Mutex: {stats['avg_mutex_wait']:.2f}\n\n")
                
                f.write("=" * 100 + "\n")
                if has_mutex_data:
                    f.write(f"{'ID':<6} {'Chegada':<10} {'Término':<10} {'Turnaround':<12} {'Espera':<10} {'Resposta':<10} {'Ativações':<10} {'MutexWait':<10} {'MutexCnt':<8}\n")
                else:
                    f.write(f"{'ID':<6} {'Chegada':<10} {'Término':<10} {'Turnaround':<12} {'Espera':<10} {'Resposta':<10} {'Ativações':<10}\n")
                f.write("=" * 100 + "\n")
                
                for task_stat in sorted(stats['tasks'], key=lambda x: x['id']):
                    if has_mutex_data:
                        f.write(f"{task_stat['id']:<6} {task_stat['arrival']:<10} {task_stat['completion']:<10} "
                               f"{task_stat['turnaround_time']:<12} {task_stat['waiting_time']:<10} "
                               f"{task_stat['response_time']:<10} {task_stat['activations']:<10} "
                               f"{task_stat.get('mutex_wait_time', 0):<10} {task_stat.get('mutex_wait_count', 0):<8}\n")
                    else:
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
        entry_quantum.insert(0, "2")
        
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
        entry_io_prob.insert(0, "0")
        
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
                content += "#id;cor_hex;ingresso;duracao;prioridade;io_events\n"
                
                for i in range(num_tasks):
                    task_id = i + 1
                    
                    # Gera cor hexadecimal aleatória
                    r = random.randint(0, 255)
                    g = random.randint(0, 255)
                    b = random.randint(0, 255)
                    cor_hex = f"{r:02x}{g:02x}{b:02x}"
                    
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
                    
                    line = f"t{task_id:02d};{cor_hex};{ingresso};{duracao};{prioridade}"
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
                            # Salva configuração para edição posterior
                            self.current_algo = algo_name
                            self.current_quantum = quantum_val
                            self.loaded_tasks = tasks
                            
                            scheduler = scheduler_class(quantum=quantum_val) if quantum_val else scheduler_class()
                            self.simulator = Simulator(scheduler, tasks)
                            self.lbl_algo_name.config(text=f"Algoritmo: {algo_name}" + (f" (Q={quantum_val})" if quantum_val else ""))
                            self.btn_step.config(state=tk.NORMAL)
                            self.btn_run.config(state=tk.NORMAL)
                            self.btn_edit.config(state=tk.NORMAL)
                            self.btn_reset.config(state=tk.NORMAL)
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

