"""
Script para criar executável com Ghostscript embutido.

Este script:
1. Baixa o Ghostscript portable (se necessário)
2. Configura o PyInstaller para incluir os binários do Ghostscript
3. Gera o executável standalone com tudo embutido
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
GHOSTSCRIPT_VERSION = "10.04.0"
GHOSTSCRIPT_DIR = PROJECT_DIR / "ghostscript"
GHOSTSCRIPT_BIN = GHOSTSCRIPT_DIR / "bin"

def check_ghostscript_installed():
    """Verifica se o Ghostscript já está instalado no sistema."""
    try:
        result = subprocess.run(["gs", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Ghostscript já instalado no sistema: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    try:
        result = subprocess.run(["gswin64c", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✓ Ghostscript já instalado no sistema: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    return False

def download_ghostscript_portable():
    """
    Baixa e extrai o Ghostscript portable.
    
    Nota: Para simplificar, este script assume que você já tem o Ghostscript
    instalado localmente. Para distribuição, você precisaria:
    1. Baixar o Ghostscript portable/standalone
    2. Extrair apenas os arquivos necessários (gs executável + DLLs)
    3. Copiar para a pasta ghostscript/
    """
    print("\n⚠️  AVISO: Ghostscript portable não encontrado!")
    print("Para criar um executável standalone com Ghostscript embutido:")
    print("1. Instale o Ghostscript: winget install --id Artifex.Ghostscript -e")
    print("2. Copie os arquivos necessários do Ghostscript para ./ghostscript/bin/")
    print("   - gswin64c.exe (ou gs.exe)")
    print("   - gsdll64.dll")
    print("   - Pasta 'lib' com os arquivos de suporte")
    print("\nPor enquanto, o executável será criado SEM o Ghostscript embutido.")
    print("Os usuários precisarão instalar o Ghostscript separadamente.\n")
    return False

def find_ghostscript_system_path():
    """Encontra o caminho do Ghostscript instalado no sistema."""
    possible_paths = [
        r"C:\Program Files\gs",
        r"C:\Program Files (x86)\gs",
    ]
    
    for base_path in possible_paths:
        if os.path.exists(base_path):
            # Procura por versões instaladas
            for item in os.listdir(base_path):
                gs_path = Path(base_path) / item / "bin"
                if gs_path.exists():
                    gs_exe = gs_path / "gswin64c.exe"
                    if gs_exe.exists():
                        return gs_path
    return None

def copy_ghostscript_to_local():
    """Copia o Ghostscript do sistema para a pasta local do projeto."""
    gs_system_path = find_ghostscript_system_path()
    
    if not gs_system_path:
        print("❌ Ghostscript não encontrado no sistema")
        return False
    
    print(f"✓ Ghostscript encontrado em: {gs_system_path}")
    
    # Cria a pasta local
    GHOSTSCRIPT_BIN.mkdir(parents=True, exist_ok=True)
    
    # Copia os arquivos essenciais
    files_to_copy = ["gswin64c.exe", "gsdll64.dll"]
    for file in files_to_copy:
        src = gs_system_path / file
        dst = GHOSTSCRIPT_BIN / file
        if src.exists():
            print(f"  Copiando {file}...")
            shutil.copy2(src, dst)
        else:
            print(f"  ⚠️  {file} não encontrado")
    
    # Copia a pasta lib (necessária para o Ghostscript funcionar)
    lib_src = gs_system_path.parent / "lib"
    lib_dst = GHOSTSCRIPT_DIR / "lib"
    
    if lib_src.exists():
        print(f"  Copiando pasta lib...")
        if lib_dst.exists():
            shutil.rmtree(lib_dst)
        shutil.copytree(lib_src, lib_dst)
    
    print("✓ Ghostscript copiado com sucesso!\n")
    return True

def create_pyinstaller_spec():
    """Cria um arquivo .spec personalizado para o PyInstaller."""
    
    has_ghostscript = GHOSTSCRIPT_BIN.exists() and (GHOSTSCRIPT_BIN / "gswin64c.exe").exists()
    
    datas_section = ""
    if has_ghostscript:
        datas_section = f"""
    datas=[
        ('{GHOSTSCRIPT_DIR.as_posix()}', 'ghostscript'),
    ],"""
    
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],{datas_section}
    hiddenimports=['PIL._tkinter_finder'],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SimuladorEscalonamento',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Janela de console não aparece
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
"""
    
    spec_file = PROJECT_DIR / "SimuladorEscalonamento.spec"
    with open(spec_file, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print(f"✓ Arquivo .spec criado: {spec_file}\n")
    return spec_file

def build_executable():
    """Executa o PyInstaller para criar o executável."""
    print("="*60)
    print("🏗️  CONSTRUINDO EXECUTÁVEL")
    print("="*60)
    
    # Verifica se PyInstaller está instalado
    try:
        subprocess.run(["pyinstaller", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ PyInstaller não encontrado. Instalando...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"], check=True)
    
    # Cria o arquivo .spec
    spec_file = create_pyinstaller_spec()
    
    # Executa PyInstaller
    print("🔨 Executando PyInstaller...")
    result = subprocess.run(["pyinstaller", "--clean", str(spec_file)], capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ BUILD CONCLUÍDO COM SUCESSO!")
        print("="*60)
        print(f"📦 Executável criado em: dist/SimuladorEscalonamento.exe")
        print("="*60)
    else:
        print("❌ ERRO NO BUILD!")
        print(result.stderr)
        return False
    
    return True

def main():
    """Função principal do script de build."""
    print("\n" + "="*60)
    print("🚀 BUILD COM GHOSTSCRIPT EMBUTIDO")
    print("="*60 + "\n")
    
    # Verifica se Ghostscript está instalado
    if not check_ghostscript_installed():
        print("⚠️  Ghostscript não está instalado no sistema")
        print("Instalando via winget...")
        subprocess.run(["winget", "install", "--id", "Artifex.Ghostscript", "-e"])
        print()
    
    # Copia Ghostscript para a pasta local
    if not GHOSTSCRIPT_BIN.exists():
        if not copy_ghostscript_to_local():
            print("⚠️  Prosseguindo sem Ghostscript embutido...")
    
    # Constrói o executável
    build_executable()
    
    print("\n💡 IMPORTANTE:")
    if (GHOSTSCRIPT_BIN / "gswin64c.exe").exists():
        print("   ✅ Ghostscript FOI embutido no executável")
        print("   Os usuários NÃO precisarão instalar Ghostscript")
    else:
        print("   ⚠️  Ghostscript NÃO foi embutido")
        print("   Os usuários precisarão instalar Ghostscript para exportar PNG")
        print("   Comando: winget install --id Artifex.Ghostscript -e")
    print()

if __name__ == "__main__":
    main()
