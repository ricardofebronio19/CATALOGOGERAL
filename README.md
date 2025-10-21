# Catálogo de Peças v1.7.0

Este repositório contém uma aplicação Flask para gerenciar um catálogo de peças com sistema de atualização automática e interface moderna.

## 🚀 Novidades v1.7.0

### ✨ Sistema de Atualização Automática
- Verificação automática de novas versões a cada 6 horas
- Banner interativo para administradores
- Download e instalação automática
- Interface moderna com animações

### 🎨 Melhorias Visuais
- Destaque das montadoras com fundo gradiente
- Alternância de cores nas linhas dos veículos
- Menu principal modernizado
- Responsividade aprimorada

### 🔧 Correções de Bugs
- Corrigido erro de IntegrityError ao adicionar produtos
- Autopreenchimento da montadora funcionando
- Melhor validação de formulários

## 📁 Estrutura do Projeto

- `run.py` - entrypoint/CLI
- `app.py` - factory do Flask com sistema de atualização
- `models.py` - modelos SQLAlchemy
- `routes.py` - rotas organizadas em blueprints
- `importar_pecas.py`, `validar_csv.py` - scripts de importação
- `vincular_imagens.py` - script para ligar imagens aos produtos
- `build.bat` - script para empacotar com PyInstaller e criar instalador
- `prepare_release.ps1` - script para preparar releases

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

## Criar release e enviar executável (opcional)

Se você quer criar um release no GitHub e anexar o executável gerado em `dist\CatalogoDePecas.exe`, use o script PowerShell `scripts\create_release.ps1`.

Passos:

1. Gere um Personal Access Token (PAT) no GitHub com escopo `repo` e exporte para a variável de ambiente `GITHUB_TOKEN`:

```powershell
$env:GITHUB_TOKEN = 'seu_token_aqui'
```

2. Execute o script (ajuste a tag/nome se necessário):

```powershell
PowerShell -File .\scripts\create_release.ps1 -TagName "v1.5" -ReleaseName "CatalogoDePecas v1.5"
```

O script criará o release e enviará `dist\CatalogoDePecas.exe` como asset.

