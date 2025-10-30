"""
Script para verificar arquivos antes da entrega
Lista todos os arquivos que devem ser enviados no Moodle

IMPORTANTE: Execute este script da pasta raiz do projeto:
  cd ..
  python scripts/verificar_entrega.py
"""

import os
from pathlib import Path

def check_files():
    """Verifica quais arquivos estão prontos para entrega"""
    
    print("=" * 70)
    print("📦 VERIFICAÇÃO DE ARQUIVOS PARA ENTREGA")
    print("=" * 70)
    
    # Muda para diretório raiz se estiver na pasta scripts
    if os.path.basename(os.getcwd()) == 'scripts':
        os.chdir('..')
        print("📁 Mudando para diretório raiz do projeto\n")
    
    # Arquivos obrigatórios (com caminhos relativos)
    required_files = {
        "Código Principal": [
            "main.py",
            "simulador.py",
            "scheduler.py",
            "tasks.py",
            "config_loader.py"
        ],
        "Testes": [
            "tests/test_suite.py",
            "tests/teste_fifo_basico.txt",
            "tests/teste_round_robin.txt",
            "tests/teste_io_completo.txt",
            "tests/teste_complexo.txt"
        ],
        "Documentação": [
            "docs/README.md",
            "docs/GUIA_TESTES.md",
            "docs/IMPLEMENTACOES.md",
            "docs/CHECKLIST_FINAL.md",
            "docs/RESUMO_EXECUTIVO.md",
            "docs/LEIA_PRIMEIRO.txt"
        ],
        "Configuração": [
            "requirements.txt"
        ],
        "Scripts": [
            "scripts/verificar_entrega.py"
        ]
    }
    
    # Arquivos opcionais mas recomendados
    optional_files = [
        "exemplos/exemplos-arquivo-configuracao (1).txt",
        "exemplos/nova_config.txt",
    ]
    
    # Arquivo crítico faltando
    critical_missing = ["docs/documentacao_visual.pdf"]
    
    total_found = 0
    total_required = sum(len(files) for files in required_files.values())
    
    # Verifica arquivos obrigatórios
    for category, files in required_files.items():
        print(f"\n📁 {category}:")
        for file in files:
            if os.path.exists(file):
                size = os.path.getsize(file)
                print(f"   ✅ {file:40} ({size:,} bytes)")
                total_found += 1
            else:
                print(f"   ❌ {file:40} (NÃO ENCONTRADO)")
    
    # Verifica arquivos opcionais
    print(f"\n📂 Arquivos Opcionais:")
    for file in optional_files:
        if os.path.exists(file):
            size = os.path.getsize(file)
            print(f"   ℹ️  {file:40} ({size:,} bytes)")
    
    # Verifica arquivo crítico
    print(f"\n⚠️  Arquivo Crítico Pendente:")
    for file in critical_missing:
        if os.path.exists(file):
            print(f"   ✅ {file}")
        else:
            print(f"   ❌ {file} - CRIAR ESTE ARQUIVO!")
    
    # Resumo
    print("\n" + "=" * 70)
    print(f"📊 RESUMO:")
    print(f"   Arquivos encontrados: {total_found}/{total_required}")
    print(f"   Percentual completo: {(total_found/total_required)*100:.1f}%")
    
    # Verifica arquivos compactados (não devem existir!)
    print("\n" + "=" * 70)
    print("⚠️  VERIFICAÇÃO DE ARQUIVOS COMPACTADOS (NÃO DEVE TER NENHUM!):")
    compressed_extensions = ['.zip', '.rar', '.7z', '.tar', '.gz']
    found_compressed = []
    
    for file in os.listdir('.'):
        if any(file.endswith(ext) for ext in compressed_extensions):
            found_compressed.append(file)
    
    if found_compressed:
        print("   ❌ ATENÇÃO! Arquivos compactados encontrados:")
        for file in found_compressed:
            print(f"      - {file}")
        print("   ⚠️  REMOVA-OS! Envio de arquivos compactados = NOTA ZERO")
    else:
        print("   ✅ Nenhum arquivo compactado encontrado (correto!)")
    
    # Instruções finais
    print("\n" + "=" * 70)
    print("📝 PRÓXIMOS PASSOS:")
    print("=" * 70)
    
    if total_found == total_required and not os.path.exists("docs/documentacao_visual.pdf"):
        print("1. ⚠️  CRIAR 'docs/documentacao_visual.pdf' com screenshots")
        print("2. ✅ Executar este script novamente para verificar")
        print("3. ✅ Enviar TODOS os arquivos INDIVIDUALMENTE no Moodle")
        print("4. ❌ NÃO comprimir os arquivos!")
    elif total_found == total_required and os.path.exists("docs/documentacao_visual.pdf"):
        print("✅ TUDO PRONTO PARA ENTREGA!")
        print("\n📤 INSTRUÇÕES DE ENVIO:")
        print("   1. Acesse o Moodle")
        print("   2. Encontre a atividade de entrega do projeto")
        print("   3. Envie CADA arquivo INDIVIDUALMENTE (não comprimir!)")
        print("   4. Verifique que todos os arquivos foram enviados")
        print("   5. Confirme a entrega")
    else:
        print("❌ Alguns arquivos estão faltando!")
        print("   Verifique os itens marcados com ❌ acima")
    
    print("\n" + "=" * 70)
    print("📂 Estrutura do Projeto:")
    print("=" * 70)
    print("  ProjSO/")
    print("  ├── *.py ................... Código principal")
    print("  ├── requirements.txt ....... Dependências")
    print("  ├── docs/ .................. Documentação")
    print("  ├── tests/ ................. Testes")
    print("  ├── exemplos/ .............. Exemplos de configuração")
    print("  └── scripts/ ............... Scripts utilitários")
    print("=" * 70)

if __name__ == "__main__":
    check_files()
