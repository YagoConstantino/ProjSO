# 🧪 Testes do Simulador

Esta pasta contém todos os arquivos de teste do projeto.

## Arquivos de Teste

### 🐍 Suite de Testes Automatizados
- **test_suite.py** - Bateria com 7 testes automatizados
  - Carregamento de configuração
  - Eventos de I/O
  - Quantum Round-Robin
  - Simulação FIFO
  - Cálculo de estatísticas
  - Preempção SRTF
  - Bloqueio por I/O

### 📄 Casos de Teste (Arquivos .txt)

#### Testes Básicos
- **teste_fifo_basico.txt** - Teste FIFO sem preempção
  - 3 tarefas com chegadas escalonadas
  - Execução em ordem FIFO

- **teste_round_robin.txt** - Teste Round-Robin com quantum
  - Quantum = 3
  - 4 tarefas com preempção por quantum

#### Testes Avançados
- **teste_io_completo.txt** - Teste com eventos de I/O
  - 4 tarefas
  - Múltiplos eventos de bloqueio
  - Algoritmo SRTF

- **teste_complexo.txt** - Cenário complexo
  - Prioridades variadas
  - Múltiplos eventos I/O
  - Chegadas escalonadas

## Como Executar

### Suite Completa
```bash
cd tests
python test_suite.py
```

### Teste Individual (Interface Gráfica)
```bash
cd ..
python main.py
# Carregar arquivo: tests/teste_fifo_basico.txt
```

## Resultados Esperados

Todos os testes devem passar:
```
✅ Passou: 7/7
❌ Falhou: 0/7
```

## Adicionar Novos Testes

Para adicionar um novo caso de teste:

1. Crie arquivo `.txt` nesta pasta
2. Use o formato:
   ```
   ALGORITMO;QUANTUM
   t01;cor;ingresso;duracao;prioridade;[IO:X-Y]
   ```
3. Documente em `../docs/GUIA_TESTES.md`

## Navegação

```
../               - Código principal
../docs/          - Documentação
../exemplos/      - Exemplos de configuração
../scripts/       - Scripts utilitários
```
