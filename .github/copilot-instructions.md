# Copilot Instructions for AI Agents

## Visão Geral do Projeto
Este é um sistema de catálogo de peças automotivas desenvolvido em Python usando Flask, SQLAlchemy e Flask-Login. O objetivo é gerenciar produtos, aplicações, usuários e configurações visuais, com interface web e persistência local de dados.

## Estrutura e Componentes Principais
- `app.py`: Núcleo da aplicação Flask. Define modelos, rotas, autenticação, lógica de uploads, backup/restauração e configuração visual.
- `run.py`: Inicializa o banco de dados e executa o servidor de produção (Waitress), abrindo o navegador automaticamente.
- `static/` e `templates/`: Arquivos estáticos (CSS, imagens) e templates Jinja2 para a interface web.
- `setup_script.iss`: Script Inno Setup para empacotamento e instalação no Windows.
- Dados e uploads são salvos em `%APPDATA%/CatalogoDePecas` para garantir persistência e isolamento do usuário.

## Fluxos e Convenções Específicas
- **Banco de Dados**: SQLite, inicializado automaticamente se ausente. Modelos principais: `Produto`, `Aplicacao`, `User`.
- **Uploads**: Imagens de produtos e logos são salvas em `APPDATA/CatalogoDePecas/uploads`.
- **Backup/Restauração**: Rotas protegidas permitem baixar/restaurar todo o diretório de dados como ZIP.
- **Autenticação/Administração**: Usuários e permissões via Flask-Login. O primeiro usuário criado é admin.
- **Configuração Visual**: Cores e logo customizáveis via painel/admin, persistidos em `config.json`.
- **Execução**: Use `python run.py` para produção (porta 8000, abre navegador). Para inicializar apenas o banco: `python run.py init-db`.
- **Empacotamento**: Use PyInstaller para gerar executável, depois o Inno Setup (`setup_script.iss`) para criar instalador Windows.

## Padrões e Dicas para Agentes
- Sempre use as funções utilitárias já presentes para configuração, busca e manipulação de dados.
- Novas rotas devem seguir o padrão de autenticação e uso de `@login_required` quando necessário.
- Para novos modelos, adicione ao `app.py` e atualize a inicialização do banco.
- Templates devem ser criados/alterados em `templates/` e seguir o uso de variáveis injetadas pelo contexto Flask.
- Para alterações visuais, edite `static/style.css` e utilize as configurações dinâmicas de cor/logo.
- Não armazene dados sensíveis ou arquivos de usuário fora do diretório `APPDATA/CatalogoDePecas`.

## Exemplos de Arquivos-Chave
- `app.py`: Modelos, rotas, lógica de backup, autenticação, configuração visual.
- `run.py`: Inicialização e execução do servidor.
- `setup_script.iss`: Empacotamento e instalação.
- `static/style.css`: Customização visual.
- `templates/`: Interface web.

## Integrações e Dependências
- Flask, Flask-Login, Flask-SQLAlchemy, Waitress, Werkzeug, PyInstaller, Inno Setup.
- Não há dependências externas de APIs ou serviços web.

---

Seções incompletas ou dúvidas sobre fluxos específicos? Peça exemplos ou esclarecimentos ao usuário.