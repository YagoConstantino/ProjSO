# Makefile (Multiplataforma para Windows e Linux)

# --- Configuração ---
APP_NAME = SimuladorEscalonamento
MAIN_SCRIPT = main.py
VENV_DIR = venv

# --- Detecção de SO e Configuração de Comandos ---
# Define comandos e caminhos padrão (para Linux/macOS)
PYTHON_CMD = python3
VENV_BIN_SUBDIR = bin

# Detecta se estamos no Windows
ifeq ($(OS),Windows_NT)
	PYTHON_CMD = python
	VENV_BIN_SUBDIR = Scripts
endif

# Define os caminhos dos executáveis do venv
# Usamos '/' pois o GNU Make (mesmo no Windows) entende
VENV_PIP = $(VENV_DIR)/$(VENV_BIN_SUBDIR)/pip
VENV_PYINSTALLER = $(VENV_DIR)/$(VENV_BIN_SUBDIR)/pyinstaller

# Define comandos de limpeza cross-platform usando Python
# O '-' no início ignora erros (ex: se a pasta não existir)
CLEAN_BUILD = -$(PYTHON_CMD) -c "import shutil; shutil.rmtree('build', ignore_errors=True)"
CLEAN_DIST = -$(PYTHON_CMD) -c "import shutil; shutil.rmtree('dist', ignore_errors=True)"
CLEAN_VENV = -$(PYTHON_CMD) -c "import shutil; shutil.rmtree('$(VENV_DIR)', ignore_errors=True)"
CLEAN_SPEC = -$(PYTHON_CMD) -c "import os, glob; [os.remove(f) for f in glob.glob('*.spec')]"


# --- Alvos (Targets) ---

# Alvo padrão: 'make' ou 'make all' executará 'build'
all: build

# Cria o ambiente virtual
# O alvo é um arquivo "marcador" que é criado pelo venv
$(VENV_DIR)/pyvenv.cfg:
	@echo "-> Criando ambiente virtual em $(VENV_DIR)..."
	$(PYTHON_CMD) -m venv $(VENV_DIR)

# Instala as dependências do requirements.txt
# Depende que o arquivo marcador do venv exista
install: $(VENV_DIR)/pyvenv.cfg
	@echo "-> Instalando dependencias (pyinstaller)..."
	$(VENV_PIP) install -r requirements.txt

# Constrói o executável standalone (SEM Ghostscript embutido)
build: install
	@echo "-> Construindo o executavel standalone..."
	$(VENV_PYINSTALLER) --onefile --windowed --name=$(APP_NAME) $(MAIN_SCRIPT)
	@echo "------------------------------------------------------"
	@echo "-> Build concluido!"
	@echo "-> Seu executavel esta em: dist/$(APP_NAME).exe"
	@echo "------------------------------------------------------"
	@echo ""
	@echo "AVISO: Ghostscript NAO foi embutido!"
	@echo "Usuarios precisarao instalar Ghostscript para exportar PNG."
	@echo "Para build COM Ghostscript embutido, use: make build-full"
	@echo ""

# Constrói o executável COM Ghostscript embutido (recomendado para distribuição)
build-full: install
	@echo "-> Construindo executavel COM Ghostscript embutido..."
	$(PYTHON_CMD) build_with_ghostscript.py
	@echo "------------------------------------------------------"
	@echo "-> Build completo concluido!"
	@echo "-> Seu executavel esta em: dist/$(APP_NAME).exe"
	@echo "------------------------------------------------------"

# Executa o simulador diretamente (sem build)
run:
	@echo "-> Executando simulador diretamente..."
	$(PYTHON_CMD) $(MAIN_SCRIPT)

# Executa os testes
test:
	@echo "-> Executando testes automatizados..."
	$(PYTHON_CMD) tests/test_suite.py

# Limpa os arquivos gerados pelo PyInstaller (de forma multiplataforma)
clean:
	@echo "-> Limpando arquivos de build..."
	$(CLEAN_BUILD)
	$(CLEAN_DIST)
	$(CLEAN_SPEC)
	@echo "-> Limpeza concluida."

# Alvo para remover o ambiente virtual também
clean-all: clean
	@echo "-> Removendo ambiente virtual..."
	$(CLEAN_VENV)
	@echo "-> Limpeza total concluida."

# Alvo 'help' para listar os comandos
# Adiciona .PHONY para garantir que 'help' sempre execute
.PHONY: all install build build-full run test clean clean-all help
help:
	@echo "=========================================="
	@echo "  SIMULADOR DE SISTEMA OPERACIONAL"
	@echo "=========================================="
	@echo ""
	@echo "Comandos disponiveis:"
	@echo "  make             - (Padrao) Cria venv, instala e gera .exe"
	@echo "  make build       - Gera executavel SEM Ghostscript"
	@echo "  make build-full  - Gera executavel COM Ghostscript (RECOMENDADO)"
	@echo "  make install     - Cria venv e instala dependencias"
	@echo "  make run         - Executa direto sem build"
	@echo "  make test        - Executa os testes"
	@echo "  make clean       - Remove arquivos de build"
	@echo "  make clean-all   - Remove tudo (incluindo venv)"
	@echo "  make help        - Mostra esta ajuda"
	@echo ""
	@echo "Build Recomendado para Distribuicao:"
	@echo "  make build-full  -> Gera .exe com Ghostscript embutido"
	@echo "  Usuarios NAO precisarao instalar Ghostscript!"
	@echo ""
	@echo "Fluxo completo:"
	@echo "  1. make build-full  -> Gera dist/SimuladorEscalonamento.exe"
	@echo "  2. Execute o .exe da pasta dist/"
	@echo ""
