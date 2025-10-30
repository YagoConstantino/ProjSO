# 📚 GUIA DE TESTES - Simulador de Escalonamento

## Teste 1: FIFO Básico (Sem Preempção)
**Arquivo**: `teste_fifo_basico.txt`
```
FIFO;0
#id;cor_id;ingresso;duracao;prioridade
t01;0;0;5;1
t02;1;2;3;2
t03;2;4;4;3
```

**Comportamento Esperado**:
- T1 executa do tempo 0 ao 5 (sem interrupção)
- T2 executa do tempo 5 ao 8
- T3 executa do tempo 8 ao 12

---

## Teste 2: SRTF com Preempção
**Arquivo**: `teste_srtf_preempcao.txt`
```
SRTF;0
#id;cor_id;ingresso;duracao;prioridade
t01;0;0;8;1
t02;1;1;4;1
t03;2;3;2;1
```

**Comportamento Esperado**:
- T1 inicia em 0
- T2 chega em 1 e preempta T1 (tempo restante menor: 4 < 7)
- T3 chega em 3 e preempta T2 (tempo restante menor: 2 < 3)
- Ordem de conclusão: T3, T2, T1

---

## Teste 3: Prioridade com Preempção
**Arquivo**: `teste_prioridade.txt`
```
PRIO;0
#id;cor_id;ingresso;duracao;prioridade
t01;0;0;6;2
t02;1;2;4;5
t03;2;4;3;3
```

**Comportamento Esperado**:
- T1 (prioridade 2) executa de 0 a 2
- T2 (prioridade 5) chega e preempta T1
- T2 executa até terminar
- T3 (prioridade 3) tem mais prioridade que T1 restante
- Ordem: T2 > T3 > T1

---

## Teste 4: Round-Robin com Quantum
**Arquivo**: `teste_round_robin.txt`
```
RR;3
#id;cor_id;ingresso;duracao;prioridade
t01;0;0;7;1
t02;1;0;5;1
t03;2;0;3;1
```

**Comportamento Esperado**:
- Todas chegam em 0
- T1 executa 3 unidades (quantum), vai para fim da fila
- T2 executa 3 unidades, vai para fim da fila
- T3 executa 3 unidades e termina
- T1 executa 3 unidades, vai para fim
- T2 executa 2 unidades e termina
- T1 executa 1 unidade e termina

---

## Teste 5: Eventos de I/O
**Arquivo**: `teste_io_bloqueio.txt`
```
SRTF;0
#id;cor_id;ingresso;duracao;prioridade;io_events
t01;0;0;8;1;IO:3-2
t02;1;2;5;1;IO:2-1
t03;2;4;4;1
```

**Comportamento Esperado**:
- T1 executa de 0 a 3, depois bloqueia por 2 unidades (I/O)
- Durante bloqueio de T1, T2 ou T3 executam
- T1 desbloqueia no tempo 5 e volta para fila de prontos
- Sistema gerencia múltiplas transições de estado

---

## Teste 6: Cenário Complexo
**Arquivo**: `teste_complexo.txt`
```
PRIO;0
#id;cor_id;ingresso;duracao;prioridade;io_events
t01;0;0;10;3;IO:4-3
t02;1;2;6;5;IO:2-2
t03;2;5;4;2
t04;3;8;5;4;IO:1-1;IO:3-2
```

**Características**:
- Múltiplas prioridades
- Chegadas escalonadas
- Vários eventos I/O
- Preempções frequentes

**Métricas Esperadas**:
- Turnaround médio: ~15-20
- Tarefas de alta prioridade terminam primeiro
- I/O causa fragmentação no Gantt

---

## 🧪 Validação de Testes

### Checklist de Verificação:
- [ ] Todas as tarefas foram executadas?
- [ ] A ordem de execução seguiu o algoritmo?
- [ ] Eventos de I/O bloquearam corretamente?
- [ ] Estatísticas fazem sentido?
- [ ] Gantt Chart está legível e correto?

### Valores Típicos:
| Métrica | Valor Baixo | Valor Médio | Valor Alto |
|---------|-------------|-------------|------------|
| Turnaround | < 10 | 10-20 | > 20 |
| Waiting | < 5 | 5-15 | > 15 |
| Response | < 2 | 2-5 | > 5 |
| Ativações | 1 | 2-3 | > 5 |

---

## 🎯 Teste de Estresse

Use o **Gerador de Testes Aleatórios**:
1. Clique em "🎲 Teste Aleatório"
2. Configure:
   - Número de tarefas: 20
   - Duração: 1-15
   - Chegada: 0-30
   - Prob. I/O: 50%
3. Execute e verifique que:
   - Não há crashes
   - Todas as tarefas terminam
   - Estatísticas são calculadas
   - Gantt é renderizado (pode precisar scroll)

---

## 📊 Comparação de Algoritmos

Execute o **mesmo conjunto de tarefas** com diferentes algoritmos:

**Tarefas Base**:
```
t01;0;0;8;3
t02;1;2;5;5
t03;2;4;4;2
```

**Comparar**:
- FIFO vs SRTF: Waiting Time
- PRIO vs RR: Response Time
- RR (Q=2) vs RR (Q=5): Ativações

**Análise**:
- SRTF geralmente minimiza Waiting Time
- PRIO favorece tarefas importantes
- RR oferece melhor Response Time médio

---

## ⚠️ Casos Extremos

### Teste de Inanição (Starvation)
```
PRIO;0
t01;0;0;10;1
t02;1;1;5;10
t03;2;2;5;10
t04;3;3;5;10
```
- T1 (baixa prioridade) pode demorar muito para executar

### Teste de CPU Ociosa
```
FIFO;0
t01;0;10;5;1
t02;1;20;5;1
```
- CPU fica ociosa de 0 a 10 e de 15 a 20

### Teste de I/O Intensivo
```
SRTF;0
t01;0;0;10;1;IO:1-2;IO:3-2;IO:5-2;IO:7-2
```
- Tarefa passa mais tempo bloqueada que executando

---

**Dica**: Sempre compare os resultados com cálculos manuais em casos pequenos!
