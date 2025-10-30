# 🖥️ Simulador de Escalonamento de Processos

Simulador educacional de algoritmos de escalonamento de processos para Sistemas Operacionais, desenvolvido em Python com interface gráfica Tkinter.

## 📋 Funcionalidades

### ✅ Algoritmos de Escalonamento Implementados
- **FIFO/FCFS** (First In, First Out / First Come, First Served) - Não preemptivo
- **SRTF** (Shortest Remaining Time First) - Preemptivo
- **PRIO/PRIOP** (Priority Scheduling) - Preemptivo
- **RR** (Round-Robin) - Preemptivo com quantum configurável

### 🎯 Recursos Principais
1. **Carregamento de Configurações**: Importa arquivos .txt com definição de tarefas e algoritmos
2. **Criação Interativa de Tarefas**: Interface para criar arquivos de configuração
3. **Eventos de I/O**: Suporte a bloqueio de tarefas durante operações de entrada/saída
4. **Gráfico de Gantt**: Visualização em tempo real da execução das tarefas
5. **Estatísticas Detalhadas**: 
   - Turnaround Time (tempo total no sistema)
   - Waiting Time (tempo de espera)
   - Response Time (tempo até primeira execução)
   - Número de ativações
6. **Gerador de Testes Aleatórios**: Cria cenários de teste com parâmetros configuráveis
7. **Exportação de Resultados**: Salva estatísticas em arquivo de texto

## 🚀 Como Usar

### Instalação
```bash
# Clone o repositório
git clone <url-do-repositorio>
cd ProjSO

# Instale as dependências
pip install -r requirements.txt

# Execute o simulador
python main.py
```

### Interface Principal

#### Botões de Controle
- **Carregar Configuração**: Abre arquivo .txt com tarefas
- **Próximo Passo**: Executa 1 unidade de tempo
- **Executar Tudo**: Executa a simulação completa
- **Criar TXT**: Interface para criar arquivos de configuração
- **🎲 Teste Aleatório**: Gera e carrega cenário aleatório
- **📊 Estatísticas**: Exibe métricas da simulação (após conclusão)

## 📄 Formato do Arquivo de Configuração

```txt
ALGORITMO;QUANTUM
#id;cor_id;ingresso;duracao;prioridade;io_events
t01;0;0;10;5;IO:3-2
t02;1;2;5;3;IO:2-1;IO:4-1
t03;2;4;8;4
```

### Estrutura:
- **Linha 1**: `ALGORITMO;QUANTUM`
  - ALGORITMO: FIFO, SRTF, PRIO, PRIOP, RR
  - QUANTUM: Valor inteiro (obrigatório para RR, opcional para outros)

- **Linha 2**: Comentário (opcional, começa com #)

- **Linhas seguintes**: Uma tarefa por linha
  - `t<ID>`: Identificador da tarefa (ex: t01, t02)
  - `cor_id`: Índice de cor (0-6) para o gráfico
  - `ingresso`: Tempo de chegada da tarefa
  - `duracao`: Tempo de CPU necessário
  - `prioridade`: Prioridade estática (maior = mais prioritária)
  - `io_events` (opcional): Eventos I/O no formato `IO:tempo-duracao`
    - Múltiplos eventos separados por `;`
    - Exemplo: `IO:2-1;IO:5-2` (I/O aos 2s por 1s, e aos 5s por 2s)

### Cores Disponíveis
- 0: Vermelho
- 1: Verde
- 2: Azul
- 3: Amarelo
- 4: Ciano
- 5: Magenta
- 6: Roxo

## 🧪 Exemplo de Uso

1. **Criar Teste Aleatório**:
   - Clique em "🎲 Teste Aleatório"
   - Configure número de tarefas, algoritmo, etc.
   - Clique em "Gerar e Carregar"

2. **Executar Simulação**:
   - Use "Próximo Passo" para depuração passo a passo
   - Ou "Executar Tudo" para ver o resultado final

3. **Analisar Resultados**:
   - Clique em "📊 Estatísticas" após a conclusão
   - Exporte os dados com o botão "Exportar Estatísticas"

## 📊 Interpretando as Estatísticas

- **Turnaround Time**: Tempo desde chegada até conclusão (fim - inicio)
- **Waiting Time**: Tempo esperando na fila (turnaround - duracao)
- **Response Time**: Tempo até primeira execução (primeira_exec - inicio)
- **Ativações**: Número de vezes que a tarefa entrou em execução

## 🎨 Gráfico de Gantt

### Legenda de Cores:
- **Verde**: Tarefa em execução (CPU)
- **Laranja**: Tarefa bloqueada (I/O)
- **Cinza**: CPU ociosa (IDLE)

### Interpretação:
- Cada linha representa uma tarefa (T1, T2, T3...)
- Eixo horizontal mostra o tempo
- Blocos coloridos mostram quando cada tarefa executou

## 🔧 Estrutura do Projeto

```
ProjSO/
├── main.py              # Interface gráfica principal
├── simulador.py         # Lógica de simulação e eventos
├── scheduler.py         # Algoritmos de escalonamento
├── tasks.py             # Estruturas de dados (TCB, Fila)
├── config_loader.py     # Carregamento de arquivos
├── requirements.txt     # Dependências Python
└── README.md           # Esta documentação
```

## 📚 Estados das Tarefas

1. **Novo (1)**: Tarefa criada, aguardando chegada
2. **Pronto (2)**: Na fila, aguardando CPU
3. **Executando (3)**: Usando a CPU
4. **Bloqueado (4)**: Aguardando I/O
5. **Terminado (5)**: Execução completa

## 🐛 Resolução de Problemas

### Erro ao carregar arquivo
- Verifique o formato do arquivo (use o exemplo acima)
- Certifique-se de que todos os campos obrigatórios estão presentes
- Valores numéricos devem ser inteiros positivos

### Simulação não inicia
- Verifique se há tarefas no arquivo
- Confirme que o algoritmo é válido (FIFO, SRTF, PRIO, RR)
- Para RR, certifique-se de que o quantum está definido

### Estatísticas não aparecem
- Execute a simulação completa primeiro ("Executar Tudo")
- Aguarde até que todas as tarefas terminem

## 👥 Desenvolvimento

### Autores
- [Seu Nome]
- [Nome do Colega] (se em dupla)

### Disciplina
Sistemas Operacionais - [Universidade] - [Período]

## 📝 Licença

Este projeto é desenvolvido para fins educacionais.

## 🎓 Referências

- Material da disciplina de Sistemas Operacionais
- `simulador-escalonamento-v01.pdf` (especificação do projeto)
- Tanenbaum, A. S. "Sistemas Operacionais Modernos"

---

**Última atualização**: Outubro/2025
Projeto efetuado na disciplina ICSO30 de Sistemas Operacionais na UTFPR durante o semestre de 2025.2

# Simulação de um Sistema Operacional Multitarefa de Tempo Compartilhado

Objetivos
1. Aprofundar o estudo do gerenciamento de tarefas através de implementação de escalonadores,
a execução de múltiplas tarefas e do escalador, e a apresentação gráfica dessa execução do sistema
ao longo do tempo.
2. Aprimorar o conhecimento sobre interação entre tarefas usando serviços de exclusão mútua
comumente encontrados em sistemas operacionais multi-tarefa;
3. Compreender e resolver os problemas de escalonamento, p.ex., inanição e inversão de
prioridades;

Em Resumo um simulador de escalonamento
