import os
import json
import threading
import requests
import sys
from flask import Flask, send_from_directory, request
from flask_sqlalchemy import SQLAlchemy
from markupsafe import Markup
from flask_login import LoginManager, current_user
from packaging import version as pkg_version
import re
from typing import Optional

# Inicializa extensões sem associá-las a um app ainda
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login' # Aponta para o blueprint de autenticação

# --- Configurações de Atualização ---
def _carregar_versao() -> str:
    """Obtém a versão da aplicação de forma resiliente.

    Ordem:
    1) Variável de ambiente APP_VERSION (injeção no build/CI)
    2) Arquivo version.json empacotado (criado pelo build)
    3) Fallback para '1.0.0'
    """
    # 1) Ambiente
    env_version = os.getenv("APP_VERSION")
    if env_version:
        return env_version

    # 2) Arquivo version.json (no diretório do app ou no sys._MEIPASS quando congelado)
    try:
        base_dir = None
        if getattr(sys, 'frozen', False):
            base_dir = sys._MEIPASS  # type: ignore[attr-defined]
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        version_file = os.path.join(base_dir, 'version.json')
        if os.path.exists(version_file):
            with open(version_file, 'r', encoding='utf-8') as vf:
                data = json.load(vf)
                if isinstance(data, dict) and 'version' in data and data['version']:
                    return str(data['version'])
    except Exception:
        pass

    # 3) Default
    return "1.0.0"

VERSION = _carregar_versao()
UPDATE_CONFIG_URL = "https://raw.githubusercontent.com/ricardofebronio19/CATALOGOGERAL/main/update_config.json" # URL para o JSON de configuração da atualização

# Esta rota deve ser definida após a criação do objeto 'app', então será movida para depois da definição do app.


# Define o caminho base para os dados da aplicação (banco de dados, uploads)
# Usa a pasta AppData do usuário, que é um local seguro para escrita.
base_path = os.getenv('APPDATA') or os.path.expanduser('~')
APP_DATA_PATH = os.path.join(base_path, 'CatalogoDePecas')

UPLOAD_FOLDER = os.path.join(APP_DATA_PATH, 'uploads')
CONFIG_FILE = os.path.join(APP_DATA_PATH, 'config.json')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
# Lista pré-definida com as principais montadoras de automóveis no Brasil
MONTADORAS_PREDEFINIDAS = [
    'Audi',
    'BMW',
    'BYD',
    'Caoa Chery',
    'Chevrolet',
    'CITROËN',
    'Fiat',
    'Ford',
    'GWM',
    'Honda',
    'Hyundai',
    'Jeep',
    'Kia',
    'Land Rover',
    'Mercedes-Benz',
    'Mitsubishi',
    'Nissan',
    'Peugeot',
    'Ram',
    'Renault',
    'Toyota',
    'Volkswagen',
    'Volvo'
]

# Determina o caminho base para templates e arquivos estáticos
# Nota: a criação das pastas de dados foi movida para dentro de create_app()
# para evitar efeitos colaterais durante a importação do módulo (útil em
# testes que sobrescrevem APP_DATA_PATH antes de criar a app).
# --- Funções de Configuração de Aparência ---
def carregar_config_aparencia():
    """Carrega as configurações de aparência do arquivo JSON de forma segura."""
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            # Garante que as chaves essenciais existam
            config.setdefault('cor_principal', '#ff6600')
            config.setdefault('logo_path', None)
            return config
    except (FileNotFoundError, json.JSONDecodeError):
        # Retorna um dicionário padrão se o arquivo não existir ou for inválido
        return {'cor_principal': '#ff6600', 'logo_path': None}

