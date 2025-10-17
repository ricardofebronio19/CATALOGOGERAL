<!-- Instruções para agentes de código (Copilot / IA) específicas deste repositório -->

# Resumo rápido

Projeto: Catálogo de Peças (Flask)
- App principal: `create_app()` em `app.py`
- Entrypoint CLI / servidor: `run.py` (usa `waitress` como servidor de produção)
- Banco de dados: SQLite em `%APPDATA%/CatalogoDePecas/catalogo.db` (variável `APP_DATA_PATH` em `app.py`)

# Objetivo deste arquivo
Fornecer ao agente as informações essenciais para ser imediatamente produtivo neste repositório: arquitetura, padrões, comandos para executar e convenções de código.

# Arquitetura e fluxo principal
- App factory: `create_app()` em `app.py` inicializa Flask, SQLAlchemy (`db`) e Flask-Login (`login_manager`).
- Blueprints: registrados em `create_app()` — `main_bp`, `auth_bp`, `admin_bp` (definidos em `routes.py`).
- Persistência: modelos em `models.py` (Produto, Aplicacao, ImagemProduto, User). Relação many-to-many para "similares" via tabela `similares_association`.
- Uploads/Uploads path: arquivos enviados salvos em `APP_DATA_PATH/uploads`. A rota que serve uploads é definida dinamicamente em `create_app()` (`/uploads/<filename>`).
- Templates: pasta `templates/` contém macros em `templates/partials/` — a macro de paginação `partials/_pagination.html` é carregada globalmente pelo context processor em `app.py`.

# Como executar / workflows
- Ambiente virtual: projeto assume uso de virtualenv (ex.: `.venv`).
- Instalar dependências: `requirements.txt` lista Flask, Flask-SQLAlchemy, Flask-Login, requests, waitress.
- Rodar localmente (modo produção leve): `python run.py` (abre servidor Waitress em 0.0.0.0:8000 por padrão). Parâmetros:
  - `python run.py run --host 0.0.0.0 --port 8000` (não abre navegador com `--no-browser`).
- Comandos utilitários:
  - `python run.py reset-db` — recria todas as tabelas (pergunta de confirmação no CLI).
  - Importação / ligação de imagens: scripts autônomos `importar_pecas.py`, `vincular_imagens.py` — execute diretamente quando necessário.

# Padrões e convenções do código
- Strings de campos (nome, código, etc.) são normalizadas para UPPERCASE ao salvar via formulários (ver `routes.py`).
- Upload de imagens: use `image_utils.download_image_from_url` ou `request.files` com `allowed_file()` do `core_utils.py`.
- Banco: `inicializar_banco(app, reset=False)` cria o DB e um usuário admin com senha temporária se necessário. O app usa WAL (PRAGMA journal_mode=WAL).
- Jinja: filtros e context processors são registrados em `register_jinja_helpers(app)` (em `app.py`). Evite sobrescrever `render_pagination` — use a macro global.

# Pontos frágeis / armadilhas observadas
- Templates parciais: `app.py` carrega `partials/_pagination.html` no context processor. Se esse arquivo não existir, o app lançará `jinja2.exceptions.TemplateNotFound` (ver erro de execução). Verifique `templates/partials/` antes de alterar o carregamento.
- Caminho de dados: o app grava em `%APPDATA%/CatalogoDePecas` (no Windows). Localizar arquivos (DB, uploads, config.json) aqui em tempo de desenvolvimento.
- Execução congelada (PyInstaller): há handling em `create_app()` para `sys._MEIPASS` — mantenha compatibilidade de caminhos se modificar comportamento de empacotamento.

# Integrações e dependências externas
- Atualização: `check_for_updates()` busca `update_config.json` no GitHub — alterações a essa URL afetam o comportamento de update.
- HTTP client: usa `requests` com timeout razoável; trate exceções de rede quando modificar esse fluxo.

# Exemplos úteis retirados do código
- Servir uploads (definido em `app.py`):
  - Route: `/uploads/<filename>` -> `send_from_directory(app.config['UPLOAD_FOLDER'], filename)`
- Macro de paginação (carregada globalmente): `templates/partials/_pagination.html` — use `render_pagination(pagination, 'main.buscar', search_args)` nos templates.

# Quando editar rotas/templates
- Ao renomear ou mover `templates/partials/_pagination.html`, atualize `register_jinja_helpers()` em `app.py` para carregar a nova localização ou remover a injeção global.
- Ao alterar modelos (`models.py`), lembre-se de atualizar `inicializar_banco()` e migrar dados manualmente (não há migrations automáticas incluídas).

# Checks rápidos para o agente antes de abrir PR
- Verificar existência de `templates/partials/_pagination.html` ao tocar `app.py` (para evitar TemplateNotFound).
- Não assumir que `templates` está embutido; em builds com PyInstaller, `template_folder` muda para `sys._MEIPASS`.
- Checar `APP_DATA_PATH` em ambientes CI/execução para garantir permissões de escrita.

# Perguntas úteis para o autor humano
- Deseja adicionar migrações (Alembic) no repositório?
- Há planos para separar upload storage (ex: S3) no futuro? Isso afeta onde os agentes devem focar refatores.

---
Se algo estiver incompleto ou você quiser que eu expanda algum bloco (ex.: exemplos de refatoração, testes unitários rápidos, ou migrar para Flask Migrate), me diga e eu ajusto o arquivo.
