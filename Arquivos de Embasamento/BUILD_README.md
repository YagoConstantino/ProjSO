# 🏗️ Build do Executável com Ghostscript Embutido

## Visão Geral

Este guia explica como criar um executável standalone do simulador que **inclui o Ghostscript**, permitindo que os usuários exportem gráficos de Gantt em PNG sem precisar instalar dependências adicionais.

## Pré-requisitos

1. **Python 3.8+** instalado
2. **Ghostscript** instalado no sistema:
   ```powershell
   winget install --id Artifex.Ghostscript -e
   ```
3. **PyInstaller**:
   ```powershell
   pip install pyinstaller pillow
   ```

## Método 1: Build Automático (Recomendado)

Execute o script de build que faz tudo automaticamente:

```powershell
python build_with_ghostscript.py
```

Este script irá:
1. ✅ Verificar se o Ghostscript está instalado
2. ✅ Copiar os arquivos do Ghostscript para a pasta local
3. ✅ Criar um arquivo `.spec` personalizado para o PyInstaller
4. ✅ Empacotar tudo em um único executável

O executável final estará em: `dist/SimuladorEscalonamento.exe`

## Método 2: Build Manual

### Passo 1: Preparar o Ghostscript

Copie os arquivos do Ghostscript instalado para o projeto:

```powershell
# Crie a estrutura de pastas
mkdir ghostscript\bin
mkdir ghostscript\lib

# Encontre onde o Ghostscript está instalado
# Geralmente em: C:\Program Files\gs\gs10.04.0\

# Copie os arquivos necessários
copy "C:\Program Files\gs\gs10.04.0\bin\gswin64c.exe" ghostscript\bin\
copy "C:\Program Files\gs\gs10.04.0\bin\gsdll64.dll" ghostscript\bin\
xcopy /E /I "C:\Program Files\gs\gs10.04.0\lib" ghostscript\lib\
```

### Passo 2: Criar o Executável

```powershell
pyinstaller --clean SimuladorEscalonamento.spec
```

Ou usando o Makefile:
```powershell
make build
```

## Estrutura do Executável

Quando empacotado com o Ghostscript, a estrutura interna do executável será:

```
SimuladorEscalonamento.exe (executável único)
├── main.py (código Python compilado)
├── ghostscript/
│   ├── bin/
│   │   ├── gswin64c.exe
│   │   └── gsdll64.dll
│   └── lib/
│       └── [arquivos de suporte do GS]
└── [outros arquivos Python]
```

## Como Funciona

1. **Detecção Automática**: Ao iniciar, o `main.py` detecta se está rodando como executável PyInstaller
2. **Configuração do PATH**: Adiciona a pasta `ghostscript/bin` ao PATH do sistema automaticamente
3. **Configuração GS_LIB**: Define a variável de ambiente necessária para o Ghostscript funcionar
4. **Exportação PNG**: A exportação de Gantt para PNG funciona imediatamente, sem configuração adicional

## Testando o Executável

Após criar o executável:

```powershell
cd dist
.\SimuladorEscalonamento.exe
```

Teste a exportação PNG:
1. Carregue uma configuração de teste
2. Execute a simulação
3. Clique em "💾 Salvar Gantt"
4. Salve como PNG - deve funcionar imediatamente!

## Tamanho do Executável

- **Sem Ghostscript**: ~20-30 MB
- **Com Ghostscript**: ~50-70 MB

O aumento no tamanho é devido aos binários e bibliotecas do Ghostscript embutidos.

## Distribuição

O executável gerado em `dist/` é **completamente standalone**:
- ✅ Não requer Python instalado
- ✅ Não requer Ghostscript instalado
- ✅ Não requer nenhuma dependência externa
- ✅ Pode ser copiado para qualquer computador Windows 64-bit

## Solução de Problemas

### "Ghostscript não encontrado no sistema"
Instale o Ghostscript antes de rodar o build:
```powershell
winget install --id Artifex.Ghostscript -e
```

### "Executável não exporta PNG"
Verifique se o Ghostscript foi copiado corretamente:
```powershell
# Execute e veja se mostra mensagem de Ghostscript encontrado
python main.py
```

### Build falha com erro de DLL
Verifique se copiou TODOS os arquivos necessários:
- `gswin64c.exe`
- `gsdll64.dll`
- Pasta `lib` completa

## Alternativa: Build Sem Ghostscript

Se preferir criar um executável menor, sem o Ghostscript embutido:

```powershell
pyinstaller --onefile --windowed --name=SimuladorEscalonamento main.py
```

Neste caso, os usuários precisarão instalar o Ghostscript separadamente.

---

**Nota**: Este método de empacotamento é específico para Windows. Para Linux/macOS, seria necessário adaptar os caminhos e nomes de arquivos do Ghostscript.
