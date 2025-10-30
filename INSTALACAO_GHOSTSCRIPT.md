# Instalação do Ghostscript para Exportação PNG

## O que é?
O Ghostscript é necessário para que o PIL/Pillow converta o gráfico de Gantt de PostScript (.ps) para PNG (.png).

## Instalação no Windows

### Opção 1: Usando winget (Recomendado)
```powershell
winget install --id Artifex.Ghostscript -e
```

### Opção 2: Usando Chocolatey
```powershell
choco install ghostscript -y
```

### Opção 3: Download Manual
1. Acesse: https://ghostscript.com/releases/gsdnld.html
2. Baixe a versão mais recente para Windows (64-bit)
3. Execute o instalador
4. Certifique-se de marcar a opção para adicionar ao PATH

## Verificação da Instalação
```powershell
gswin64c --version
```
Ou:
```powershell
gs --version
```

## Após a Instalação
1. **Feche e reabra o aplicativo Python** (main.py)
2. Tente exportar o Gantt novamente
3. Agora deve funcionar diretamente para PNG!

## Alternativa (sem Ghostscript)
Se preferir não instalar o Ghostscript:
1. O sistema salvará automaticamente como `.ps` (PostScript)
2. Você pode converter online em: https://convertio.co/ps-png/
3. Ou usar visualizadores PDF que abrem `.ps` e exportam como PNG

## Observações
- O Pillow já está instalado (`pip install pillow`)
- O Ghostscript só é necessário para conversão automática PS→PNG
- Sem Ghostscript, a exportação funcionará, mas gerará arquivo `.ps` em vez de `.png`
