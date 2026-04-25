# Copilot Instructions - Catálogo de Peças

## Arquitetura do Projeto

Este é um **sistema de catálogo de peças** Flask com interface web e aplicação desktop híbrida:

- **Backend**: Flask + SQLAlchemy com banco SQLite local
- **Frontend**: Templates Jinja2 + CSS/JS customizados
- **Desktop**: PyWebview wrapper opcional (modo GUI nativo)
- **Deploy**: PyInstaller para executáveis standalone

## Pontos de Entrada e Modos de Execução

- `run.py` - Servidor web (Waitress + fallback Flask dev server)
- `run_gui.py` - Interface desktop via PyWebview com menu nativo
- `build.bat` - Build automatizado (PyInstaller + Inno Setup)

## Estrutura de Dados Central

### Modelos Principais (`models.py`)
- `Produto` - Peça principal com código único por fornecedor
- `Aplicacao` - Veículos compatíveis (many-to-many com Produto)
- `ImagemProduto` - Imagens ordenadas por produto
- `similares_association` - Relacionamento M:M simétrico entre produtos

### Padrões de Busca Críticos
- **Normalização**: `_normalize_for_search()` remove acentos/pontuação
- **Busca flexível**: `_build_search_query()` em `core_utils.py`
- **Constraint único**: `codigo + fornecedor` deve ser único

## Convenções Específicas do Projeto

### Gerenciamento de Dados
- **APP_DATA_PATH**: Diretório dinâmico para banco SQLite e uploads
- **Backup automático**: Scripts em `scripts/backup_db.py`
- **Import CSV**: `importar_pecas.py` com parsing de aplicações estruturado

### Padrões de Rota (`routes.py`)
- Blueprint único sem prefixo para todas as rotas
- **Auth obrigatório**: Decorador `@login_required` em operações de escrita
- **Admin check**: `current_user.is_admin` para operações sensíveis

### Interface Desktop
- **Menu nativo**: Configurado em `run_gui.py` com ações de sistema
- **CSS específico**: `gui_enhancements.css` para ajustes desktop
- **Thread separation**: Flask server roda em thread separada

## Fluxos de Desenvolvimento

### Build & Deploy
```bash
# Build completo com versionamento Git
build.bat  # Cria executável + instalador

# GUI development
python run_gui.py
```

### Debugging Database
```bash
# Scripts utilitários em /scripts/
python scripts/inspect_db.py        # Análise do banco
python scripts/sql_check.py         # Validação queries
python scripts/backup_db.py         # Backup manual
```

### Import de Dados
- **Formato CSV**: Colunas específicas para código, fornecedor, aplicações
- **Parsing inteligente**: Reconhece padrões de anos, motores, veículos
- **Validação**: `validar_csv.py` antes do import

## Integrações Críticas

### Sistema de Arquivos
- **Uploads**: Pasta `APP_DATA_PATH/uploads` para imagens
- **Database**: SQLite em `APP_DATA_PATH/catalogo.db`
- **Config**: JSON dinâmico para aparência/configurações

### Threading & Background
- **Update checker**: Thread para verificar atualizações automáticas
- **Image downloads**: Async download de URLs externas
- **GUI threading**: Separação Flask server/webview UI

## Padrões de Código Importantes

### Encoding & Unicode
- **Força UTF-8**: Configuração explícita em pontos de entrada
- **Normalização**: Tratamento consistente de acentos em buscas
- **Windows compatibility**: Workarounds para CP1252/console issues

### Error Handling
- **Graceful fallbacks**: Waitress → Flask dev server
- **Import resilience**: Continua processamento mesmo com erros parciais
- **Database constraints**: Unique constraints com mensagens user-friendly

### Security
- **CSRF**: Flask-Login com secret key configurável
- **File uploads**: Validação de extensões permitidas
- **Admin separation**: Operações críticas restritas a administradores

---

**Quando modificar este projeto**: Sempre considere compatibilidade com modo desktop, encoding UTF-8, e mantenha padrões de normalização para buscas de produtos.