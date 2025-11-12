<!-- Instruções para agentes de código (Copilot / IA) específicas deste repositório -->

# Projeto: Catálogo de Peças (Flask + PyInstaller)

Sistema desktop de catálogo de peças automotivas com busca avançada, gestão de similares, sistema de atualização automática e empacotamento para Windows.

## Arquitetura de alto nível

### Camadas da aplicação
- **App factory**: `create_app()` em `app.py` — inicializa Flask, SQLAlchemy (`db`), Flask-Login (`login_manager`)
- **Blueprints**: 3 módulos principais em `routes.py`:
  - `main_bp`: busca, visualização, API AJAX
  - `auth_bp`: autenticação (login/logout)
  - `admin_bp`: CRUD produtos/aplicações, gestão de usuários, importação CSV, backup/restore
- **Entrypoints**:
  - `run.py` — CLI com subcomandos (`run`, `reset-db`, `link-images`, `import-csv`) + servidor Waitress + navegador
  - `run_gui.py` — Modo desktop (janela nativa com pywebview) — mesmas funcionalidades sem navegador
- **Persistência**: SQLite com WAL mode em `%APPDATA%/CatalogoDePecas/catalogo.db`

### Modelos de dados (models.py)
- `Produto`: código único, nome, grupo, fornecedor, conversões, medidas, observações
- `Aplicacao`: veículo, ano (suporta ranges: "2010/2015", "2018/..."), motor, montadora (FK para Produto)
- `ImagemProduto`: filename, ordem (FK para Produto)
- `User`: autenticação com Flask-Login, flag `is_admin`
- `similares_association`: many-to-many para produtos similares (simétrica via `_atualizar_similares_simetricamente`)
- `SugestaoIgnorada`: marca sugestões de similares ignoradas pelo usuário

### Fluxo de busca e sugestões de similares
1. **Busca**: `_build_search_query()` em `core_utils.py` — suporta busca por termo livre, código, montadora, aplicação (veículo/motor), grupo, medidas
2. **Normalização**: `_normalize_for_search()` remove acentos/pontuação para matching case-insensitive
3. **Agrupamento**: resultados agrupados por montadora+veículo quando busca é por aplicação (ver `routes.buscar()`)
4. **Sugestões automáticas**: em `detalhe_peca()`, gera similares baseados em:
   - Conversões mútuas (código produto aparece em conversões de outro)
   - Mesmo grupo + veículo com overlap de anos (`_ranges_overlap()`)
   - Exclui sugestões marcadas em `SugestaoIgnorada`

## Workflows de desenvolvimento

