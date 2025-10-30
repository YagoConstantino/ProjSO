# 🛠️ Scripts Utilitários

Esta pasta contém scripts auxiliares para facilitar o desenvolvimento e entrega.

## Arquivos

### verificar_entrega.py
Script para verificar se todos os arquivos necessários estão presentes antes da entrega.

**Uso:**
```bash
cd scripts
python verificar_entrega.py
```

**O que verifica:**
- ✅ Arquivos de código principal
- ✅ Arquivos de teste
- ✅ Documentação
- ✅ Arquivos de configuração
- ⚠️  Arquivo PDF de documentação visual
- ❌ Arquivos compactados (não devem existir!)

**Saída:**
```
📦 VERIFICAÇÃO DE ARQUIVOS PARA ENTREGA
======================================
✅ Arquivos encontrados: 16/16
📊 Percentual completo: 100.0%
```

## Adicionar Novos Scripts

Para adicionar um novo script utilitário:

1. Crie o arquivo `.py` nesta pasta
2. Adicione docstring explicando sua função
3. Atualize este README
4. Teste o script

## Exemplos de Scripts Úteis

Ideias para scripts futuros:
- Gerador de relatórios de performance
- Validador de arquivos de configuração
- Conversor de formatos
- Estatísticas comparativas entre algoritmos

## Navegação

```
../               - Código principal
../tests/         - Arquivos de teste
../docs/          - Documentação
../exemplos/      - Exemplos de configuração
```
