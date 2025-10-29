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
	@echo "-> Instalando dependências (pyinstaller)..."
	$(VENV_PIP) install -r requirements.txt

# Constrói o executável standalone
build: install
	@echo "-> Construindo o executável standalone..."
	$(VENV_PYINSTALLER) --onefile --windowed --name=$(APP_NAME) $(MAIN_SCRIPT)
	@echo "------------------------------------------------------"
	@echo "-> Build concluído!"
	@echo "-> Seu executável está em: dist/"
	@echo "------------------------------------------------------"

# Limpa os arquivos gerados pelo PyInstaller (de forma multiplataforma)
clean:
	@echo "-> Limpando arquivos de build..."
	$(CLEAN_BUILD)
	$(CLEAN_DIST)
	$(CLEAN_SPEC)
	@echo "-> Limpeza concluída."

# Alvo para remover o ambiente virtual também
clean-all: clean
	@echo "-> Removendo ambiente virtual..."
	$(CLEAN_VENV)
	@echo "-> Limpeza total concluída."

# Alvo 'help' para listar os comandos
# Adiciona .PHONY para garantir que 'help' sempre execute
.PHONY: all install build clean clean-all help
help:
	@echo "Comandos disponíveis:"
	@echo "  make all       - (Padrão) Cria o ambiente virtual, instala e constrói o app."
	@echo "  make build     - Apenas constrói o app (requer 'make install' primeiro)."
	@echo "  make install   - Cria o venv e instala as dependências."
	@echo "  make clean     - Remove os arquivos de build (dist/, build/, *.spec)."
	@echo "  make clean-all - Remove tudo, incluindo o ambiente virtual."