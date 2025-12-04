import tkinter as tk
from tkinter import (
    filedialog, Canvas, Label, Frame, 
    Toplevel, Entry, Button, Text, messagebox
)

from config_loader import load_simulation_config
from scheduler import FIFOScheduler, SRTFScheduler, PriorityScheduler, RoundRobinScheduler, PRIOPEnvScheduler, PRIOPEnvTickScheduler
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
    "PRIOPENV": PRIOPEnvScheduler,  # Prioridade com envelhecimento (chegada/término)
    "PRIOPENV-T": PRIOPEnvTickScheduler,  # Prioridade com envelhecimento por tick
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

        self.simulator = None
        self.loaded_tasks = []
        self.original_tasks_data = []  # NOVO: Guarda os dados ORIGINAIS das tarefas (não modificados)
        self.current_algo = None
        self.current_quantum = None
        self.current_alpha = None
        self.current_filepath = None  # NOVO: Guarda o caminho do arquivo carregado

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
        
        # NOVO: Botão Voltar
        self.btn_back = tk.Button(control_frame, text="⏪ Voltar", command=self.do_step_back, state=tk.DISABLED)
        self.btn_back.pack(side=tk.LEFT, padx=5)
        
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
            algo_name, quantum, alpha, tasks = load_simulation_config(filepath)
            scheduler_class = SCHEDULER_FACTORY.get(algo_name)
            if not scheduler_class:
                messagebox.showerror("Erro", f"Algoritmo '{algo_name}' não suportado.")
                self.lbl_algo_name.config(text="Algoritmo: Erro") 
                return

            # Salva configuração para edição posterior
            self.current_algo = algo_name
            self.current_quantum = quantum
            self.current_alpha = alpha
            self.loaded_tasks = tasks
            self.current_filepath = filepath  # NOVO: Salva o caminho
            
            # NOVO: Salva os dados ORIGINAIS das tarefas (para reset correto)
            self._save_original_tasks_data()

            # Instancia o escalonador com parâmetros apropriados
            if algo_name in ("PRIOPENV", "PRIOPENV-T"):
                # PRIOPEnv e PRIOPEnv-T precisam de quantum e alpha
                scheduler = scheduler_class(quantum=quantum or 1, alpha=alpha or 1)
            elif quantum:
                scheduler = scheduler_class(quantum=quantum)
            else:
                scheduler = scheduler_class()
            
            self.simulator = Simulator(scheduler, tasks)
            
            # Atualiza label com informações do algoritmo
            algo_info = f"Algoritmo: {algo_name}"
            if quantum:
                algo_info += f" (Q={quantum})"
            if alpha:
                algo_info += f" (α={alpha})"
            self.lbl_algo_name.config(text=algo_info)

            self.btn_step.config(state=tk.NORMAL)
            self.btn_run.config(state=tk.NORMAL)
            self.btn_edit.config(state=tk.NORMAL)
            self.btn_reset.config(state=tk.NORMAL)
            self.btn_back.config(state=tk.DISABLED)  # NOVO: Inicia desabilitado
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
        
        # Verifica se é PRIOPEnv ou PRIOPEnv-T para mostrar prioridade dinâmica
        is_priopenv = self.current_algo in ("PRIOPENV", "PRIOPENV-T")
        
        # Cabeçalho
        if is_priopenv:
            header = f"{'ID':<6} {'Cor':<8} {'Cheg':<6} {'Dur':<5} {'PrioS':<6} {'PrioD':<6} {'I/O Events':<20}\n"
            self.tasks_table.insert(tk.END, header)
            self.tasks_table.insert(tk.END, "=" * 70 + "\n")
        else:
            header = f"{'ID':<8} {'Cor':<8} {'Chegada':<9} {'Duração':<9} {'Prioridade':<11} {'I/O Events':<30}\n"
            self.tasks_table.insert(tk.END, header)
            self.tasks_table.insert(tk.END, "=" * 80 + "\n")
        
        # Dados das tarefas
        for task in sorted(tasks, key=lambda t: t.id):
            io_str = ", ".join([f"{t}-{d}" for t, d in task.io_events]) if task.io_events else ""
            if is_priopenv:
                line = f"{task.id:<6} {task.RGB[0]:02x}{task.RGB[1]:02x}{task.RGB[2]:02x}  {task.inicio:<6} {task.duracao:<5} {task.prio_s:<6} {task.prio_d:<6} {io_str:<20}\n"
            else:
                line = f"{task.id:<8} {task.RGB[0]:02x}{task.RGB[1]:02x}{task.RGB[2]:02x}  {task.inicio:<9} {task.duracao:<9} {task.prio_s:<11} {io_str:<30}\n"
            self.tasks_table.insert(tk.END, line)
        
        self.tasks_table.config(state=tk.DISABLED)

    def do_step_back(self):
        """Volta um passo na simulação."""
        if self.simulator and self.simulator.can_step_back():
            if self.simulator.step_back():
                self.update_ui()
                
                # Reabilita botões se a simulação não terminou
                if not self.simulator.is_finished():
                    self.btn_step.config(state=tk.NORMAL)
                    self.btn_run.config(state=tk.NORMAL)
                    self.btn_stats.config(state=tk.DISABLED)
                    self.btn_export_gantt.config(state=tk.DISABLED)
                    self.btn_export_svg.config(state=tk.DISABLED)
                
                # Atualiza estado do botão voltar
                self._update_back_button()
        else:
            messagebox.showinfo("Aviso", "Não há passos anteriores para voltar.")

    def _update_back_button(self):
        """Atualiza o estado do botão voltar baseado no histórico."""
        if self.simulator and self.simulator.can_step_back():
            self.btn_back.config(state=tk.NORMAL)
        else:
            self.btn_back.config(state=tk.DISABLED)

    def do_step(self):
        if self.simulator:
            self.simulator.step()
            self.update_ui()
            self._update_back_button()  # NOVO: Atualiza botão voltar
            
            # Verifica se a simulação terminou
            if self.simulator.is_finished():
                self.btn_step.config(state=tk.DISABLED)
                self.btn_run.config(state=tk.DISABLED)
                self.btn_stats.config(state=tk.NORMAL)
                self.btn_export_gantt.config(state=tk.NORMAL)
                self.btn_export_svg.config(state=tk.NORMAL)  # ADICIONADO
                messagebox.showinfo("Simulação Completa", "A simulação foi concluída!")
                self.show_statistics()

    def _save_original_tasks_data(self):
        """Salva os dados originais das tarefas para permitir reset correto."""
        self.original_tasks_data = []
        for task in self.loaded_tasks:
            self.original_tasks_data.append({
                'id': task.id,
                'RGB': list(task.RGB),
                'inicio': task.inicio,
                'duracao': task.duracao,
                'prio_s': task.prio_s,
                'io_events': list(task.io_events) if task.io_events else [],
                'ml_events': list(task.ml_events) if task.ml_events else [],
                'mu_events': list(task.mu_events) if task.mu_events else []
            })

    def reset_simulation(self):
        """Reinicia a simulação com as tarefas ORIGINAIS (preservando I/O, ML, MU)."""
        if not self.original_tasks_data:
            messagebox.showwarning("Aviso", "Nenhuma configuração carregada.")
            return
        
        try:
            from tasks import TCB
            
            # Recria tarefas a partir dos dados ORIGINAIS salvos
            fresh_tasks = []
            for data in self.original_tasks_data:
                new_task = TCB(
                    id=data['id'],
                    RGB=list(data['RGB']),
                    inicio=data['inicio'],
                    duracao=data['duracao'],
                    prio_s=data['prio_s'],
                    io_events=list(data['io_events']),  # Copia da lista ORIGINAL
                    ml_events=list(data['ml_events']),  # Copia da lista ORIGINAL
                    mu_events=list(data['mu_events'])   # Copia da lista ORIGINAL
                )
                fresh_tasks.append(new_task)
            
            # Atualiza loaded_tasks com cópias frescas
            self.loaded_tasks = fresh_tasks
            
            # Recria o simulador
            scheduler_class = SCHEDULER_FACTORY.get(self.current_algo)
            if scheduler_class:
                # Instancia o escalonador com parâmetros apropriados
                if self.current_algo in ("PRIOPENV", "PRIOPENV-T"):
                    scheduler = scheduler_class(quantum=self.current_quantum or 1, alpha=self.current_alpha or 1)
                elif self.current_quantum:
                    scheduler = scheduler_class(quantum=self.current_quantum)
                else:
                    scheduler = scheduler_class()
                
                self.simulator = Simulator(scheduler, self.loaded_tasks)
                
                self.btn_step.config(state=tk.NORMAL)
                self.btn_run.config(state=tk.NORMAL)
                self.btn_back.config(state=tk.DISABLED)  # NOVO: Reset desabilita voltar
                self.btn_stats.config(state=tk.DISABLED)
                self.btn_export_gantt.config(state=tk.DISABLED)
                self.btn_export_svg.config(state=tk.DISABLED)
                
                # Atualiza a tabela de tarefas
                self.update_tasks_table(self.loaded_tasks)
                self.update_ui()
                messagebox.showinfo("Reiniciado", "Simulação reiniciada com sucesso!")
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao reiniciar simulação:\n{e}")

    def open_edit_tasks_window(self):
        """Abre janela ÚNICA para editar tarefas e configuração."""
        if not self.loaded_tasks:
            messagebox.showwarning("Aviso", "Nenhuma tarefa carregada para editar.")
            return
        
        if self.edit_window and self.edit_window.winfo_exists():
            self.edit_window.lift()
            return
        
        self.edit_window = Toplevel(self)
        self.edit_window.title("✏️ Editor de Configuração")
        self.edit_window.geometry("1000x650")  # AUMENTADO: de 850x600 para 950x650
        
        # Frame de configuração do algoritmo
        config_frame = Frame(self.edit_window, padx=10, pady=10, bg="#E8F4F8", relief=tk.RIDGE, bd=2)
        config_frame.pack(fill=tk.X, padx=10, pady=5)
        
        Label(config_frame, text="⚙️ Configuração:", font=("Arial", 11, "bold"), bg="#E8F4F8").grid(row=0, column=0, sticky=tk.W)
        
        Label(config_frame, text="Algoritmo:", bg="#E8F4F8").grid(row=0, column=1, padx=(20, 5))
        self.edit_algo_var = tk.StringVar(value=self.current_algo or "FIFO")
        algo_combo = tk.OptionMenu(config_frame, self.edit_algo_var, "FIFO", "FCFS", "SRTF", "PRIO", "PRIOP", "RR", "PRIOPENV", "PRIOPENV-T")
        algo_combo.grid(row=0, column=2, padx=5)
        
        Label(config_frame, text="Quantum:", bg="#E8F4F8").grid(row=0, column=3, padx=(20, 5))
        self.edit_quantum_entry = Entry(config_frame, width=6)
        self.edit_quantum_entry.grid(row=0, column=4, padx=5)
        self.edit_quantum_entry.insert(0, str(self.current_quantum or ""))
        
        Label(config_frame, text="Alpha:", bg="#E8F4F8").grid(row=0, column=5, padx=(20, 5))
        self.edit_alpha_entry = Entry(config_frame, width=6)
        self.edit_alpha_entry.grid(row=0, column=6, padx=5)
        self.edit_alpha_entry.insert(0, str(self.current_alpha or ""))
        
        # Mostra arquivo atual
        if self.current_filepath:
            Label(config_frame, text=f"📁 {os.path.basename(self.current_filepath)}", bg="#E8F4F8", fg="blue").grid(row=0, column=7, padx=10)
        
        # Frame da lista de tarefas
        list_frame = Frame(self.edit_window, padx=10, pady=5)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10)
        
        Label(list_frame, text="📋 Tarefas (selecione para editar abaixo):", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        from tkinter import ttk
        columns = ("ID", "Cor (Hex)", "Chegada", "Duração", "Prioridade", "I/O", "ML", "MU")
        
        tree_frame = Frame(list_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True)
        
        self.tasks_tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=10)
        for col in columns:
            self.tasks_tree.heading(col, text=col)
            self.tasks_tree.column(col, width=85, anchor=tk.CENTER)
        
        vsb = tk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tasks_tree.yview)
        self.tasks_tree.configure(yscrollcommand=vsb.set)
        self.tasks_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        self._populate_tasks_tree()
        self.tasks_tree.bind("<<TreeviewSelect>>", self._on_tree_select)
        
        # Frame de edição inline
        edit_frame = Frame(self.edit_window, padx=10, pady=10, bg="#FFF8DC", relief=tk.GROOVE, bd=2)
        edit_frame.pack(fill=tk.X, padx=10, pady=5)
        
        Label(edit_frame, text="📝 Editar Tarefa:", font=("Arial", 10, "bold"), bg="#FFF8DC").grid(row=0, column=0, columnspan=16, sticky=tk.W, pady=(0,5))
        
        self.edit_entries = {}
        # MODIFICADO: ID é apenas leitura (disabled), outros campos são editáveis
        fields = [("ID", 4, True), ("Cor", 7, False), ("Chegada", 5, False), ("Duração", 5, False), 
                  ("Prioridade", 5, False), ("I/O", 12, False), ("ML", 8, False), ("MU", 8, False)]
        
        for i, (name, width, readonly) in enumerate(fields):
            Label(edit_frame, text=f"{name}:", bg="#FFF8DC", font=("Arial", 9)).grid(row=1, column=i*2, sticky=tk.E, padx=2)
            entry = Entry(edit_frame, width=width)
            entry.grid(row=1, column=i*2+1, padx=2, pady=3)
            if readonly:
                entry.config(state='readonly', readonlybackground='#E0E0E0')
            self.edit_entries[name] = entry
        
        Button(edit_frame, text="💾 Atualizar", command=self._update_task, bg="#4CAF50", fg="white").grid(row=1, column=16, padx=5)
        
        # Frame de botões de ação
        btn_frame = Frame(self.edit_window, padx=10, pady=10)
        btn_frame.pack(fill=tk.X)
        
        Button(btn_frame, text="➕ Nova Tarefa", command=self._add_task).pack(side=tk.LEFT, padx=5)
        Button(btn_frame, text="🗑️ Remover", command=self._remove_task).pack(side=tk.LEFT, padx=5)
        Button(btn_frame, text="💾 Salvar Arquivo", command=self._save_file_with_dialog, bg="#2196F3", fg="white").pack(side=tk.RIGHT, padx=5)
        Button(btn_frame, text="✅ Aplicar", command=self._apply_edits, bg="#4CAF50", fg="white").pack(side=tk.RIGHT, padx=5)
        Button(btn_frame, text="❌ Cancelar", command=self.edit_window.destroy).pack(side=tk.RIGHT, padx=5)

    def _on_tree_select(self, event=None):
        """Atualiza os campos de edição quando uma tarefa é selecionada na lista."""
        selection = self.tasks_tree.selection()
        if not selection:
            return
        
        values = self.tasks_tree.item(selection[0], "values")
        fields = ["ID", "Cor", "Chegada", "Duração", "Prioridade", "I/O", "ML", "MU"]
        
        for i, name in enumerate(fields):
            entry = self.edit_entries[name]
            # Para campo readonly (ID), precisa habilitar temporariamente
            if name == "ID":
                entry.config(state='normal')
                entry.delete(0, tk.END)
                entry.insert(0, str(values[i]) if i < len(values) else "")
                entry.config(state='readonly')
            else:
                entry.delete(0, tk.END)
                entry.insert(0, str(values[i]) if i < len(values) else "")

    def _update_task(self):
        """Atualiza os dados da tarefa selecionada na lista."""
        selection = self.tasks_tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione uma tarefa.", parent=self.edit_window)
            return
        
        # Pega o ID da treeview (NÃO pode ser alterado)
        task_id = self.tasks_tree.item(selection[0], "values")[0]
        
        # Busca a tarefa pelo ID
        task = None
        for t in self.loaded_tasks:
            if t.id == task_id or str(t.id) == str(task_id):
                task = t
                break
        
        if not task:
            messagebox.showerror("Erro", f"Tarefa {task_id} não encontrada!", parent=self.edit_window)
            return
        
        try:
            # Atualiza cor
            from config_loader import hex_to_rgb
            cor_str = self.edit_entries["Cor"].get().strip()
            task.RGB = hex_to_rgb(cor_str)
            
            # Atualiza parâmetros numéricos
            task.inicio = int(self.edit_entries["Chegada"].get())
            task.duracao = int(self.edit_entries["Duração"].get())
            task.tempo_restante = task.duracao  # Sincroniza tempo_restante
            task.prio_s = int(self.edit_entries["Prioridade"].get())
            task.prio_d = task.prio_s  # Sincroniza prioridade dinâmica
            
            # Atualiza eventos de I/O
            io_text = self.edit_entries["I/O"].get().strip()
            task.io_events = []
            if io_text:
                for part in io_text.split(","):
                    part = part.strip()
                    if "-" in part:
                        t_val, d_val = part.split("-")
                        task.io_events.append((int(t_val.strip()), int(d_val.strip())))
            
            # Atualiza eventos de Mutex Lock
            ml_text = self.edit_entries["ML"].get().strip()
            task.ml_events = []
            if ml_text:
                task.ml_events = [int(x.strip()) for x in ml_text.split(",") if x.strip()]
            
            # Atualiza eventos de Mutex Unlock
            mu_text = self.edit_entries["MU"].get().strip()
            task.mu_events = []
            if mu_text:
                task.mu_events = [int(x.strip()) for x in mu_text.split(",") if x.strip()]
            
            # DEBUG
            print(f"[DEBUG] Tarefa {task.id} atualizada: dur={task.duracao}, prio={task.prio_s}")
            
            # Atualiza a treeview da janela de edição
            self._populate_tasks_tree()
            
            # Atualiza a tabela principal
            self.update_tasks_table(self.loaded_tasks)
            
            # Salva automaticamente no arquivo se existir
            if self.current_filepath:
                self._save_file(self.current_filepath)
                print(f"[DEBUG] Arquivo salvo automaticamente: {self.current_filepath}")
            
            messagebox.showinfo("Sucesso", f"Tarefa {task.id} atualizada!", parent=self.edit_window)
            
        except ValueError as e:
            messagebox.showerror("Erro", f"Valor inválido: {e}", parent=self.edit_window)
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erro", f"Erro ao atualizar: {e}", parent=self.edit_window)

    def _populate_tasks_tree(self):
        """Popula a treeview com as tarefas atuais."""
        for item in self.tasks_tree.get_children():
            self.tasks_tree.delete(item)
        
        for task in sorted(self.loaded_tasks, key=lambda t: t.id if isinstance(t.id, int) else 0):
            io_str = ",".join([f"{t}-{d}" for t, d in task.io_events]) if task.io_events else ""
            ml_str = ",".join([str(t) for t in task.ml_events]) if task.ml_events else ""
            mu_str = ",".join([str(t) for t in task.mu_events]) if task.mu_events else ""
            cor_str = f"{task.RGB[0]:02x}{task.RGB[1]:02x}{task.RGB[2]:02x}"
            
            self.tasks_tree.insert("", tk.END, values=(
                task.id,
                cor_str, 
                task.inicio, 
                task.duracao, 
                task.prio_s, 
                io_str, 
                ml_str, 
                mu_str
            ))

    def _remove_task(self):
        """Remove a tarefa selecionada da lista."""
        selection = self.tasks_tree.selection()
        if not selection:
            messagebox.showwarning("Aviso", "Selecione uma tarefa.", parent=self.edit_window)
            return
        
        task_id = self.tasks_tree.item(selection[0], "values")[0]
        
        # Remove da lista
        self.loaded_tasks = [t for t in self.loaded_tasks if t.id != task_id and str(t.id) != str(task_id)]
        
        # Atualiza treeview
        self._populate_tasks_tree()
        
        # Limpa campos de edição
        for name, entry in self.edit_entries.items():
            if name == "ID":
                entry.config(state='normal')
                entry.delete(0, tk.END)
                entry.config(state='readonly')
            else:
                entry.delete(0, tk.END)
        
        # Atualiza tabela principal
        self.update_tasks_table(self.loaded_tasks)
        
        # Salva automaticamente
        if self.current_filepath:
            self._save_file(self.current_filepath)

    def _save_file(self, filepath=None):
        """Salva as tarefas e configuração atual em um arquivo TXT."""
        if filepath is None:
            initial_file = "config.txt"
            if self.current_filepath:
                initial_file = os.path.basename(self.current_filepath)
            
            filepath = filedialog.asksaveasfilename(
                defaultextension=".txt", 
                filetypes=[("Text Files", "*.txt")], 
                initialfile=initial_file, 
                parent=self.edit_window if self.edit_window else self
            )
        
        if not filepath:
            return False
        
        try:
            # Pega valores do editor se estiver aberto
            if self.edit_window and hasattr(self, 'edit_algo_var'):
                algo = self.edit_algo_var.get()
                quantum = self.edit_quantum_entry.get().strip()
                alpha = self.edit_alpha_entry.get().strip()
            else:
                algo = self.current_algo or "FIFO"
                quantum = str(self.current_quantum) if self.current_quantum else ""
                alpha = str(self.current_alpha) if self.current_alpha else ""
            
            # Cabeçalho
            header_parts = [algo]
            if quantum:
                header_parts.append(quantum)
            if alpha:
                if not quantum:
                    header_parts.append("")
                header_parts.append(alpha)
            
            while header_parts and header_parts[-1] == "":
                header_parts.pop()
            
            header = ";".join(header_parts)
            content = header + "\n"
            content += "#id;cor_hex;ingresso;duracao;prioridade;eventos\n"
            
            # Ordena tarefas pelo ID
            sorted_tasks = sorted(self.loaded_tasks, key=lambda t: t.id if isinstance(t.id, int) else 0)
            
            for task in sorted_tasks:
                # Formata ID
                if isinstance(task.id, int):
                    tid = f"t{task.id:02d}"
                else:
                    tid = f"t{task.id}"
                
                # Formata cor
                cor = f"{task.RGB[0]:02x}{task.RGB[1]:02x}{task.RGB[2]:02x}"
                
                # Monta eventos
                events = []
                if task.io_events:
                    for t_ev, d_ev in task.io_events:
                        events.append(f"IO:{t_ev}-{d_ev}")
                if task.ml_events:
                    for t_ev in task.ml_events:
                        events.append(f"ML:{t_ev}")
                if task.mu_events:
                    for t_ev in task.mu_events:
                        events.append(f"MU:{t_ev}")
                
                # Linha da tarefa
                line = f"{tid};{cor};{task.inicio};{task.duracao};{task.prio_s}"
                if events:
                    line += ";" + ";".join(events)
                content += line + "\n"
            
            # Salva no arquivo
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            
            self.current_filepath = filepath
            return True
            
        except Exception as e:
            print(f"[DEBUG] Erro ao salvar: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _save_file_with_dialog(self):
        """Salva o arquivo com diálogo (chamado pelo botão Salvar Arquivo)."""
        if self._save_file():
            parent = self.edit_window if self.edit_window else self
            messagebox.showinfo("Sucesso", f"Arquivo salvo em:\n{self.current_filepath}", parent=parent)

    def _apply_edits(self):
        """Aplica as edições: salva no TXT, atualiza tarefas no sistema e reinicia simulação."""
        try:
            # DEBUG
            print(f"\n[DEBUG] === APLICANDO EDIÇÕES ===")
            print(f"[DEBUG] loaded_tasks ANTES:")
            for t in self.loaded_tasks:
                print(f"        T{t.id}: inicio={t.inicio}, dur={t.duracao}, prio={t.prio_s}")
            
            # 1. Atualiza configuração do algoritmo
            self.current_algo = self.edit_algo_var.get()
            
            q = self.edit_quantum_entry.get().strip()
            self.current_quantum = int(q) if q else None
            
            a = self.edit_alpha_entry.get().strip()
            self.current_alpha = int(a) if a else None
            
            # 2. Salva no arquivo TXT (se houver arquivo carregado)
            saved = False
            if self.current_filepath:
                saved = self._save_file(self.current_filepath)
                if not saved:
                    if not messagebox.askyesno("Aviso", 
                        "Não foi possível salvar no arquivo original.\nDeseja continuar aplicando as alterações apenas na memória?",
                        parent=self.edit_window):
                        return
            
            # 3. Atualiza label do algoritmo
            algo_info = f"Algoritmo: {self.current_algo}"
            if self.current_quantum:
                algo_info += f" (Q={self.current_quantum})"
            if self.current_alpha:
                algo_info += f" (α={self.current_alpha})"
            self.lbl_algo_name.config(text=algo_info)
            
            # 4. Fecha janela de edição
            self.edit_window.destroy()
            self.edit_window = None
            
            # 5. Recria as tarefas com os valores atualizados (cópia limpa para simulação)
            from tasks import TCB
            fresh_tasks = []
            for task in self.loaded_tasks:
                new_task = TCB(
                    id=task.id,
                    RGB=list(task.RGB),
                    inicio=task.inicio,
                    duracao=task.duracao,
                    prio_s=task.prio_s,
                    io_events=list(task.io_events) if task.io_events else [],
                    ml_events=list(task.ml_events) if task.ml_events else [],
                    mu_events=list(task.mu_events) if task.mu_events else []
                )
                fresh_tasks.append(new_task)
            
            # IMPORTANTE: Atualiza loaded_tasks com as cópias frescas
            self.loaded_tasks = fresh_tasks
            
            # NOVO: Atualiza os dados originais para refletir as edições
            self._save_original_tasks_data()
            
            # DEBUG
            print(f"[DEBUG] loaded_tasks DEPOIS (cópias frescas):")
            for t in self.loaded_tasks:
                print(f"        T{t.id}: inicio={t.inicio}, dur={t.duracao}, prio={t.prio_s}, tempo_restante={t.tempo_restante}")
            
            # 6. Recria o simulador com o novo algoritmo
            scheduler_class = SCHEDULER_FACTORY.get(self.current_algo)
            if scheduler_class:
                if self.current_algo in ("PRIOPENV", "PRIOPENV-T"):
                    scheduler = scheduler_class(
                        quantum=self.current_quantum or 1, 
                        alpha=self.current_alpha or 1
                    )
                elif self.current_quantum:
                    scheduler = scheduler_class(quantum=self.current_quantum)
                else:
                    scheduler = scheduler_class()
                
                self.simulator = Simulator(scheduler, self.loaded_tasks)
                
                # 7. Atualiza UI
                self.btn_step.config(state=tk.NORMAL)
                self.btn_run.config(state=tk.NORMAL)
                self.btn_stats.config(state=tk.DISABLED)
                self.btn_export_gantt.config(state=tk.DISABLED)
                self.btn_export_svg.config(state=tk.DISABLED)
                
                self.update_tasks_table(self.loaded_tasks)
                self.update_ui()
                
                msg = "Configuração aplicada e simulação reiniciada!"
                if saved and self.current_filepath:
                    msg += f"\n\nArquivo atualizado:\n{self.current_filepath}"
                messagebox.showinfo("Sucesso", msg)
            else:
                messagebox.showerror("Erro", f"Algoritmo '{self.current_algo}' não suportado.")
                
        except ValueError as e:
            messagebox.showerror("Erro", f"Valor inválido: {e}", parent=self.edit_window)
        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erro", f"Erro ao aplicar: {e}", parent=self.edit_window)

    def run_all(self):
        """Executa a simulação completa até o fim."""
        if self.simulator:
            self.simulator.run_full()
            self.update_ui()
            self._update_back_button()  # NOVO: Atualiza botão voltar
            self.btn_step.config(state=tk.DISABLED)
            self.btn_run.config(state=tk.DISABLED)
            self.btn_stats.config(state=tk.NORMAL)
            self.btn_export_gantt.config(state=tk.NORMAL)
            self.btn_export_svg.config(state=tk.NORMAL)
            messagebox.showinfo("Simulação Completa", "A simulação foi concluída!")
            self.show_statistics()

    def export_gantt_svg(self):
        if not self.simulator:
            messagebox.showwarning("Aviso", "Nenhuma simulação carregada.")
            return
        filepath = filedialog.asksaveasfilename(defaultextension=".svg", filetypes=[("SVG", "*.svg")], initialfile="gantt.svg")
        if not filepath:
            return
        self.gantt_canvas.update_idletasks()
        bbox = self.gantt_canvas.bbox("all")
        if not bbox:
            messagebox.showerror("Erro", "Nada para exportar.")
            return
        self._save_canvas_as_svg(filepath, *bbox)

    def _save_canvas_as_svg(self, filepath, x0, y0, x1, y1, silent=False):
        import xml.etree.ElementTree as ET
        import xml.dom.minidom as md
        width, height = x1 - x0 + 20, y1 - y0 + 40
        svg = ET.Element("svg", width=str(width), height=str(height), version="1.1", xmlns="http://www.w3.org/2000/svg")
        ET.SubElement(svg, "rect", x="0", y="0", width=str(width), height=str(height), fill="white")
        for item in self.gantt_canvas.find_all():
            itype = self.gantt_canvas.type(item)
            coords = self.gantt_canvas.coords(item)
            adj = [coords[i] - (x0 if i%2==0 else y0) for i in range(len(coords))]
            if itype == "rectangle":
                fill = self.gantt_canvas.itemcget(item, "fill")
                ET.SubElement(svg, "rect", x=str(adj[0]), y=str(adj[1]), width=str(adj[2]-adj[0]), height=str(adj[3]-adj[1]), fill=fill if fill else "none", stroke="black")
            elif itype == "line":
                ET.SubElement(svg, "line", x1=str(adj[0]), y1=str(adj[1]), x2=str(adj[2]), y2=str(adj[3]), stroke="black")
            elif itype == "text":
                txt = self.gantt_canvas.itemcget(item, "text")
                el = ET.SubElement(svg, "text", x=str(adj[0]), y=str(adj[1]), fill="black")
                el.text = txt
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(md.parseString(ET.tostring(svg)).toprettyxml())
        if not silent:
            messagebox.showinfo("Sucesso", f"SVG salvo: {filepath}")

    def export_gantt_ps(self):
        if not self.simulator:
            messagebox.showwarning("Aviso", "Nenhuma simulação carregada.")
            return
        filepath = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG", "*.png")], initialfile="gantt.png")
        if not filepath:
            return
        try:
            from PIL import Image, ImageDraw, ImageFont
            bbox = self.gantt_canvas.bbox("all")
            if not bbox:
                return
            w, h = bbox[2]-bbox[0]+20, bbox[3]-bbox[1]+20
            img = Image.new('RGB', (w, h), 'white')
            draw = ImageDraw.Draw(img)
            try:
                font = ImageFont.truetype("arial.ttf", 12)
            except:
                font = ImageFont.load_default()
            
            task_ids = sorted([t.id for t in self.simulator.all_tasks], reverse=True)
            task_y = {tid: i*40+30 for i, tid in enumerate(task_ids)}
            for tid, y in task_y.items():
                draw.text((10, y-6), f"T{tid}", fill='black', font=font)
            
            for entry in (self.simulator.gantt_data or []):
                time, tid, rgb, state = entry if len(entry)==4 else (*entry, "EXEC")
                if tid != "IDLE" and tid in task_y:
                    y = task_y[tid]
                    x = 50 + time * 20
                    fill = {"EXEC": tuple(rgb), "IO": (191,191,191), "READY": (255,255,255), "MUTEX": (153,50,204)}.get(state, tuple(rgb))
                    draw.rectangle([x, y-15, x+20, y+15], fill=fill, outline=(0,0,0))
            img.save(filepath, 'PNG')
            messagebox.showinfo("Sucesso", f"PNG salvo: {filepath}")
        except ImportError:
            messagebox.showerror("Erro", "Instale Pillow: pip install pillow")

    def show_statistics(self):
        if not self.simulator or not self.simulator.is_finished():
            messagebox.showwarning("Aviso", "Execute a simulação primeiro.")
            return
        stats = self.simulator.get_statistics()
        win = Toplevel(self)
        win.title("📊 Estatísticas")
        win.geometry("600x400")
        
        fr = Frame(win, bg="#E8F4F8", padx=20, pady=15)
        fr.pack(fill=tk.X)
        Label(fr, text="Estatísticas Gerais", font=("Arial", 14, "bold"), bg="#E8F4F8").pack()
        Label(fr, text=f"Turnaround Médio: {stats['avg_turnaround']:.2f}", bg="#E8F4F8").pack(anchor=tk.W)
        Label(fr, text=f"Espera Média: {stats['avg_waiting']:.2f}", bg="#E8F4F8").pack(anchor=tk.W)
        Label(fr, text=f"Resposta Média: {stats['avg_response']:.2f}", bg="#E8F4F8").pack(anchor=tk.W)
        
        txt = Text(win, font=("Courier", 10))
        txt.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        txt.insert(tk.END, f"{'ID':<6}{'Chegada':<10}{'Término':<10}{'Turnaround':<12}{'Espera':<10}\n{'='*50}\n")
        for t in sorted(stats['tasks'], key=lambda x: x['id']):
            txt.insert(tk.END, f"{t['id']:<6}{t['arrival']:<10}{t['completion']:<10}{t['turnaround_time']:<12}{t['waiting_time']:<10}\n")
        txt.config(state=tk.DISABLED)

    def open_create_txt_window(self):
        if self.create_window and self.create_window.winfo_exists():
            self.create_window.lift()
            return
        self.create_window = Toplevel(self)
        self.create_window.title("📝 Criar Configuração")
        self.create_window.geometry("400x500")
        
        fr = Frame(self.create_window, padx=10, pady=10)
        fr.pack(fill=tk.BOTH, expand=True)
        
        Label(fr, text="Algoritmo:").grid(row=0, column=0, sticky=tk.W)
        self.new_algo = Entry(fr)
        self.new_algo.grid(row=0, column=1, sticky=tk.EW)
        self.new_algo.insert(0, "FIFO")
        
        Label(fr, text="Quantum:").grid(row=1, column=0, sticky=tk.W)
        self.new_quantum = Entry(fr)
        self.new_quantum.grid(row=1, column=1, sticky=tk.EW)
        
        Label(fr, text="\nAdicionar Tarefa:", font=("Arial", 10, "bold")).grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=10)
        
        labels = ["ID:", "Cor (hex):", "Chegada:", "Duração:", "Prioridade:"]
        self.new_task_entries = {}
        for i, lbl in enumerate(labels):
            Label(fr, text=lbl).grid(row=3+i, column=0, sticky=tk.W)
            e = Entry(fr)
            e.grid(row=3+i, column=1, sticky=tk.EW)
            self.new_task_entries[lbl] = e
        
        self.new_tasks_list = []
        Button(fr, text="Adicionar", command=self._add_new_task).grid(row=8, column=0, columnspan=2, pady=5)
        
        self.new_tasks_display = Text(fr, height=8)
        self.new_tasks_display.grid(row=9, column=0, columnspan=2, sticky=tk.NSEW, pady=5)
        
        Button(fr, text="Salvar Arquivo", command=self._save_new_file, bg="#4CAF50", fg="white").grid(row=10, column=0, columnspan=2, pady=10)
        fr.columnconfigure(1, weight=1)
        fr.rowconfigure(9, weight=1)

    def _add_new_task(self):
        try:
            tid = self.new_task_entries["ID:"].get()
            cor = self.new_task_entries["Cor (hex):"].get()
            cheg = self.new_task_entries["Chegada:"].get()
            dur = self.new_task_entries["Duração:"].get()
            prio = self.new_task_entries["Prioridade:"].get()
            line = f"t{tid};{cor};{cheg};{dur};{prio}"
            self.new_tasks_list.append(line)
            self.new_tasks_display.insert(tk.END, line + "\n")
            for e in self.new_task_entries.values():
                e.delete(0, tk.END)
        except Exception as e:
            messagebox.showerror("Erro", str(e), parent=self.create_window)

    def _save_new_file(self):
        filepath = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text", "*.txt")], parent=self.create_window)
        if not filepath:
            return
        algo = self.new_algo.get()
        quantum = self.new_quantum.get()
        content = f"{algo};{quantum}\n#id;cor;chegada;duracao;prioridade\n" + "\n".join(self.new_tasks_list)
        with open(filepath, "w") as f:
            f.write(content)
        messagebox.showinfo("Sucesso", f"Salvo: {filepath}", parent=self.create_window)
        self.create_window.destroy()

    def generate_random_test(self):
        win = Toplevel(self)
        win.title("🎲 Teste Aleatório")
        win.geometry("350x300")
        fr = Frame(win, padx=20, pady=20)
        fr.pack(fill=tk.BOTH, expand=True)
        
        entries = {}
        for i, (lbl, val) in enumerate([("Tarefas:", "5"), ("Algoritmo:", "SRTF"), ("Quantum:", "2"), ("Dur Min:", "1"), ("Dur Max:", "10"), ("Chegada Max:", "20")]):
            Label(fr, text=lbl).grid(row=i, column=0, sticky=tk.W)
            e = Entry(fr)
            e.grid(row=i, column=1, sticky=tk.EW)
            e.insert(0, val)
            entries[lbl] = e
        
        def gen():
            n = int(entries["Tarefas:"].get())
            algo = entries["Algoritmo:"].get()
            q = entries["Quantum:"].get()
            dmin, dmax = int(entries["Dur Min:"].get()), int(entries["Dur Max:"].get())
            amax = int(entries["Chegada Max:"].get())
            
            content = f"{algo};{q}\n#id;cor;chegada;duracao;prioridade\n"
            for i in range(n):
                cor = f"{random.randint(0,255):02x}{random.randint(0,255):02x}{random.randint(0,255):02x}"
                content += f"t{i+1:02d};{cor};{random.randint(0,amax)};{random.randint(dmin,dmax)};{random.randint(1,10)}\n"
            
            fp = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text", "*.txt")], initialfile=f"teste_{n}tasks.txt")
            if fp:
                with open(fp, "w") as f:
                    f.write(content)
                win.destroy()
                algo_name, quantum, alpha, tasks = load_simulation_config(fp)
                self.current_algo, self.current_quantum, self.current_alpha, self.loaded_tasks = algo_name, quantum, alpha, tasks
                self.current_filepath = fp
                self._save_original_tasks_data()  # NOVO: Salva dados originais
                sched_class = SCHEDULER_FACTORY.get(algo_name)
                if sched_class:
                    if algo_name in ("PRIOPENV", "PRIOPENV-T"):
                        sched = sched_class(quantum=quantum or 1, alpha=alpha or 1)
                    elif quantum:
                        sched = sched_class(quantum=quantum)
                    else:
                        sched = sched_class()
                    self.simulator = Simulator(sched, tasks)
                    self.lbl_algo_name.config(text=f"Algoritmo: {algo_name}")
                    self.btn_step.config(state=tk.NORMAL)
                    self.btn_run.config(state=tk.NORMAL)
                    self.btn_edit.config(state=tk.NORMAL)
                    self.btn_reset.config(state=tk.NORMAL)
                    self.btn_back.config(state=tk.DISABLED)
                    self.update_tasks_table(tasks)
                    self.update_ui()
        
        Button(fr, text="Gerar", command=gen, bg="#4CAF50", fg="white").grid(row=6, column=0, columnspan=2, pady=20)

    def update_ui(self):
        if not self.simulator:
            return
        
        self.lbl_time.config(text=f"Tempo: {self.simulator.time}")
        
        current_id = self.simulator.current_task.id if self.simulator.current_task else "Nenhuma"
        self.lbl_current_task.config(text=f"Executando: {current_id}")
        
        ready_ids = [t.id for t in self.simulator.ready_queue]
        self.lbl_ready_queue.config(text=f"Fila de Prontos: {ready_ids}")
        
        # Atualiza tabela de tarefas (para mostrar prioridade dinâmica atualizada)
        if self.current_algo in ("PRIOPENV", "PRIOPENV-T"):
            self.update_tasks_table(self.simulator.all_tasks)
        
        self.draw_gantt()

    def draw_gantt(self):
        self.gantt_canvas.delete("all")
        if not self.simulator or not self.simulator.all_tasks:
            return
        
        task_ids = sorted([t.id for t in self.simulator.all_tasks], reverse=True)
        task_y_positions = {tid: i * 40 + 20 for i, tid in enumerate(task_ids)}
        
        for tid, y in task_y_positions.items():
            self.gantt_canvas.create_text(20, y, anchor=tk.W, text=f"T{tid}")
        
        block_width = 20
        left_margin = 50
        max_time = -1
        gantt_data = getattr(self.simulator, "gantt_data", []) or []
        
        for entry in gantt_data:
            if len(entry) == 4:
                time, tid, rgb, state = entry
            else:
                time, tid, rgb = entry
                state = "EXEC"
            
            if time > max_time:
                max_time = time
            
            if tid != "IDLE" and tid in task_y_positions:
                y_pos = task_y_positions[tid]
                x_start = left_margin + time * block_width
                color = f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"
                
                if state == "EXEC":
                    fill_color = color
                    outline_color = "black"
                elif state == "IO":
                    fill_color = "#bfbfbf"
                    outline_color = "black"
                elif state == "READY":
                    fill_color = ""
                    outline_color = color
                elif state == "MUTEX":
                    fill_color = "#9932CC"
                    outline_color = "black"
                else:
                    fill_color = color
                    outline_color = "black"
                
                self.gantt_canvas.create_rectangle(
                    x_start, y_pos - 15,
                    x_start + block_width, y_pos + 15,
                    fill=fill_color,
                    outline=outline_color,
                    width=1
                )
        
        if max_time < 0:
            max_time = self.simulator.time if self.simulator else 1
        
        total_time = max_time + 1
        x_end = left_margin + total_time * block_width
        max_y = max(task_y_positions.values()) if task_y_positions else 0
        eixo_y = max_y + 40
        
        self.gantt_canvas.create_line(left_margin, eixo_y, x_end, eixo_y, width=2)
        
        for t in range(1, total_time + 1):
            x_start = left_margin + (t - 1) * block_width
            self.gantt_canvas.create_line(x_start, eixo_y - 6, x_start, eixo_y + 6)
            self.gantt_canvas.create_line(x_start + block_width, eixo_y - 6, x_start + block_width, eixo_y + 6)
            self.gantt_canvas.create_text(x_start + block_width / 2, eixo_y + 18, text=str(t), anchor=tk.N, font=("Arial", 9))
        
        self.gantt_canvas.config(scrollregion=(0, 0, x_end + 50, eixo_y + 40))


if __name__ == "__main__":
    app = App()
    app.mainloop()

