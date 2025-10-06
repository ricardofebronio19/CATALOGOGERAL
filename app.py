import os
import csv
import json
from sqlalchemy import func, or_
import unicodedata
import threading
import requests
import sys # Adicionado para verificar o modo de execução
import shutil
import collections
import zipfile
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, Response, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

import re # Importado para a lógica de importação de CSV
# --- ROTA TEMPORÁRIA PARA PROMOVER ADMIN ---

# --- Configurações de Atualização ---
VERSION = "1.0.0"  # Versão atual da aplicação
UPDATE_CONFIG_URL = "https://raw.githubusercontent.com/SEU_USUARIO/catalogo-pecas-releases/main/update_config.json" # URL para o JSON de configuração da atualização

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
# Garante que a pasta de dados exista
os.makedirs(APP_DATA_PATH, exist_ok=True)
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
# --- Funções de Configuração de Aparência ---
def carregar_config_aparencia():
    """Carrega as configurações de aparência do arquivo JSON."""
    try:
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Retorna um dicionário padrão se o arquivo não existir ou for inválido
        return {'cor_principal': '#ff6600', 'logo_path': None}

def salvar_config_aparencia(config):
    """Salva as configurações de aparência no arquivo JSON."""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)


if getattr(sys, 'frozen', False):
    # Se estiver rodando como um executável PyInstaller
    # PyInstaller coloca os dados em um diretório temporário (_MEIPASS).
    # Precisamos dizer ao Flask para procurar os templates e arquivos estáticos lá.
    template_folder = os.path.join(sys._MEIPASS, 'templates')
    static_folder = os.path.join(sys._MEIPASS, 'static')
    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)
else:
    # Se estiver rodando como um script Python normal
    app = Flask(__name__)

# Habilita a extensão 'do' no Jinja2, permitindo modificar variáveis dentro de templates.
# Isso é necessário para a lógica de ordenação na página de resultados.
app.jinja_env.add_extension('jinja2.ext.do')

@app.template_filter('merge')
def _merge_query_args(dict1, dict2):
    """Filtro Jinja2 para mesclar dicionários, útil para construir URLs de paginação/ordenação."""
    result = dict1.copy()
    result.update(dict2)
    return result
# Gera uma chave secreta se não existir, para maior segurança.
if not os.path.exists(CONFIG_FILE) or 'secret_key' not in carregar_config_aparencia():
    config = carregar_config_aparencia()
    config['secret_key'] = os.urandom(24).hex()
    salvar_config_aparencia(config)
app.config['SECRET_KEY'] = carregar_config_aparencia()['secret_key']
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(APP_DATA_PATH, "catalogo.db")
 # Adiciona opções de engine para melhorar a robustez do SQLite
# O 'timeout' aqui é para o SQLite esperar mais tempo antes de falhar com 'database is locked'.
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'connect_args': {
        'timeout': 15
    }, 
    'pool_pre_ping': True
}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
db = SQLAlchemy(app)

@app.template_filter('highlight')
def highlight_filter(text, query):
    """
    Filtro Jinja2 para destacar termos de uma busca em um texto.
    Usa a tag <mark> para o destaque.
    """
    if not query or not text:
        return text

    # Divide a query em palavras, escapa para uso em regex e cria um padrão case-insensitive
    keywords = [re.escape(kw) for kw in query.strip().split() if kw]
    if not keywords:
        return text
    
    return re.sub(f"({'|'.join(keywords)})", r'<mark>\1</mark>', str(text), flags=re.IGNORECASE)

@app.context_processor
def inject_config():
    """Injeta as configurações de aparência em todos os templates."""
    config = carregar_config_aparencia()
    update_info = app.config.get('UPDATE_INFO', None)
    is_admin = current_user.is_authenticated and current_user.is_admin
    return dict(config_aparencia=config, is_admin=is_admin, app_version=VERSION, update_info=update_info)

# Configuração do Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' # Redireciona usuários não logados para a rota /login

# Função para verificar se a extensão do arquivo é permitida
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- Tabela de Associação para Similares (Many-to-Many) ---
similares_association = db.Table('similares_association',
    db.Column('produto_id', db.Integer, db.ForeignKey('produto.id'), primary_key=True),
    db.Column('similar_id', db.Integer, db.ForeignKey('produto.id'), primary_key=True)
)

# --- Modelos de Dados ---
class Produto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    codigo = db.Column(db.String(50), unique=True, nullable=False, index=True)
    grupo = db.Column(db.String(50), nullable=True, index=True)
    fornecedor = db.Column(db.String(100), nullable=True, index=True)
    conversoes = db.Column(db.Text, nullable=True) # Campo para conversões/códigos similares

    similares = db.relationship('Produto', secondary=similares_association,
                                primaryjoin=(similares_association.c.produto_id == id),
                                secondaryjoin=(similares_association.c.similar_id == id),
                                backref=db.backref('similar_to'))

    medidas = db.Column(db.String(255), nullable=True)
    observacoes = db.Column(db.Text, nullable=True) # Novo campo para observações

    # Relacionamento com as aplicações
    aplicacoes = db.relationship('Aplicacao', backref='produto', lazy=True, cascade="all, delete-orphan")
    
    # Relacionamento com as imagens
    imagens = db.relationship('ImagemProduto', backref='produto', lazy=True, cascade="all, delete-orphan", order_by='ImagemProduto.ordem')

    def __repr__(self):
        return f'<Produto {self.nome}>'

class Aplicacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    veiculo = db.Column(db.String(100), nullable=True)
    ano = db.Column(db.String(10), nullable=True)
    motor = db.Column(db.String(100), nullable=True)
    conf_mtr = db.Column(db.String(100), nullable=True) # Conf. MTR da imagem
    montadora = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f'<Aplicacao {self.montadora} {self.veiculo} - {self.motor}>'

class ImagemProduto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    filename = db.Column(db.String(100), nullable=False)
    ordem = db.Column(db.Integer, default=0) # Novo campo para ordenação

    def __repr__(self):
        return f'<ImagemProduto {self.filename}>'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

# --- Funções Auxiliares ---
def _normalize_for_search(text: str) -> str:
    """Remove acentos, pontuações comuns e converte para minúsculas para busca."""
    if not text:
        return ""
    # Normaliza para decompor acentos (e.g., 'á' -> 'a' + '´')
    nfkd_form = unicodedata.normalize('NFD', text.lower())
    # Remove os acentos
    text = "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    # Remove pontuações e caracteres especiais
    return text.replace('.', '').replace('-', '').replace(',', '').replace(' ', '')

