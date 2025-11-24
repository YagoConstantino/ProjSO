# Instalação do Ghostscript para Exportação PNG

## ⚠️ ATUALIZAÇÃO: Ghostscript Agora é OPCIONAL!

O simulador usa uma **abordagem híbrida inteligente** que tenta múltiplos métodos:

1. **Método 1 (Padrão)**: ImageGrab - Captura de tela
   - ✅ **Não requer Ghostscript**
   - ✅ Funciona apenas com `pip install pillow`
   - ✅ Mais rápido
   
2. **Método 2 (Fallback)**: PostScript + Ghostscript
   - ⚠️ Requer Ghostscript instalado
   - ✅ Melhor qualidade (vetorial)
   - ✅ Funciona mesmo com janela minimizada

## Se a Exportação Já Funciona

Se você consegue exportar PNG sem problemas, **não precisa instalar o Ghostscript**!

O método ImageGrab está funcionando e é suficiente para a maioria dos casos.

## Por que Instalar o Ghostscript?

Instale o Ghostscript se:
- ✅ Quer **melhor qualidade** (imagem vetorial)
- ✅ Precisa exportar com a **janela minimizada**
- ✅ Quer o método de **backup robusto**
- ✅ Vai **distribuir o executável** (empacotado)

## Instalação no Windows

### Opção 1: Usando winget (Recomendado - Mais Rápido)
```powershell
winget install --id Artifex.Ghostscript -e
```

### Opção 2: Usando Chocolatey
```powershell
choco install ghostscript -y
```

### Opção 3: Download Manual
1. Acesse: https://ghostscript.com/releases/gsdnld.html
2. Baixe: **Ghostscript AGPL Release** (versão mais recente para Windows 64-bit)
3. Execute o instalador
4. **Importante:** Marque a opção para adicionar ao PATH durante a instalação

## Verificação da Instalação
Após instalar, abra um novo PowerShell e teste:
```powershell
gs --version
```
Ou:
```powershell
gswin64c --version
```

Se retornar a versão (ex: `10.04.0`), está instalado corretamente!

## Após a Instalação
1. **Feche completamente** o aplicativo Python (se estiver aberto)
2. **Reabra** o simulador:
   ```powershell
   python main.py
   ```
3. Agora a exportação PNG funcionará perfeitamente! ✅

## Por que o Ghostscript é necessário?
- O Tkinter (biblioteca de interface gráfica do Python) só consegue exportar canvas como **PostScript (.ps)**
- O PIL/Pillow usa o Ghostscript internamente para converter **PostScript → PNG**
- Sem Ghostscript = Sem conversão = Sem PNG

## Já instalou o Pillow?
O Pillow já está listado no `requirements.txt`. Se ainda não instalou:
```powershell
pip install pillow
```

---

**Resumo:** Ghostscript é necessário. Instale com winget, feche e reabra o app. Pronto!
