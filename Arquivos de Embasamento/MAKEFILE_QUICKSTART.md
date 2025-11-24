# 🔨 Guia Rápido do Makefile

## Comandos Disponíveis

### Build Completo (Recomendado para Distribuição) ⭐
```bash
make build-full
```
- ✅ Cria executável **COM Ghostscript embutido**
- ✅ Usuários **NÃO precisam** instalar Ghostscript
- ✅ Exportação PNG funciona imediatamente
- 📦 Tamanho: ~50-70 MB

### Build Simples (Menor tamanho)
```bash
make build
```
- ⚠️ Cria executável **SEM Ghostscript**
- ⚠️ Usuários **precisam instalar** Ghostscript separadamente
- 📦 Tamanho: ~20-30 MB

### Outros Comandos

```bash
make install     # Cria ambiente virtual e instala dependências
make run         # Executa o simulador diretamente (sem build)
make test        # Executa testes automatizados
make clean       # Remove arquivos de build (dist/, build/)
make clean-all   # Remove tudo incluindo venv/
make help        # Mostra lista de comandos
```

## Fluxo Recomendado

### Para Desenvolvimento:
```bash
make run         # Testa o código diretamente
make test        # Valida com testes
```

### Para Distribuição:
```bash
make build-full  # Gera executável completo
cd dist
# Teste o executável:
./SimuladorEscalonamento.exe
```

## Comparação: `build` vs `build-full`

| Característica | `make build` | `make build-full` |
|----------------|--------------|-------------------|
| Ghostscript embutido | ❌ Não | ✅ Sim |
| Tamanho | ~20-30 MB | ~50-70 MB |
| Requer Ghostscript instalado | ✅ Sim | ❌ Não |
| Exportação PNG | ⚠️ Só com GS instalado | ✅ Imediato |
| Recomendado para distribuição | ❌ | ✅ |

## O que acontece com `make build-full`?

1. **Cria ambiente virtual** (se não existir)
2. **Instala dependências** do `requirements.txt`
3. **Executa** `build_with_ghostscript.py`:
   - Detecta Ghostscript instalado no sistema
   - Copia binários do GS para pasta local (`ghostscript/`)
   - Gera arquivo `.spec` personalizado
   - Empacota tudo com PyInstaller
4. **Resultado**: `dist/SimuladorEscalonamento.exe` (standalone completo)

## Pré-requisitos para `build-full`

Você precisa ter o Ghostscript **instalado no sistema** para que ele seja copiado:

```powershell
winget install --id Artifex.Ghostscript -e
```

Depois:
```bash
make build-full
```

## Exemplo de Uso Completo

```bash
# 1. Clone o repositório
git clone <repo-url>
cd ProjSO

# 2. Gere o executável completo
make build-full

# 3. Distribua o executável
# O arquivo em dist/ pode ser copiado para qualquer computador Windows
# SEM precisar de Python ou Ghostscript instalados!
```

## Troubleshooting

### "Ghostscript não encontrado no sistema"
```bash
# Instale o Ghostscript primeiro:
winget install --id Artifex.Ghostscript -e

# Depois rode o build novamente:
make build-full
```

### "make: command not found"
No Windows, você precisa ter o Make instalado:
```powershell
winget install --id GnuWin32.Make -e
# ou
winget install --id ezwinports.make -e
```

### Quer limpar tudo e recomeçar?
```bash
make clean-all  # Remove dist/, build/, venv/
make build-full # Reconstrói do zero
```

---

**Resumo**: Use `make build-full` para distribuição. Usuários finais não precisarão instalar nada! 🚀
