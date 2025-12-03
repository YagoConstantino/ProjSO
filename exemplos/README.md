# 📋 Exemplos de Configuração

Esta pasta contém exemplos de arquivos de configuração para o simulador.

## Arquivos

- **exemplos-arquivo-configuracao (1).txt** - Exemplo fornecido com o projeto
- **nova_config.txt** - Exemplo de configuração customizada

## Formato dos Arquivos

```txt
ALGORITMO;QUANTUM
#comentário opcional
t01;cor_hex;ingresso;duracao;prioridade;[IO:tempo-duracao]
t02;cor_hex;ingresso;duracao;prioridade
...
```

### Campos Obrigatórios
- **ALGORITMO**: FIFO, FCFS, SRTF, PRIO, PRIOP, RR
- **QUANTUM**: Número inteiro (obrigatório para RR, opcional para outros)
- **t<ID>**: Identificador da tarefa (ex: t01, t02)
- **cor_hex**: Cor em formato hexadecimal - `#RRGGBB` ou `RRGGBB`
- **ingresso**: Tempo de chegada
- **duracao**: Tempo de CPU necessário
- **prioridade**: Número inteiro (maior = mais prioritária)

### Campos Opcionais
- **IO:tempo-duracao**: Eventos de I/O
  - Múltiplos eventos: `IO:2-1;IO:5-2`
  - tempo: Quando bloquear (relativo ao tempo de execução)
  - duracao: Por quanto tempo bloquear

## Exemplos de Cores Hexadecimais
````
0 - Vermelho
1 - Verde
2 - Azul
3 - Amarelo
4 - Ciano
5 - Magenta
6 - Roxo
```

## Exemplos

### FIFO Simples
```txt
FIFO;0
t01;0;0;5;1
t02;1;2;3;2
t03;2;4;4;3
```

### Round-Robin com Quantum
```txt
RR;3
t01;0;0;7;1
t02;1;0;5;1
t03;2;0;3;1
```

### Com Eventos I/O
```txt
SRTF;0
t01;0;0;10;5;IO:3-2
t02;1;2;6;3;IO:2-1;IO:4-1
t03;2;4;8;4
```

## Criar Novos Exemplos

Use a interface gráfica:
1. Execute `python main.py`
2. Clique em "Criar TXT"
3. Ou use o gerador aleatório (🎲)

## Navegação

```
../               - Código principal
../tests/         - Arquivos de teste
../docs/          - Documentação
../scripts/       - Scripts utilitários
```