def _apply_db_normalization(column):
    """Aplica funções SQL para normalizar uma coluna para busca (case, acentos, pontuação)."""
    # Esta é uma aproximação para remover acentos no SQLite, substituindo caracteres comuns.
    # Uma solução completa exigiria uma função customizada no SQLite.
    normalized_column = func.lower(column)
    # Substitui caracteres acentuados comuns
    accent_map = {'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 'â': 'a', 'ê': 'e', 'ô': 'o', 'à': 'a', 'ü': 'u', 'ç': 'c'}
    for accented, unaccented in accent_map.items():
        normalized_column = func.replace(normalized_column, accented, unaccented)
    
    # Remove pontuações
    return func.replace(func.replace(func.replace(func.replace(normalized_column, '.', ''), '-', ''), ',', ''), ' ', '')

def _build_search_query(termo, codigo_produto, montadora, aplicacao_termo, grupo, medidas):
    """Constrói a query de busca de produtos com base nos filtros fornecidos."""
    query = Produto.query

    # Lógica de busca geral aprimorada
    if termo:
        # Junta as tabelas Produto e Aplicacao para permitir a busca em ambas
        query = query.join(Aplicacao, Produto.id == Aplicacao.produto_id, isouter=True).distinct()

        # Divide o termo de busca em palavras individuais
        for palavra in termo.strip().split():
            palavra_normalizada = _normalize_for_search(palavra)
            if not palavra_normalizada: continue

            # Para cada palavra, adiciona um filtro que exige que ela esteja presente em pelo menos um dos campos.
            # Isso garante que um produto só apareça se TODAS as palavras da busca forem encontradas.
            query = query.filter(db.or_(
                _apply_db_normalization(Produto.nome).contains(palavra_normalizada),
                _apply_db_normalization(Produto.codigo).contains(palavra_normalizada),
                _apply_db_normalization(Produto.fornecedor).contains(palavra_normalizada),
                _apply_db_normalization(Aplicacao.veiculo).contains(palavra_normalizada),
                _apply_db_normalization(Aplicacao.motor).contains(palavra_normalizada),
                _apply_db_normalization(Produto.conversoes).contains(palavra_normalizada)
            ))

    if codigo_produto:
        codigo_normalizado = _normalize_for_search(codigo_produto)
        query = query.filter(_apply_db_normalization(Produto.codigo).contains(codigo_normalizado))

    if grupo:
        query = query.filter(Produto.grupo.ilike(f"%{grupo}%"))

    if medidas:
        # Normaliza tanto o termo de busca quanto a coluna do banco para uma comparação robusta
        medidas_normalizadas = _normalize_for_search(medidas)
        query = query.filter(_apply_db_normalization(Produto.medidas).contains(medidas_normalizadas))

    # A busca por fabricante e aplicação agora precisa garantir que a junção com Aplicação exista,
    # caso a busca geral (termo) não tenha sido usada.
    needs_join = not termo and (montadora or aplicacao_termo)
    if needs_join:
        query = query.join(Aplicacao, Produto.id == Aplicacao.produto_id)

    if montadora:
        query = query.filter(Aplicacao.montadora.ilike(f"%{montadora}%"))

    if aplicacao_termo:
        aplicacao_like = f'%{aplicacao_termo}%'
        query = query.filter(db.or_(Aplicacao.veiculo.ilike(aplicacao_like), Aplicacao.motor.ilike(aplicacao_like)))
    return query

def _download_image_from_url(url: str, upload_folder: str, product_code: str = None) -> str | None:
    """
    Baixa uma imagem de uma URL, a salva na pasta de uploads com um nome seguro
    e retorna o nome do arquivo salvo. Retorna None em caso de falha.
    """
    if not url or not url.startswith(('http://', 'https://')):
        return None
    try:
        response = requests.get(url, stream=True, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        response.raise_for_status() # Lança um erro para status HTTP ruins (4xx ou 5xx)

        # Tenta obter a extensão do arquivo a partir da URL
        original_filename = url.split('/')[-1].split('?')[0]
        _, ext = os.path.splitext(original_filename)
        if ext.lower() not in ['.jpg', '.jpeg', '.png', '.gif', '.webp']:
            # Se a extensão não for de imagem, tenta adivinhar pelo content-type
            content_type = response.headers.get('content-type')
            if content_type and 'image' in content_type:
                ext = '.' + content_type.split('/')[1]
            else:
                ext = '.jpg' # Padrão

        # Gera um nome de arquivo seguro e único
        base_name = product_code if product_code else "img"
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
        filename = secure_filename(f"{base_name}_{timestamp}{ext}")
        
        filepath = os.path.join(upload_folder, filename)
        with open(filepath, 'wb') as f:
            shutil.copyfileobj(response.raw, f)
        return filename
    except requests.exceptions.RequestException as e:
        print(f"Erro ao baixar a imagem da URL {url}: {e}")
        return None

def _atualizar_similares_simetricamente(produto_principal, novos_similares):
    """
    Atualiza a relação de similares de forma simétrica.
    Garante que se A é similar a B, B também seja similar a A.
    """
    # Similares atuais antes da modificação
    similares_antigos = set(produto_principal.similares)
    novos_similares_set = set(novos_similares)

    # Define a nova lista de similares para o produto principal
    produto_principal.similares = novos_similares

    # Remove a referência do produto principal dos similares que foram desassociados
    for similar_removido in (similares_antigos - novos_similares_set):
        if produto_principal in similar_removido.similares:
            similar_removido.similares.remove(produto_principal)

    # Adiciona a referência do produto principal nos novos similares
    for novo_similar in novos_similares:
        if produto_principal not in novo_similar.similares:
            novo_similar.similares.append(produto_principal)

def _parse_year_range(year_str: str | None) -> tuple[int, int]:
    """
    Converte uma string de ano (ex: "2010", "2010/2015", "2018/...") 
    em uma tupla com ano inicial e final.
    """
    if not year_str or not year_str.strip():
        return -1, -1 # Retorna um intervalo inválido se a string for vazia

    year_str = year_str.strip()
    
    try:
        # Formato: 2018/... ou 2018/
        if year_str.endswith('/...') or year_str.endswith('/'):
            start_year = int(year_str.split('/')[0])
            return start_year, 9999 # Fim "infinito"
        # Formato: .../2015 ou /2015
        if year_str.startswith('.../') or year_str.startswith('/'):
            end_year = int(year_str.split('/')[1])
            return 0, end_year # Início "infinito"
        # Formato: 2010/2015
        if '/' in year_str:
            parts = year_str.split('/')
            start = int(parts[0])
            end = int(parts[1])
            return min(start, end), max(start, end)
        # Formato: 2010
        single_year = int(year_str)
        return single_year, single_year
    except (ValueError, IndexError):
        return -1, -1 # Retorna intervalo inválido em caso de erro de parse

def _ranges_overlap(range1: tuple[int, int], range2: tuple[int, int]) -> bool:
    """Verifica se dois intervalos de anos (tuplas) se sobrepõem."""
    return range1[0] <= range2[1] and range2[0] <= range1[1]
# --- Rotas da Aplicação ---
@app.route('/')
def index():
    """Página inicial que exibe a busca e a lista de montadoras com seus veículos."""
    # Busca pares distintos de (montadora, veiculo) do banco de dados
    aplicacoes = db.session.query(Aplicacao.montadora, Aplicacao.veiculo).distinct().filter(
        Aplicacao.montadora.isnot(None), 
        Aplicacao.montadora != ''
    ).order_by(Aplicacao.montadora, Aplicacao.veiculo).all()

    # Agrupa os veículos por montadora
    montadoras_com_veiculos_raw = collections.defaultdict(list)
    for montadora, veiculo in aplicacoes:
        # Normaliza para Title Case e remove espaços extras para consistência (ex: 'FORD ' -> 'Ford')
        montadoras_com_veiculos_raw[montadora.strip().title()].append(veiculo)

    # Converte para um dicionário normal para o próximo passo
    montadoras_com_veiculos = dict(montadoras_com_veiculos_raw)
    # Garante que todas as montadoras pré-definidas apareçam na lista, mesmo sem veículos
    for montadora_predefinida in MONTADORAS_PREDEFINIDAS:
        if montadora_predefinida.title() not in montadoras_com_veiculos:
            montadoras_com_veiculos[montadora_predefinida] = []

    return render_template('index.html', montadoras_com_veiculos=dict(sorted(montadoras_com_veiculos.items())))
@app.route('/buscar', methods=['GET'])
def buscar():
    page = request.args.get('page', 1, type=int)
    termo = request.args.get('termo', '')
    codigo_produto = request.args.get('codigo_produto', '')
    montadora = request.args.get('montadora', '')
    aplicacao_termo = request.args.get('aplicacao', '') # Renomeado para evitar conflito
    grupo = request.args.get('grupo', '')
    medidas = request.args.get('medidas', '')
    sort_by = request.args.get('sort_by', 'codigo') # Novo: Padrão para 'codigo'

    # Define o número de itens por página
    PER_PAGE = 20

    # Usa a função auxiliar para construir a query
    query = _build_search_query(termo, codigo_produto, montadora, aplicacao_termo, grupo, medidas)

    # Adiciona a ordenação com base no parâmetro 'sort_by'
    if sort_by == 'nome':
        query = query.order_by(Produto.nome)
    else: # Padrão é ordenar por código
        query = query.order_by(Produto.codigo)
    pagination = query.paginate(page=page, per_page=PER_PAGE, error_out=False)

    # Cria uma cópia dos argumentos da requisição para passar para o template,
    # removendo a chave 'page' para evitar conflito no url_for da paginação.
    search_args = request.args.copy()
    search_args.pop('page', None)

    return render_template('resultados.html', pagination=pagination, termo=termo, sort_by=sort_by, search_args=search_args)

@app.route('/exportar/csv')
@login_required
def exportar_csv():
    # Reutiliza os mesmos parâmetros da busca
    termo = request.args.get('termo', '')
    codigo_produto = request.args.get('codigo_produto', '')
    montadora = request.args.get('montadora', '')
    aplicacao_termo = request.args.get('aplicacao', '')
    grupo = request.args.get('grupo', '')
    medidas = request.args.get('medidas', '')

    # Usa a função auxiliar para construir a query
    query = _build_search_query(termo, codigo_produto, montadora, aplicacao_termo, grupo, medidas)
    resultados = query.options(db.joinedload(Produto.aplicacoes)).all()

    def generate():
        # Cabeçalho do CSV
        yield 'Código,Nome,Fornecedor,Montadoras (Aplicações),Grupo,Aplicações\n'
        for produto in resultados:
            # Coleta todos os fabricantes únicos das aplicações do produto
            montadoras_aplicacoes = sorted(list(set(a.montadora for a in produto.aplicacoes if a.montadora)))
            montadoras_str = " | ".join(montadoras_aplicacoes)

            # Junta todas as aplicações em uma única string, separadas por "|"
            aplicacoes_str = " | ".join([f"{a.veiculo or ''} {a.ano or ''} {a.motor or ''}" for a in produto.aplicacoes])
            # Cria a linha do CSV, tratando valores nulos e escapando aspas
            yield f'"{produto.codigo}","{produto.nome}","{produto.fornecedor or ""}","{montadoras_str}","{produto.grupo or ""}","{aplicacoes_str}"\n'

    return Response(generate(), mimetype='text/csv', headers={"Content-disposition": "attachment; filename=export_pecas.csv"})

@app.route('/adicionar_peca', methods=['GET', 'POST'])
@login_required
def adicionar_peca():
    if request.method == 'POST':
        # Validação manual básica
        nome = request.form.get('nome', '').strip().upper()
        codigo = request.form.get('codigo', '').strip().upper()
        if not nome or not codigo:
            flash('Nome da Peça e Código são campos obrigatórios.', 'danger')
            # Retorna para o formulário, mas precisa passar os dados de volta
            return redirect(url_for('adicionar_peca'))

        # Verifica se o código já existe
        if Produto.query.filter(func.upper(Produto.codigo) == codigo).first():
            flash(f'O código "{codigo}" já está em uso. Por favor, escolha outro.', 'danger')
            return redirect(url_for('adicionar_peca'))

        try:
            novo_produto = Produto(
                nome=nome,
                codigo=codigo,
                grupo=request.form.get('grupo', '').strip().upper(),
                fornecedor=request.form.get('fornecedor', '').strip().upper(),
                conversoes=request.form.get('conversoes', '').strip().upper(),
                medidas=request.form.get('medidas', '').strip().upper(),
                observacoes=request.form.get('observacoes', '').strip().upper()
            )

            db.session.add(novo_produto)
            db.session.flush() # Garante que o novo_produto tenha um ID

            # Lógica de upload de múltiplas imagens
            proxima_ordem = 0
            files = request.files.getlist('imagens')
            for file in files:
                if file and file.filename != '' and allowed_file(file.filename):
                    _, ext = os.path.splitext(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
                    imagem_filename = secure_filename(f"{novo_produto.codigo}_{timestamp}{ext}")
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], imagem_filename))
                    nova_imagem = ImagemProduto(filename=imagem_filename, ordem=proxima_ordem)
                    novo_produto.imagens.append(nova_imagem)
                    proxima_ordem += 1

            # Lógica para baixar imagem da URL
            imagem_url = request.form.get('imagem_url')
            if imagem_url:
                downloaded_filename = _download_image_from_url(imagem_url, app.config['UPLOAD_FOLDER'], product_code=novo_produto.codigo)
                if downloaded_filename:
                    nova_imagem = ImagemProduto(filename=downloaded_filename, ordem=proxima_ordem)
                    novo_produto.imagens.append(nova_imagem)

            # Lógica para associar produtos similares de forma simétrica
            similares_ids_str = request.form.get('similares_ids', '')
            similares_ids = [int(id) for id in similares_ids_str.split(',') if id.isdigit()]
            produtos_similares = Produto.query.filter(Produto.id.in_(similares_ids)).all() if similares_ids else []
            _atualizar_similares_simetricamente(novo_produto, produtos_similares)
            
            # Processa múltiplas aplicações
            aplicacoes_form = {}
            for key, value in request.form.items():
                if key.startswith('aplicacoes-'):
                    parts = key.split('-') # aplicacoes-0-veiculo
                    index = parts[1]
                    field = parts[2]
                    aplicacoes_form.setdefault(index, {})[field] = value.strip().upper()

            for data in aplicacoes_form.values():
                if data.get('veiculo'):
                    db.session.add(Aplicacao(produto=novo_produto, **data))

            db.session.commit()
            flash('Produto adicionado com sucesso!', 'success')
            return redirect(url_for('detalhe_peca', id=novo_produto.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Ocorreu um erro inesperado ao adicionar o produto: {e}', 'danger')

    # Busca todos os grupos distintos para o autocompletar no formulário
    grupos = db.session.query(Produto.grupo).distinct().filter(Produto.grupo.isnot(None)).order_by(Produto.grupo).all()
    lista_grupos = sorted([g[0] for g in grupos])

    # Busca todos os fornecedores distintos para o autocompletar
    fornecedores = db.session.query(Produto.fornecedor).distinct().filter(Produto.fornecedor.isnot(None)).order_by(Produto.fornecedor).all()
    lista_fornecedores = sorted([f[0] for f in fornecedores])

    # Busca todos os fabricantes distintos e combina com a lista pré-definida
    montadoras_db = db.session.query(Aplicacao.montadora).distinct().filter(Aplicacao.montadora.isnot(None)).all()
    lista_montadoras_db = [m[0] for m in montadoras_db]
    # Usa um set para unir as listas e remover duplicatas, depois ordena
    lista_montadoras_completa = sorted(list(set(lista_montadoras_db + MONTADORAS_PREDEFINIDAS)))

    return render_template('adicionar_peca.html',
                           grupos=lista_grupos, 
                           montadoras=lista_montadoras_completa,
                           fornecedores=lista_fornecedores)

@app.route('/peca/<int:id>')
def detalhe_peca(id):
    """Exibe a página de detalhes de um produto específico."""
    from sqlalchemy.orm import selectinload

    produto = db.session.query(Produto).options(
        selectinload(Produto.aplicacoes),
        selectinload(Produto.imagens),
        selectinload(Produto.similares).selectinload(Produto.aplicacoes), # Carrega aplicações dos similares
        selectinload(Produto.similar_to)
    ).get(id)
    if not produto:
        return "Produto não encontrado", 404

    # Agrupa as aplicações por fabricante para exibição organizada
    aplicacoes_agrupadas = collections.defaultdict(list)
    # Ordena as aplicações para garantir uma ordem consistente (por montadora, depois por veículo)
    sorted_aplicacoes = sorted(produto.aplicacoes, key=lambda app: (app.montadora or 'ZZZ', app.veiculo or ''))
    for aplicacao in sorted_aplicacoes:
        montadora_chave = aplicacao.montadora or 'Sem Montadora'
        aplicacoes_agrupadas[montadora_chave].append(aplicacao)

    # --- Lógica para encontrar produtos sugeridos por conversão ---
    sugestoes_similares_dict = {}
    # A nova lógica requer que o produto tenha um grupo e aplicações para funcionar.
    if produto.grupo and produto.aplicacoes:
        ids_similares_manuais = {p.id for p in produto.similares}
        ids_similares_manuais.add(produto.id) # Adiciona o próprio produto para não ser sugerido

        # Para cada aplicação do produto principal, busca por similares
        for app_principal in produto.aplicacoes:
            if not app_principal.veiculo: continue

            range_principal = _parse_year_range(app_principal.ano)
            if range_principal == (-1, -1): continue # Pula se o ano for inválido

            # Busca produtos do mesmo grupo, com o mesmo veículo
            candidatos = Produto.query.filter(
                Produto.id.notin_(ids_similares_manuais),
                Produto.grupo == produto.grupo,
                Produto.aplicacoes.any(Aplicacao.veiculo == app_principal.veiculo)
            ).options(selectinload(Produto.aplicacoes)).all()

            # Filtra os candidatos em Python pela sobreposição de ano
            for candidato in candidatos:
                if candidato.id in sugestoes_similares_dict: continue # Já adicionado

                for app_candidata in candidato.aplicacoes:
                    if app_candidata.veiculo == app_principal.veiculo:
                        range_candidato = _parse_year_range(app_candidata.ano)
                        if range_candidato != (-1, -1) and _ranges_overlap(range_principal, range_candidato):
                            sugestoes_similares_dict[candidato.id] = candidato
                            break # Encontrou uma aplicação correspondente, pode ir para o próximo candidato

    # Converte o dicionário de volta para uma lista para o template
    sugestoes_similares = list(sugestoes_similares_dict.values())

    # Captura a URL da página anterior para criar um link "Voltar" funcional.
    # Isso preserva os filtros da busca.
    voltar_url = request.referrer
    if not voltar_url or any(x in voltar_url for x in ['/login', '/adicionar_peca', f'/peca/{id}/editar']):
        voltar_url = url_for('index')

    return render_template('detalhe_peca.html', produto=produto, aplicacoes_agrupadas=aplicacoes_agrupadas, sugestoes_similares=sugestoes_similares, voltar_url=voltar_url)

@app.route('/peca/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_peca(id):
    # Usar db.session.get() é a forma padrão e mais eficiente de buscar por chave primária.
    # Para carregar relações junto, usamos `selectinload` que é mais adequado para coleções.
    from sqlalchemy.orm import selectinload
    produto = db.session.query(Produto).options(selectinload(Produto.aplicacoes), selectinload(Produto.imagens), selectinload(Produto.similares)).get(id)

    if not produto:
        flash('Produto não encontrado.', 'danger')
        return "Produto não encontrado", 404

    # Captura a URL da página anterior para o botão "Voltar".
    # Se não houver um referenciador válido, volta para a página de detalhes da peça.
    voltar_url = request.referrer
    if not voltar_url or any(x in voltar_url for x in ['/login', '/adicionar_peca']):
        voltar_url = url_for('detalhe_peca', id=id)

    if request.method == 'POST':
        # Validação manual básica
        nome = request.form.get('nome', '').strip().upper()
        codigo = request.form.get('codigo', '').strip().upper()
        if not nome or not codigo:
            flash('Nome da Peça e Código são campos obrigatórios.', 'danger')
            return redirect(url_for('editar_peca', id=id))

        # Verifica se o novo código já está em uso por OUTRO produto
        produto_existente = Produto.query.filter(func.upper(Produto.codigo) == codigo, Produto.id != id).first()
        if produto_existente:
            flash(f'O código "{codigo}" já está em uso pelo produto "{produto_existente.nome}".', 'danger')
            return redirect(url_for('editar_peca', id=id))

        try:
            # Atualiza os campos do produto
            produto.nome = nome
            produto.codigo = codigo
            produto.grupo = request.form.get('grupo', '').strip().upper()
            produto.fornecedor = request.form.get('fornecedor', '').strip().upper()
            produto.conversoes = request.form.get('conversoes', '').strip().upper()
            produto.medidas = request.form.get('medidas', '').strip().upper()
            produto.observacoes = request.form.get('observacoes', '').strip().upper()

            # Lógica para associar produtos similares de forma simétrica
            similares_ids_str = request.form.get('similares_ids', '')
            similares_ids = [int(id) for id in similares_ids_str.split(',') if id.isdigit()]
            produtos_similares = Produto.query.filter(Produto.id.in_(similares_ids)).all() if similares_ids else []
            _atualizar_similares_simetricamente(produto, produtos_similares)

            # Lógica para atualizar/adicionar/remover aplicações
            aplicacoes_form = {}
            for key, value in request.form.items():
                if key.startswith('aplicacoes-'):
                    parts = key.split('-') # aplicacoes-0-veiculo
                    index = parts[1]
                    field = parts[2]
                    aplicacoes_form.setdefault(index, {})[field] = value.strip().upper()

            aplicacoes_existentes_map = {str(app.id): app for app in produto.aplicacoes if app.id}
            ids_aplicacoes_no_form = {data.get('id') for data in aplicacoes_form.values() if data.get('id')}

            for data in aplicacoes_form.values():
                if not data.get('veiculo'): continue

                app_id = data.get('id')
                if app_id and app_id in aplicacoes_existentes_map: # Atualiza
                    aplicacao = aplicacoes_existentes_map[app_id]
                    aplicacao.veiculo = data.get('veiculo', '')
                    aplicacao.ano = data.get('ano', '')
                    aplicacao.motor = data.get('motor', '')
                    aplicacao.conf_mtr = data.get('conf_mtr', '')
                    aplicacao.montadora = data.get('montadora', '')
                elif data.get('veiculo'): # Adiciona nova
                    db.session.add(Aplicacao(produto=produto, **{k:v for k,v in data.items() if k != 'id'}))
            
            ids_para_remover = set(aplicacoes_existentes_map.keys()) - ids_aplicacoes_no_form
            for app_id in ids_para_remover:
                db.session.delete(aplicacoes_existentes_map[app_id])

            # Lógica de upload de nova imagem
            proxima_ordem = max([img.ordem for img in produto.imagens] + [-1]) + 1
            files = request.files.getlist('imagens')
            for file in files:
                if file and file.filename != '' and allowed_file(file.filename):
                    _, ext = os.path.splitext(file.filename)
                    timestamp = datetime.now().strftime('%Y%m%d%H%M%S%f')
                    imagem_filename = secure_filename(f"{produto.codigo}_{timestamp}{ext}")
                    file.save(os.path.join(app.config['UPLOAD_FOLDER'], imagem_filename))
                    nova_imagem = ImagemProduto(filename=imagem_filename, ordem=proxima_ordem)
                    produto.imagens.append(nova_imagem)
                    proxima_ordem += 1

            # Lógica para baixar imagem da URL
            imagem_url = request.form.get('imagem_url')
            if imagem_url:
                downloaded_filename = _download_image_from_url(imagem_url, app.config['UPLOAD_FOLDER'], product_code=produto.codigo)
                if downloaded_filename:
                    nova_imagem = ImagemProduto(filename=downloaded_filename, ordem=proxima_ordem)
                    produto.imagens.append(nova_imagem)

            # Lógica para reordenar imagens
            ordem_imagens_str = request.form.get('ordem_imagens')
            if ordem_imagens_str:
                ordem_ids = ordem_imagens_str.split(',')
                
                # Reordena apenas as imagens que JÁ EXISTEM no banco (têm ID)
                imagens_existentes_map = {str(img.id): img for img in produto.imagens if img.id is not None}
                for i, img_id in enumerate(ordem_ids):
                    if img_id in imagens_existentes_map:
                        imagens_existentes_map[img_id].ordem = i
                
                # Atribui uma ordem para as NOVAS imagens (que não têm ID ainda)
                novas_imagens = [img for img in produto.imagens if img.id is None]
                for i, nova_img in enumerate(novas_imagens, start=len(ordem_ids)):
                    nova_img.ordem = i

            db.session.commit()
            flash('Produto atualizado com sucesso!', 'success')
            return redirect(url_for('detalhe_peca', id=produto.id))
        except Exception as e:
            db.session.rollback()
            flash(f'Ocorreu um erro inesperado ao atualizar o produto: {e}', 'danger')

    # Busca de dados para os datalists (autocompletar)
    grupos = db.session.query(Produto.grupo).distinct().filter(Produto.grupo.isnot(None)).order_by(Produto.grupo).all()
    lista_grupos = sorted([g[0] for g in grupos])

    fornecedores = db.session.query(Produto.fornecedor).distinct().filter(Produto.fornecedor.isnot(None)).order_by(Produto.fornecedor).all()
    lista_fornecedores = sorted([f[0] for f in fornecedores])

    montadoras_db = db.session.query(Aplicacao.montadora).distinct().filter(Aplicacao.montadora.isnot(None)).all()
    lista_montadoras_db = [m[0] for m in montadoras_db]
    lista_montadoras_completa = sorted(list(set(lista_montadoras_db + MONTADORAS_PREDEFINIDAS)))

    return render_template('editar_peca.html', produto=produto, 
                           grupos=lista_grupos, fornecedores=lista_fornecedores, 
                           montadoras=lista_montadoras_completa, voltar_url=voltar_url)

@app.route('/peca/<int:id>/clonar', methods=['GET'])
@login_required
def clonar_peca(id):
    # Carrega o produto original e suas relações de forma otimizada
    produto_original = db.session.query(Produto).options(
        db.joinedload(Produto.imagens),
        db.joinedload(Produto.aplicacoes),
        db.joinedload(Produto.similares)
    ).filter_by(id=id).one_or_none()

    if not produto_original:
        flash('Produto original não encontrado.', 'danger')
        return redirect(url_for('index'))

    # Gera um sufixo de clone com timestamp para maior unicidade
    clone_suffix = f"CLONE-{datetime.now().strftime('%H%M%S')}"

    # Cria um novo produto copiando os dados do original
    novo_produto = Produto(
        nome=produto_original.nome,
        codigo=f"{produto_original.codigo}-{clone_suffix}",
        grupo=produto_original.grupo,
        fornecedor=produto_original.fornecedor,
        conversoes=produto_original.conversoes,
        medidas=produto_original.medidas, # Copia as medidas
        observacoes=produto_original.observacoes # Copia as observações
    )

    # Copia as imagens, preservando a ordem
    for imagem_original in produto_original.imagens:
        novo_produto.imagens.append(ImagemProduto(
            filename=imagem_original.filename,
            ordem=imagem_original.ordem
        ))

    # Copia a relação de produtos similares
    novo_produto.similares = list(produto_original.similares)

    # Copia as aplicações
    for aplicacao_original in produto_original.aplicacoes:
        db.session.add(Aplicacao(
            produto=novo_produto, # Associa à nova peça
            veiculo=aplicacao_original.veiculo,
            ano=aplicacao_original.ano,
            motor=aplicacao_original.motor,
            conf_mtr=aplicacao_original.conf_mtr,
            montadora=aplicacao_original.montadora
        ))

    db.session.add(novo_produto)
    db.session.commit()

    flash('Produto clonado com sucesso! Por favor, revise o código e os outros dados.', 'success')
    # Redireciona para a página de edição do NOVO produto
    return redirect(url_for('editar_peca', id=novo_produto.id))

@app.route('/peca/<int:id>/excluir', methods=['POST'])
@login_required
def excluir_peca(id):
    # Carrega o produto e suas imagens associadas
    produto = db.session.query(Produto).options(db.joinedload(Produto.imagens)).filter_by(id=id).one_or_none()
    if not produto:
        flash('Produto não encontrado.', 'danger')
        return "Produto não encontrado", 404

    # Lógica otimizada para exclusão segura de imagens:
    if produto.imagens:
        # 1. Coleta todos os nomes de arquivo únicos deste produto.
        filenames_to_check = {img.filename for img in produto.imagens}

        # 2. Em uma única consulta, descobre quais desses arquivos são usados por OUTROS produtos.
        filenames_in_use_elsewhere = {
            res[0] for res in db.session.query(ImagemProduto.filename).filter(
                ImagemProduto.filename.in_(filenames_to_check),
                ImagemProduto.produto_id != produto.id
            ).distinct()
        }

        # 3. Determina quais arquivos são exclusivos deste produto e podem ser excluídos.
        files_to_delete = filenames_to_check - filenames_in_use_elsewhere

        # 4. Exclui os arquivos físicos que não estão mais em uso.
        for filename in files_to_delete:
            try:
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            except OSError as e:
                print(f"Erro ao tentar remover o arquivo de imagem {filename}: {e}")

    db.session.delete(produto)
    db.session.commit()
    
    flash('Produto excluído com sucesso.', 'success')
    return redirect(url_for('index'))

# --- ROTA PARA EXCLUIR IMAGEM DE PRODUTO --- #
@app.route('/imagem/<int:id>/excluir', methods=['POST', 'DELETE'])
@login_required
def excluir_imagem(id):
    imagem = db.session.get(ImagemProduto, id)
    if not imagem:
        if request.method == 'DELETE':
            return {"success": False, "message": "Imagem não encontrada"}, 404
        else:
            flash('Imagem não encontrada.', 'danger')
            return redirect(request.referrer or url_for('index'))

    produto_id = imagem.produto_id
    filename = imagem.filename

    # Remove a referência do banco de dados primeiro
    db.session.delete(imagem)
    db.session.commit()

    # Verifica se a imagem ainda está sendo usada por algum outro produto
    outros_usos = ImagemProduto.query.filter_by(filename=filename).count()

    # Se a imagem não for mais usada por nenhum produto, remove o arquivo físico.
    if outros_usos == 0:
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except OSError as e:
                print(f"Erro ao tentar remover o arquivo de imagem {filename}: {e}")

    if request.method == 'DELETE':
        return {"success": True, "message": "Imagem excluída com sucesso."}
    else:
        flash('Imagem excluída com sucesso.', 'success')
        return redirect(url_for('editar_peca', id=produto_id))

@app.route('/peca/<int:produto_id>/aplicacoes', methods=['GET', 'POST'])
@login_required
def gerenciar_aplicacoes(produto_id):
    produto = db.session.get(Produto, produto_id)
    if not produto:
        flash('Produto não encontrado.', 'danger')
        return redirect(url_for('index'))

    if request.method == 'POST':
        # Lógica para adicionar uma nova aplicação
        nova_aplicacao = Aplicacao(
            produto_id=produto_id,
            veiculo=request.form.get('veiculo'),
            ano=request.form.get('ano'),
            motor=request.form.get('motor'),
            conf_mtr=request.form.get('conf_mtr')
        )
        db.session.add(nova_aplicacao)
        db.session.commit()
        flash('Nova aplicação adicionada com sucesso!', 'success')
        # Redireciona para a mesma página para que o usuário possa adicionar outra
        return redirect(url_for('gerenciar_aplicacoes', produto_id=produto_id))

    return render_template('gerenciar_aplicacoes.html', produto=produto)

@app.route('/aplicacao/<int:id>/editar', methods=['GET', 'POST'])
@login_required
def editar_aplicacao(id):
    aplicacao = db.session.get(Aplicacao, id)
    if not aplicacao:
        return "Aplicação não encontrada", 404

    if request.method == 'POST':
        aplicacao.veiculo = request.form['veiculo']
        aplicacao.ano = request.form['ano']
        aplicacao.motor = request.form['motor']
        aplicacao.conf_mtr = request.form['conf_mtr']

        db.session.commit()
        # Redireciona de volta para a página de detalhes da peça a que esta aplicação pertence
        return redirect(url_for('detalhe_peca', id=aplicacao.produto_id))

    # Se for GET, exibe o formulário de edição preenchido
    return render_template('editar_aplicacao.html', aplicacao=aplicacao)

@app.route('/aplicacao/<int:id>/excluir', methods=['POST'])
@login_required
def excluir_aplicacao(id):
    aplicacao = db.session.get(Aplicacao, id)
    if not aplicacao:
        return "Aplicação não encontrada", 404
    
    produto_id = aplicacao.produto_id
    db.session.delete(aplicacao)
    db.session.commit()

    return redirect(url_for('detalhe_peca', id=produto_id))

@app.route('/aplicacao/<int:id>/excluir_ajax', methods=['DELETE'])
@login_required
def excluir_aplicacao_ajax(id):
    """Exclui uma aplicação via AJAX e retorna uma resposta JSON."""
    aplicacao = db.session.get(Aplicacao, id)
    if not aplicacao:
        return {"success": False, "message": "Aplicação não encontrada"}, 404
    
    try:
        db.session.delete(aplicacao)
        db.session.commit()
        return {"success": True, "message": "Aplicação excluída com sucesso"}
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao excluir aplicação: {e}")
        return {"success": False, "message": "Erro no servidor"}, 500

# --- Rotas de Autenticação ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user is None or not user.check_password(password):
            flash('Usuário ou senha inválidos.', 'danger')
            return redirect(url_for('login'))
        login_user(user, remember=True)
        return redirect(url_for('index'))
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

# --- Rota para validação de código em tempo real ---
@app.route('/check_codigo')
@login_required
def check_codigo():
    """Verifica se um código de produto já existe no banco de dados."""
    codigo = request.args.get('codigo', type=str)
    produto_id = request.args.get('produto_id', type=int)

    if not codigo:
        # Se o código estiver vazio, não há o que verificar
        return {"exists": False}

    query = Produto.query.filter(Produto.codigo == codigo)

    if produto_id is not None:
        # Se estivermos editando, exclui o próprio produto da verificação
        query = query.filter(Produto.id != int(produto_id))

    produto_existente = query.first()

    return {"exists": bool(produto_existente), "nome": getattr(produto_existente, 'nome', None)}

# --- Rota para busca de peças similares (autocompletar) ---
@app.route('/api/buscar_pecas_similares')
@login_required
def buscar_pecas_similares():
    """Busca peças para o campo de autocompletar de similares."""
    termo_busca = request.args.get('q', '').strip()
    produto_atual_id = request.args.get('exclude_id', type=int)

    if not termo_busca or len(termo_busca) < 2:
        return {"items": []}

    query = Produto.query.filter(
        db.or_(
            Produto.codigo.ilike(f'%{termo_busca}%'),
            Produto.nome.ilike(f'%{termo_busca}%')
        )
    )

    if produto_atual_id:
        query = query.filter(Produto.id != produto_atual_id)

    resultados = query.limit(10).all()
    
    items = [{"id": p.id, "codigo": p.codigo, "nome": p.nome} for p in resultados]
    
    return {"items": items}

# --- Rota para buscar montadora por veículo ---
@app.route('/api/get_montadora')
@login_required
def get_montadora_for_veiculo():
    """Busca a montadora mais provável para um determinado veículo."""
    veiculo = request.args.get('veiculo', '').strip().upper()
    if not veiculo:
        return {"montadora": None}

    # Busca a primeira montadora associada a este veículo.
    # Ordena por ID decrescente para pegar a mais recente, em caso de múltiplas associações.
    # Usamos ilike para ser case-insensitive.
    aplicacao = Aplicacao.query.filter(Aplicacao.veiculo.ilike(veiculo)).order_by(Aplicacao.id.desc()).first()

    if aplicacao and aplicacao.montadora:
        return {"montadora": aplicacao.montadora}
    
    return {"montadora": None}

# --- Rotas de Gerenciamento de Usuários ---
@app.route('/gerenciar_usuarios')
@login_required
def gerenciar_usuarios():
    if not current_user.is_admin:
        flash('Acesso não autorizado. Apenas administradores podem gerenciar usuários.', 'danger')
        return redirect(url_for('index'))
    usuarios = User.query.order_by(User.id).all()
    return render_template('gerenciar_usuarios.html', usuarios=usuarios)

@app.route('/adicionar_usuario', methods=['POST'])
@login_required
def adicionar_usuario():
    if not current_user.is_admin: return redirect(url_for('index'))
    username = request.form.get('username')
    password = request.form.get('password')

    if User.query.filter_by(username=username).first():
        flash(f'O nome de usuário "{username}" já existe.', 'danger')
    else:
        new_user = User(username=username)
        # Define se o novo usuário será admin
        new_user.is_admin = request.form.get('is_admin') == 'on'
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        flash(f'Usuário "{username}" criado com sucesso!', 'success')
    
    return redirect(url_for('gerenciar_usuarios'))

@app.route('/excluir_usuario/<int:user_id>', methods=['POST'])
@login_required
def excluir_usuario(user_id):
    if not current_user.is_admin: return redirect(url_for('index'))
    user_to_delete = db.session.get(User, user_id)
    if user_to_delete and user_to_delete.username != 'admin': # Proteção extra
        db.session.delete(user_to_delete)
        db.session.commit()
        flash(f'Usuário "{user_to_delete.username}" excluído com sucesso.', 'success')
    else:
        flash('Não é possível excluir este usuário.', 'danger')
    return redirect(url_for('gerenciar_usuarios'))

@app.route('/mudar_senha_usuario/<int:user_id>', methods=['POST'])
@login_required
def mudar_senha_usuario(user_id):
    if not current_user.is_admin: return redirect(url_for('index'))
    user_to_update = db.session.get(User, user_id)
    new_password = request.form.get('new_password')
    if user_to_update and new_password:
        user_to_update.set_password(new_password)
        db.session.commit()
        flash(f'Senha do usuário "{user_to_update.username}" alterada com sucesso.', 'success')
    else:
        flash('Não foi possível alterar a senha.', 'danger')
    return redirect(url_for('gerenciar_usuarios'))

# --- Rota de Configurações da Aparência ---
@app.route('/configuracoes', methods=['GET', 'POST'])
@login_required
def configuracoes():
    if not current_user.is_admin:
        return redirect(url_for('index'))
    config = carregar_config_aparencia()

    if request.method == 'POST':
        # Atualiza a cor
        config['cor_principal'] = request.form.get('cor_principal', '#ff6600')

        # Lógica de upload do logo
        if 'logo' in request.files:
            file = request.files['logo']
            if file and file.filename != '' and allowed_file(file.filename):
                # Salva o logo com um nome fixo para facilitar a referência
                logo_filename = "logo" + os.path.splitext(file.filename)[1]
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], logo_filename))
                config['logo_path'] = logo_filename
        
        salvar_config_aparencia(config)
        flash('Configurações de aparência salvas com sucesso!', 'success')
        return redirect(url_for('configuracoes'))

    return render_template('configuracoes.html', config=config)

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve os arquivos da pasta de uploads que está fora da 'static'."""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

# --- Rotas de Backup e Restauração ---
@app.route('/backup')
@login_required
def backup():
    """Cria um backup zipado e seguro da pasta de dados e o oferece para download."""
    if not current_user.is_admin:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('index'))

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    backup_filename = f"backup_catalogo_{timestamp}"
    temp_dir = os.getenv('TEMP')
    backup_zip_path = os.path.join(temp_dir, f"{backup_filename}.zip")

    # Caminho do banco de dados original
    source_db_path = os.path.join(APP_DATA_PATH, "catalogo.db")

    try:
        with zipfile.ZipFile(backup_zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            # 1. Faz uma cópia segura do banco de dados usando a API de backup do SQLite
            if os.path.exists(source_db_path):
                import sqlite3
                # Cria um banco de dados temporário em memória para o backup
                bck_conn = sqlite3.connect(':memory:')
                # Conecta ao banco de dados de origem
                src_conn = sqlite3.connect(f'file:{source_db_path}?mode=ro', uri=True)
                # Executa o backup do disco para a memória
                src_conn.backup(bck_conn)
                # Escreve o banco de dados da memória para o arquivo zip
                # dump() retorna um iterador de strings SQL
                db_dump = "\n".join(bck_conn.iterdump())
                zf.writestr('catalogo.db.sql', db_dump.encode('utf-8'))
                src_conn.close()
                bck_conn.close()

            # 2. Adiciona os outros arquivos e pastas ao zip
            for root, _, files in os.walk(APP_DATA_PATH):
                for file in files:
                    # Ignora os arquivos do banco de dados, pois já fizemos um backup seguro
                    if file.startswith('catalogo.db'):
                        continue
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, APP_DATA_PATH)
                    zf.write(file_path, arcname)

        return send_from_directory(temp_dir, f"{backup_filename}.zip", as_attachment=True)

    except Exception as e:
        flash(f"Erro ao criar o backup: {e}", "danger")
        print(f"Erro detalhado no backup: {e}")
        return redirect(url_for('configuracoes'))

@app.route('/restaurar', methods=['POST'])
@login_required
def restaurar():
    """
    Recebe um arquivo de backup, o prepara para restauração e aciona
    o reinício da aplicação.
    """
    if not current_user.is_admin:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('index'))

    if 'backup_file' not in request.files:
        flash('Nenhum arquivo de backup foi enviado.', 'danger')
        return redirect(url_for('configuracoes'))

    file = request.files['backup_file']
    if file.filename == '' or not file.filename.endswith('.zip'):
        flash('Arquivo inválido. Por favor, envie um arquivo .zip.', 'danger')
        return redirect(url_for('configuracoes'))

    # Salva o arquivo de backup com um nome fixo para ser pego pelo script de reinício
    restore_filepath = os.path.join(APP_DATA_PATH, "backup_para_restaurar.zip")
    file.save(restore_filepath)

    # Verifica se o backup contém um .sql ou um .db
    is_sql_backup = False
    with zipfile.ZipFile(restore_filepath, 'r') as zf:
        if 'catalogo.db.sql' in zf.namelist():
            is_sql_backup = True

    # Se for um backup SQL, restaura diretamente sem reiniciar
    if is_sql_backup:
        try:
            # Extrai o backup para a pasta de dados, sobrescrevendo arquivos
            with zipfile.ZipFile(restore_filepath, 'r') as zf:
                zf.extractall(APP_DATA_PATH)

            # Restaura o banco de dados a partir do arquivo .sql
            import sqlite3
            db_path = os.path.join(APP_DATA_PATH, "catalogo.db")
            sql_path = os.path.join(APP_DATA_PATH, "catalogo.db.sql")
            if os.path.exists(db_path): os.remove(db_path) # Remove o banco antigo
            
            conn = sqlite3.connect(db_path)
            with open(sql_path, 'r', encoding='utf-8') as f:
                conn.executescript(f.read())
            conn.close()
            
            os.remove(sql_path) # Limpa o arquivo sql
            os.remove(restore_filepath) # Limpa o zip
            flash("Restauração concluída com sucesso!", "success")
            return redirect(url_for('configuracoes'))
        except Exception as e:
            flash(f"Erro ao restaurar o backup: {e}", "danger")
            return redirect(url_for('configuracoes'))
    else: # Backup antigo (.db), precisa reiniciar
        # Cria um arquivo "gatilho" para sinalizar que a aplicação deve reiniciar
        restart_trigger_file = os.path.join(APP_DATA_PATH, 'RESTART_REQUIRED')
        with open(restart_trigger_file, 'w') as f:
            f.write('restart')
        return render_template('reiniciando.html')

# Para criar o banco de dados e inserir dados de exemplo
def inicializar_banco():
    """Garante que o banco de dados, tabelas, usuário admin e índice FTS existam."""
    with app.app_context():
        # Habilita o modo WAL (Write-Ahead Logging) para maior robustez contra corrupção.
        # Isso deve ser feito antes de outras operações no banco.
        with db.engine.connect() as connection:
            connection.execute(db.text('PRAGMA journal_mode=WAL;'))
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

# --- Rota e Lógica para Importação de Peças via CSV ---
def _parse_e_salvar_aplicacoes_novo_formato(produto_alvo: Produto, nome_produto: str, texto_veiculos: str, texto_ano: str, grupo: str = None, fornecedor: str = None):
    """
    Função adaptada para o novo formato do 'produto.csv'.
    Extrai aplicações de strings, lidando com múltiplos veículos e anos.
    Também atualiza o grupo e o fornecedor se forem fornecidos.
    """
    produto_alvo.nome = nome_produto
    if grupo: produto_alvo.grupo = grupo
    if fornecedor: produto_alvo.fornecedor = fornecedor

    produto_alvo.aplicacoes.clear()

    if not texto_veiculos:
        return

    # Combina o texto de 'veiculos' e 'ano' para análise
    texto_completo = f"{texto_veiculos} {texto_ano}"

    # Divide o bloco em aplicações individuais pelo separador '|'
    for aplicacao_str in texto_completo.split('|'):
        aplicacao_str = aplicacao_str.strip()
        if not aplicacao_str:
            continue

        # Encontra todos os anos na string (ex: 2012/2018, 2020/...)
        anos_encontrados = re.findall(r'(\d{4}/\s?\.{3}|\d{4}/\d{4}|\d{4}/\s?\d{4})', aplicacao_str)
        
        # Remove os anos da string para isolar os nomes dos veículos
        veiculos_str = aplicacao_str
        for ano in anos_encontrados:
            veiculos_str = veiculos_str.replace(ano, '')
        
        # Separa os veículos que podem estar juntos (ex: "CRUZE TRACKER")
        veiculos = [v.strip() for v in veiculos_str.split(' ') if v.strip()]

        for i, veiculo_completo in enumerate(veiculos):
            # Tenta pegar um ano correspondente, senão usa o primeiro ou string vazia
            ano = anos_encontrados[i] if i < len(anos_encontrados) else (anos_encontrados[0] if anos_encontrados else '')
            
            # Separa montadora e nome do veículo
            partes = veiculo_completo.split('-', 1)
            montadora = partes[0].strip().upper() if len(partes) > 1 else None
            nome_veiculo = partes[1].strip() if len(partes) > 1 else veiculo_completo.strip()

            if nome_veiculo:
                nova_aplicacao = Aplicacao(
                    veiculo=nome_veiculo,
                    ano=ano.strip(),
                    montadora=montadora,
                    produto=produto_alvo
                )
                db.session.add(nova_aplicacao)

@app.route('/importar_csv', methods=['POST'])
@login_required
def importar_csv_route():
    if not current_user.is_admin:
        flash('Acesso não autorizado.', 'danger')
        return redirect(url_for('index'))
    if 'csv_file' not in request.files:
        flash('Nenhum arquivo foi enviado.', 'danger')
        return redirect(url_for('configuracoes'))
    file = request.files['csv_file']
    if file.filename == '' or not file.filename.endswith('.csv'):
        flash('Arquivo inválido. Por favor, envie um arquivo .csv.', 'danger')
        return redirect(url_for('configuracoes'))
    produtos_adicionados = 0
    produtos_atualizados = 0
    try:
        # Usar TextIOWrapper para ler o arquivo com a codificação correta (latin-1)
        from io import TextIOWrapper
        with TextIOWrapper(file, encoding='latin-1', errors='ignore') as csvfile:
            # Detecção automática do delimitador
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(csvfile.read(2048))
            csvfile.seek(0)
            reader = csv.DictReader(csvfile, dialect=dialect)

            if not reader.fieldnames:
                flash(f"ERRO: O arquivo '{file.filename}' está vazio ou não tem um cabeçalho válido.", 'danger')
                return redirect(url_for('configuracoes'))

            # Normaliza os nomes das colunas para minúsculas e sem acentos para busca flexível
            reader.fieldnames = [_normalize_for_search(str(field)) for field in reader.fieldnames]

            for i, row in enumerate(reader, 1):
                # Busca flexível pelas colunas, independentemente de como estão escritas
                codigo = (row.get('codigo') or row.get('código') or '').strip()
                if not codigo: continue

                nome_produto = (row.get('nome') or '').strip().upper()
                # Combina 'aplicacao' e 'aplicacoescompletas' para máxima compatibilidade
                texto_veiculos = (row.get('aplicacao') or row.get('aplicacoescompletas') or '').strip().upper()
                texto_ano = (row.get('ano') or '').strip().upper()
                # Busca flexível por grupo e fornecedor
                grupo = (row.get('grupo') or '').strip().upper()
                fornecedor = (row.get('fornecedor') or row.get('fabricante') or '').strip().upper()

                produto_existente = Produto.query.filter_by(codigo=codigo).first()
                if produto_existente:
                    _parse_e_salvar_aplicacoes_novo_formato(produto_existente, nome_produto, texto_veiculos, texto_ano, grupo, fornecedor)
                    produtos_atualizados += 1
                else:
                    novo_produto = Produto(codigo=codigo)
                    db.session.add(novo_produto)
                    # Passa os novos campos para a função de parse
                    _parse_e_salvar_aplicacoes_novo_formato(novo_produto, nome_produto, texto_veiculos, texto_ano, grupo, fornecedor)
                    produtos_adicionados += 1

        db.session.commit()
        flash(f'Importação concluída! {produtos_adicionados} produtos adicionados, {produtos_atualizados} atualizados.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ocorreu um erro durante a importação: {e}', 'danger')

    return redirect(url_for('configuracoes'))