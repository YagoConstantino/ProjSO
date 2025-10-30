# 🖥️ Simulador de Escalonamento de Processos

> Projeto de Sistemas Operacionais - Simulador educacional de algoritmos de escalonamento

[![Testes](https://img.shields.io/badge/testes-7%2F7%20passando-success)](tests/)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Licença](https://img.shields.io/badge/licen%C3%A7a-MIT-green.svg)](LICENSE)

## 📋 Visão Geral

Simulador completo de algoritmos de escalonamento de processos com interface gráfica, suporte a eventos de I/O, cálculo de estatísticas e gerador de testes aleatórios.

### ✨ Funcionalidades

- **4 Algoritmos de Escalonamento**: FIFO, SRTF, Priority, Round-Robin
- **Eventos de I/O**: Bloqueio e desbloqueio de tarefas
- **Quantum Configurável**: Round-Robin com preempção
- **Estatísticas Completas**: Turnaround, Waiting, Response Time
- **Gráfico de Gantt**: Visualização interativa da execução
- **Gerador de Testes**: Criação automática de cenários
- **Interface Intuitiva**: Tkinter com validações

## 🚀 Início Rápido

### Instalação

```bash
# Clone o repositório
git clone https://github.com/YagoConstantino/ProjSO.git
cd ProjSO

# Instale dependências
pip install -r requirements.txt

# Execute o simulador
python main.py
```

### Primeiro Uso

1. **Gere um teste aleatório**: Clique em "🎲 Teste Aleatório"
2. **Execute**: Clique em "Executar Tudo"
3. **Veja resultados**: Clique em "📊 Estatísticas"

## 📂 Estrutura do Projeto

```
ProjSO/
├── 📄 Código Principal
│   ├── main.py ................... Interface gráfica (422 linhas)
│   ├── simulador.py .............. Motor de simulação
│   ├── scheduler.py .............. Algoritmos de escalonamento
│   ├── tasks.py .................. Estruturas de dados (TCB)
│   └── config_loader.py .......... Parser de configurações
│
├── 📚 docs/
│   ├── README.md ................. Manual completo
│   ├── GUIA_TESTES.md ............ Casos de teste
│   ├── IMPLEMENTACOES.md ......... Detalhes técnicos
│   ├── CHECKLIST_FINAL.md ........ Verificação de entrega
│   └── RESUMO_EXECUTIVO.md ....... Visão executiva
│
├── 🧪 tests/
│   ├── test_suite.py ............. 7 testes automatizados
│   ├── teste_fifo_basico.txt ..... Teste FIFO
│   ├── teste_round_robin.txt ..... Teste RR
│   ├── teste_io_completo.txt ..... Teste I/O
│   └── teste_complexo.txt ........ Cenário complexo
│
├── 📋 exemplos/
│   └── *.txt ..................... Exemplos de configuração
│
└── 🛠️ scripts/
    └── verificar_entrega.py ...... Verifica arquivos para entrega
```

## 🧪 Testes

### Executar Suite Completa

```bash
python tests/test_suite.py
```

**Resultado esperado:**
```
✅ Passou: 7/7
❌ Falhou: 0/7
🎉 TODOS OS TESTES PASSARAM!
```

### Testes Disponíveis

1. Carregamento de configuração
2. Eventos de I/O
3. Quantum Round-Robin
4. Simulação FIFO
5. Cálculo de estatísticas
6. Preempção SRTF
7. Bloqueio por I/O

## 📖 Documentação

| Documento | Descrição |
|-----------|-----------|
| [**README Principal**](docs/README.md) | Manual completo do usuário |
| [**Guia de Testes**](docs/GUIA_TESTES.md) | Casos de teste documentados |
| [**Implementações**](docs/IMPLEMENTACOES.md) | Detalhes técnicos |
| [**Checklist Final**](docs/CHECKLIST_FINAL.md) | Verificação de entrega |
| [**Resumo Executivo**](docs/RESUMO_EXECUTIVO.md) | Visão geral do projeto |

## 💡 Exemplos de Uso

### Carregar Arquivo de Configuração

```bash
python main.py
# Clique em "Carregar Configuração"
# Selecione: tests/teste_fifo_basico.txt
```

### Criar Arquivo Manualmente

```txt
FIFO;0
#id;cor;ingresso;duracao;prioridade;io_events
t01;0;0;5;1
t02;1;2;3;2
t03;2;4;4;3
```

### Gerar Teste Aleatório

```bash
python main.py
# Clique em "🎲 Teste Aleatório"
# Configure parâmetros
# Clique em "Gerar e Carregar"
```

## 🎯 Algoritmos Implementados

| Algoritmo | Tipo | Preempção | Uso |
|-----------|------|-----------|-----|
| **FIFO/FCFS** | Ordem de chegada | Não | Simples, justo |
| **SRTF** | Menor tempo restante | Sim | Minimiza espera |
| **PRIO** | Por prioridade | Sim | Tarefas críticas |
| **RR** | Fatia de tempo | Sim (quantum) | Interativo |

## 📊 Estatísticas Calculadas

- **Turnaround Time**: Tempo total no sistema (fim - inicio)
- **Waiting Time**: Tempo em espera (turnaround - duracao)
- **Response Time**: Tempo até primeira execução
- **Ativações**: Número de entradas em execução

## 🛠️ Scripts Utilitários

### Verificar Arquivos para Entrega

```bash
python scripts/verificar_entrega.py
```

Verifica:
- ✅ Arquivos de código
- ✅ Arquivos de teste
- ✅ Documentação
- ⚠️  PDF de documentação visual
- ❌ Arquivos compactados (não deve ter!)

## 🤝 Contribuindo

Este é um projeto educacional. Para sugestões ou melhorias:

1. Fork o projeto
2. Crie uma branch (`git checkout -b feature/melhoria`)
3. Commit suas mudanças (`git commit -am 'Adiciona nova funcionalidade'`)
4. Push para a branch (`git push origin feature/melhoria`)
5. Abra um Pull Request

## 📝 Formato dos Arquivos de Configuração

```txt
ALGORITMO;QUANTUM
#comentário opcional
t<ID>;cor_id;ingresso;duracao;prioridade;[IO:tempo-duracao]
```

**Cores disponíveis:**
- 0: Vermelho | 1: Verde | 2: Azul
- 3: Amarelo | 4: Ciano | 5: Magenta | 6: Roxo

**Eventos I/O:** `IO:3-2;IO:7-1` (bloqueia aos 3s por 2 unidades, aos 7s por 1)

## 🎓 Desenvolvimento

### Requisitos

- Python 3.8+
- tkinter (geralmente incluído)
- typing (incluído no Python 3.5+)

### Instalar em Modo Desenvolvimento

```bash
pip install -r requirements.txt
python -m pytest tests/  # Se pytest instalado
```

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 👥 Autores

- **Yago Constantino** - [GitHub](https://github.com/YagoConstantino)
- **Rômulo** - Colaborador

## 🙏 Agradecimentos

- Professor da disciplina de Sistemas Operacionais
- Material de referência: `simulador-escalonamento-v01.pdf`
- Comunidade Python

## 📞 Suporte

Para problemas ou dúvidas:

1. Consulte a [documentação](docs/)
2. Veja os [casos de teste](tests/)
3. Abra uma [issue](https://github.com/YagoConstantino/ProjSO/issues)

---

<div align="center">

**[📚 Documentação](docs/)** • **[🧪 Testes](tests/)** • **[📋 Exemplos](exemplos/)** • **[🛠️ Scripts](scripts/)**

Feito com ❤️ para a disciplina de Sistemas Operacionais

</div>