def salvar_config_aparencia(config):
    """Salva as configurações de aparência no arquivo JSON."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)

# --- Configuração do Flask-Login ---
@login_manager.user_loader
def load_user(user_id):
    """Função para carregar o usuário a partir do ID armazenado na sessão."""
    # Importa o modelo User aqui para evitar importação circular
    from models import User
    return db.session.get(User, int(user_id))

def create_app():
    """
    Cria e configura a instância da aplicação Flask (App Factory Pattern).
    """
    if getattr(sys, 'frozen', False):
        # Se estiver rodando como um executável PyInstaller
        template_folder = os.path.join(sys._MEIPASS, 'templates')
        static_folder = os.path.join(sys._MEIPASS, 'static')
        app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
    else:
        # Se estiver rodando como um script Python normal
        app = Flask(__name__)

    # --- Configuração da Aplicação ---
    # Gera uma chave secreta se não existir, para maior segurança.
    config_aparencia = carregar_config_aparencia()
    if 'secret_key' not in config_aparencia:
        config_aparencia['secret_key'] = os.urandom(24).hex()
        salvar_config_aparencia(config_aparencia)

    app.config['SECRET_KEY'] = config_aparencia['secret_key']
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(APP_DATA_PATH, "catalogo.db")
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'connect_args': {'timeout': 15}, 
        'pool_pre_ping': True
    }
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # Garante que as pastas de dados existam (cria com o APP_DATA_PATH atual)
    try:
        os.makedirs(APP_DATA_PATH, exist_ok=True)
        os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    except Exception:
        # Não falhar na criação de pastas durante import (tests podem manipular paths)
        pass

    # --- Inicialização das Extensões ---
    db.init_app(app)
    login_manager.init_app(app)

    # --- Registro de Blueprints (Rotas) ---
    from routes import main_bp, auth_bp, admin_bp
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)

    # --- Filtros e Context Processors do Jinja2 ---
    register_jinja_helpers(app)

    # --- Funções e Rotas Auxiliares ---
    @app.route('/uploads/<filename>')
    def uploaded_file(filename):
        """Serve os arquivos da pasta de uploads que está fora da 'static'."""
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    # Associa a função de verificação de atualizações ao objeto app
    app.check_for_updates = check_for_updates

    return app

def register_jinja_helpers(app):
    """Registra filtros e processadores de contexto para o Jinja2."""
    
    # Habilita a extensão 'do' no Jinja2
    app.jinja_env.add_extension('jinja2.ext.do')

    # Adiciona a macro de paginação ao contexto global do Jinja
    # Isso evita a necessidade de importar a macro em cada template que a utiliza.
    @app.context_processor
    def utility_processor():
        """Disponibiliza a macro de paginação globalmente para todos os templates."""
        pagination_macro = app.jinja_env.get_template("partials/_pagination.html").module
        return dict(render_pagination=pagination_macro.render_pagination)

    @app.template_filter('merge')
    def _merge_query_args(dict1, dict2):
        """Filtro para mesclar dicionários, essencial para os links de paginação/ordenação."""
        result = dict1.copy()
        result.update(dict2)
        return result

    @app.template_filter('highlight')
    def highlight_filter(text, query):
        """Filtro para destacar termos de busca no texto."""
        if not query or not text:
            return text
        keywords = [re.escape(kw) for kw in query.strip().split() if kw]
        if not keywords:
            return text
        # Adiciona limites de palavra (\b) ao redor da expressão regular.
        # Isso garante que apenas palavras inteiras sejam destacadas, evitando
        # que uma busca por "1005" destaque parte de "SK91005B".
        highlighted_text = re.sub(r'\b(' + '|'.join(keywords) + r')\b', r'<mark>\1</mark>', str(text), flags=re.IGNORECASE)
        return Markup(highlighted_text)

    @app.context_processor
    def inject_global_vars():
        """Injeta variáveis globais em todos os templates."""
        config = carregar_config_aparencia()
        update_info = app.config.get('UPDATE_INFO', None)
        
        # Se não há info na memória, tenta carregar do arquivo
        if not update_info:
            update_info_file = os.path.join(APP_DATA_PATH, 'update_info.json')
            if os.path.exists(update_info_file):
                try:
                    with open(update_info_file, 'r') as f:
                        update_info = json.load(f)
                        app.config['UPDATE_INFO'] = update_info
                except (json.JSONDecodeError, IOError):
                    pass
        
        is_admin = current_user.is_authenticated and current_user.is_admin
        # Passa os argumentos da requisição para todos os templates.
        # Isso simplifica a criação de links que mantêm o estado da busca.
        search_args = request.args.copy()
        search_args.pop('page', None)
        return dict(
            config_aparencia=config, 
            is_admin=is_admin, 
            app_version=VERSION, 
            update_info=update_info,
            search_args=search_args
        )

def check_for_updates(app):
    """Verifica se há uma nova versão da aplicação disponível."""
    with app.app_context():
        print("Verificando atualizações...")
        try:
            response = requests.get(UPDATE_CONFIG_URL, timeout=15)
            response.raise_for_status()
            update_data = response.json()
            latest_version = update_data.get("latest_version", update_data.get("version"))

            # Usa a biblioteca packaging para comparação de versão mais robusta
            if latest_version and pkg_version.parse(latest_version) > pkg_version.parse(VERSION):
                print(f"Nova versão encontrada: {latest_version}")
                app.config['UPDATE_INFO'] = {
                    'latest_version': latest_version,
                    'download_url': update_data.get('download_url'),
                    'release_notes': update_data.get('release_notes', 'Sem notas de lançamento.'),
                    'update_found_at': datetime.now().isoformat(),
                    'update_size': update_data.get('size_mb', 'Desconhecido')
                }
                # Salva informação de atualização em arquivo para persistir entre reinicializações
                update_info_file = os.path.join(APP_DATA_PATH, 'update_info.json')
                with open(update_info_file, 'w') as f:
                    json.dump(app.config['UPDATE_INFO'], f, indent=2)
            else:
                print("Nenhuma nova atualização encontrada.")
                # Remove arquivo de informação de atualização se não há atualizações
                update_info_file = os.path.join(APP_DATA_PATH, 'update_info.json')
                if os.path.exists(update_info_file):
                    os.remove(update_info_file)
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            print(f"Erro ao verificar atualizações: {e}")

def schedule_periodic_update_check(app):
    """Agenda verificações periódicas de atualização a cada 6 horas."""
    check_for_updates(app)
    # Agenda a próxima verificação em 6 horas (21600 segundos)
    threading.Timer(21600.0, lambda: schedule_periodic_update_check(app)).start()

# Para criar o banco de dados e inserir dados de exemplo
def inicializar_banco(app, reset=False):
    """Garante que o banco de dados, tabelas, usuário admin e índice FTS existam."""
    with app.app_context():
        # Habilita o modo WAL (Write-Ahead Logging) para maior robustez contra corrupção.
        # Isso deve ser feito antes de outras operações no banco.
        with db.engine.connect() as connection:
            connection.execute(db.text('PRAGMA journal_mode=WAL;'))
        
        if reset:
            db.drop_all()

        from models import User # Importa aqui para evitar importação circular

        db.create_all()
 
        # Cria um usuário 'admin' se não existir, com uma senha aleatória segura.
        if User.query.filter_by(username='admin').first() is None:
            import secrets
            import string
            alphabet = string.ascii_letters + string.digits
            random_password = ''.join(secrets.choice(alphabet) for i in range(12))
            
            admin_user = User(username='admin', is_admin=True)
            admin_user.set_password(random_password)
            db.session.add(admin_user)
            db.session.commit()
            print("="*50)
            print("ATENÇÃO: Usuário 'admin' criado pela primeira vez.")
            print(f"A senha temporária é: {random_password}")
            print("Anote esta senha e altere-a assim que possível.")
            print("="*50)