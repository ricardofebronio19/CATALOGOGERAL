# Catálogo de Peças

Este repositório contém uma aplicação Flask para gerenciar um catálogo de peças.

Conteúdo principal:
- `run.py` - entrypoint/CLI
- `app.py` - factory do Flask
- `models.py` - modelos SQLAlchemy
- `importar_pecas.py`, `validar_csv.py` - scripts de importação
- `vincular_imagens.py` - script para ligar imagens aos produtos
- `build.bat` - script para empacotar com PyInstaller e criar instalador (Inno Setup)

Como preparar e rodar localmente

1. Crie um ambiente virtual e instale dependências:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

2. Rodar localmente (desenvolvimento):

```powershell
.\.venv\Scripts\python.exe run.py run --host 127.0.0.1 --port 5000
```

3. Empacotar (gerar executável):

```powershell
.\build.bat
# para incluir DB local antes do build:
set INCLUDE_DB=1
.\build.bat
```

Notas
- O `build.bat` pode pular a etapa do Inno Setup se o compilador não estiver instalado. Para gerar instalador, instale Inno Setup 6 e execute:

```powershell
set CREATE_INSTALLER=1
.\build.bat
```

Se quiser que eu faça o push para um repositório remoto no GitHub, me dê o nome do repositório remoto (ex.: `ricardofebronio19/CATALOGOGERAL`) ou me autorize a criar instruções para você executar localmente.