### Setup local
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
# Modo navegador (desenvolvimento):
python run.py run --host 127.0.0.1 --port 5000
# Modo desktop (produção):
python run_gui.py
```

### CLI commands (run.py)
- `python run.py run --host 0.0.0.0 --port 8000 --no-browser` — servidor produção
- `python run.py reset-db` — recria DB (confirma interativamente)
- `python run.py link-images` — varre `uploads/` e vincula imagens aos produtos por código
- `python run.py import-csv <file.csv>` — importa produtos de CSV (ver `utils/import_utils.py`)

### Build e distribuição
```powershell
# Build PyInstaller (onefile) - modo navegador
.\build.bat
# Build PyInstaller (onefile) - modo desktop/GUI
.\build_gui.bat
# Build + staging + instalador Inno Setup
set CREATE_INSTALLER=1
set INCLUDE_DB=1
.\build.bat  # ou .\build_gui.bat para versão desktop
```
- Saída navegador: `dist/CatalogoDePecas.exe` (abre browser)
- Saída desktop: `dist/CatalogoDePecas.exe` (janela nativa via pywebview)
- Instalador: `Output/CatalogoDePecas_Setup_v*.exe` (Inno)
- Build detecta `.venv/Scripts/python.exe` ou usa `python` do PATH
- `INCLUDE_DB=1` copia DB local para `data/catalogo.db` e embute no executável

### Tasks VS Code
- **Build + Staging (no Inno)**: empacota sem instalador (modo navegador)
- **Build + Staging + Installer (Inno)**: gera instalador completo (requer Inno Setup 6)
- Para build modo desktop: execute `.\build_gui.bat` manualmente

### Modo Desktop vs Navegador
- **run.py**: Servidor Flask + abre navegador padrão (desenvolvimento/acesso remoto)
- **run_gui.py**: Servidor Flask + janela nativa pywebview (produção/usuários finais)
- Ambos usam o mesmo código Flask — diferença apenas na UI
- Modo desktop: servidor escuta em 127.0.0.1 apenas (mais seguro)
- Ver `GUIA_VERSAO_DESKTOP.md` para detalhes completos

### Melhorias visuais desktop
- **Splash screen**: animado durante carregamento (gradiente roxo, logo pulando)
- **Indicadores**: status de conexão (bolinha verde), badge "Desktop", barra de loading
- **Atalhos**: Ctrl+R (reload), F11 (fullscreen), Ctrl+Q (quit), Ctrl+0/+/- (zoom)
- **Animações**: fade-in, hover 3D, ripple em botões, smooth scroll
- **API JS**: `window.pywebview.api` expõe funções Python (get_version, minimize_window, etc)
- **Toast notifications**: `showToast(msg, type)` disponível globalmente
- **CSS/JS enhancements**: `static/gui_enhancements.{css,js}` carregados automaticamente em `base.html`
- Ver `MELHORIAS_VISUAIS_DESKTOP.md` para documentação completa

## Convenções e padrões do projeto

### Normalização de dados
- **UPPERCASE**: campos de formulário (nome, código, grupo, etc.) são convertidos para maiúsculas em `routes.py` ao salvar
- **Busca**: usa `_normalize_for_search()` para remover acentos/case/pontuação antes de comparar strings

### Upload de imagens
- **Caminho**: salvos em `APP_DATA_PATH/uploads` (ex: `%APPDATA%/CatalogoDePecas/uploads`)
- **Filename pattern**: `{codigo}_{timestamp}.{ext}` gerado via `secure_filename()`
- **Validação**: `allowed_file()` em `core_utils.py` — aceita png, jpg, jpeg, gif, webp
- **Compartilhamento**: múltiplos produtos podem referenciar a mesma imagem (exclusão verifica `ImagemProduto.query` antes de remover arquivo físico)

### Jinja2 customizations
- **Filtros globais**: `highlight` (destaca termos de busca), `merge` (mescla dicts para URLs de paginação)
- **Context processor**: injeta `config_aparencia`, `is_admin`, `app_version`, `update_info`, `search_args`, `render_pagination`
- **Macro global**: `templates/partials/_pagination.html` carregada em `register_jinja_helpers()` — nunca renomeie sem atualizar `app.py`

### Sistema de atualização automática
1. `check_for_updates()` (app.py): busca `update_config.json` no GitHub a cada 6 horas
2. Usa ETag/Last-Modified para economizar requests (cache em `APP_DATA_PATH/update_config_meta.json`)
3. Compara versões via `packaging.version.parse()`
4. Download de update: salva `update_package.zip` em `APP_DATA_PATH` e cria trigger `RESTART_FOR_UPDATE`
5. `executar_atualizacao()` (run.py): extrai zip para diretório do executável e reinicia

### Backup/Restore
- **Backup**: exporta DB como SQL dump + copia `APP_DATA_PATH` inteiro para zip (rota `/admin/backup`)
- **Restore**: verifica `backup_para_restaurar.zip` e trigger `RESTART_REQUIRED` ao iniciar — extrai, recria DB de SQL, remove trigger

## Armadilhas e pontos críticos

### PyInstaller frozen mode
- `sys._MEIPASS` usado para acessar templates/static quando congelado
- `version.json` gerado por `build.bat` e embarcado — lido por `_carregar_versao()` em `app.py`
- Nunca hardcode caminhos relativos sem checar `getattr(sys, 'frozen', False)`

### Aplicações com anos range
- Parsing: `_parse_year_range()` converte "2010/2015" em `(2010, 2015)`, "2018/..." em `(2018, 9999)`
- Overlap: `_ranges_overlap()` determina se dois produtos se aplicam ao mesmo período
- SQL: anos são strings — parsing e comparação em Python (não em SQL)

### Aplicações sem ID ao criar
- **BUG conhecido**: nunca envie `id` vazio ao criar `Aplicacao` — filtre com `{k: v for k, v in data.items() if k != "id"}` (ver `adicionar_peca()` e `editar_peca()`)

### Cache de datalists
- `_get_form_datalists()` em `core_utils.py`: cache in-memory (5min TTL) para grupos/fornecedores/montadoras
- Thread-safe com `_cache_lock`
- Cache invalida automaticamente após timeout — não precisa flush manual

### Encoding/Unicode no Windows
- `run.py` força `PYTHONIOENCODING=utf-8` e reconfigura `sys.stdout`/`stderr` para evitar `UnicodeEncodeError` em consoles cp1252

## Testes

### Estrutura
- `tests/test_aplicacao_form.py`: testa que criar produto com aplicação não envia `id` vazio
- `tests/smoke_import.csv`: arquivo de teste para importação CSV
- **Não há testes unitários abrangentes** — confie em smoke tests manuais

### Rodar testes
```powershell
pytest tests/
```

## Exemplos práticos

### Adicionar rota AJAX que retorna JSON
```python
@main_bp.route("/api/minha_rota")
@login_required  # se autenticação necessária
def minha_rota():
    termo = request.args.get("q", "").strip()
    resultados = Produto.query.filter(Produto.nome.ilike(f"%{termo}%")).limit(10).all()
    return {"items": [{"id": p.id, "nome": p.nome} for p in resultados]}
```

### Servir arquivo estático fora de static/
```python
# Em app.py (create_app):
@app.route("/custom/<filename>")
def custom_file(filename):
    return send_from_directory(os.path.join(APP_DATA_PATH, "custom"), filename)
```

### Filtrar produtos com aplicações em range de ano
```python
# Em routes.py:
from core_utils import _parse_year_range, _ranges_overlap

def buscar_por_ano(ano_target: int):
    candidatos = Produto.query.options(db.joinedload(Produto.aplicacoes)).all()
    resultados = []
    for p in candidatos:
        for app in p.aplicacoes:
            ano_range = _parse_year_range(app.ano)
            if ano_range != (-1, -1) and _ranges_overlap(ano_range, (ano_target, ano_target)):
                resultados.append(p)
                break
    return resultados
```

## Checklist antes de commit

- [ ] Campos de formulário normalizados para UPPERCASE ao salvar?
- [ ] `allowed_file()` usado para validar uploads?
- [ ] Nunca enviar `id` vazio ao criar `Aplicacao`?
- [ ] Templates parciais existem em `templates/partials/` se usados?
- [ ] Paths consideram `sys._MEIPASS` quando relevante para PyInstaller?
- [ ] Encoding UTF-8 explícito ao abrir arquivos?
- [ ] Transações DB com try/except + rollback?

## Próximos passos sugeridos

- Migrar para Flask-Migrate (Alembic) para schema migrations
- Adicionar testes de integração para rotas admin
- Externalizar storage de uploads (S3/CDN) para multi-instância
- Implementar busca full-text (FTS5) para melhor performance em grandes DBs

---
**Versão atual**: v1.8.0 (ver `version.json`)  
**Maintainer**: ricardofebronio19  
**Repositório**: ricardofebronio19/CATALOGOGERAL
