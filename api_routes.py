"""
API REST para o sistema de Catálogo de Peças CGI
Fornece endpoints RESTful para integração externa
"""

from datetime import datetime
from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, login_user, logout_user, current_user
from sqlalchemy.orm import selectinload
from sqlalchemy import func, desc

from app import db, get_logger
from models import Produto, Aplicacao, ImagemProduto, User, Contato
from core_utils import _build_search_query, _normalize_for_search, allowed_file
from utils.image_utils import download_image_from_url
from werkzeug.utils import secure_filename

import os
import json

# Logger específico para API
logger = get_logger('api')

# Blueprint da API REST
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# Configurações da API
API_VERSION = "1.0.0"
MAX_RESULTS_PER_PAGE = 100
DEFAULT_RESULTS_PER_PAGE = 20

def api_response(data=None, message=None, status_code=200, error=None):
    """
    Estrutura padronizada de resposta da API
    
    Args:
        data: Dados a serem retornados
        message: Mensagem informativa
        status_code: Código HTTP de status
        error: Detalhes do erro (se houver)
    
    Returns:
        Resposta JSON estruturada
    """
    response = {
        'version': API_VERSION,
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'status': 'success' if status_code < 400 else 'error'
    }
    
    if data is not None:
        response['data'] = data
    if message:
        response['message'] = message
    if error:
        response['error'] = error
    
    return jsonify(response), status_code

def serialize_produto(produto):
    """Serializa um objeto Produto para JSON"""
    return {
        'id': produto.id,
        'codigo': produto.codigo,
        'nome': produto.nome,
        'grupo': produto.grupo,
        'fornecedor': produto.fornecedor,
        'conversoes': produto.conversoes,
        'medidas': produto.medidas,
        'observacoes': produto.observacoes,
        'aplicacoes': [serialize_aplicacao(app) for app in produto.aplicacoes],
        'imagens': [serialize_imagem(img) for img in produto.imagens],
        'similares_ids': [similar.id for similar in produto.similares]
    }

def serialize_aplicacao(aplicacao):
    """Serializa um objeto Aplicacao para JSON"""
    return {
        'id': aplicacao.id,
        'veiculo': aplicacao.veiculo,
        'ano': aplicacao.ano,
        'motor': aplicacao.motor,
        'conf_mtr': aplicacao.conf_mtr,
        'montadora': aplicacao.montadora
    }

def serialize_imagem(imagem):
    """Serializa um objeto ImagemProduto para JSON"""
    return {
        'id': imagem.id,
        'filename': imagem.filename,
        'ordem': imagem.ordem,
        'url': f"/uploads/{imagem.filename}"
    }

def validate_produto_data(data):
    """
    Valida dados de produto para criação/atualização
    
    Returns:
        (bool, str): (is_valid, error_message)
    """
    required_fields = ['codigo', 'nome']
    
    for field in required_fields:
        if field not in data or not data[field]:
            return False, f"Campo obrigatório '{field}' não fornecido"
    
    # Validações específicas
    if len(data['codigo']) > 50:
        return False, "Código deve ter no máximo 50 caracteres"
    
    if len(data['nome']) > 100:
        return False, "Nome deve ter no máximo 100 caracteres"
    
    return True, None

# ===== ENDPOINTS DA API =====

@api_bp.route('/health', methods=['GET'])
def health_check():
    """Endpoint de verificação de saúde da API"""
    return api_response(data={
        'status': 'healthy',
        'version': API_VERSION,
        'database': 'connected'
    }, message="API está funcionando corretamente")

@api_bp.route('/info', methods=['GET'])
def api_info():
    """Informações sobre a API"""
    return api_response(data={
        'name': 'CGI Catálogo de Peças API',
        'version': API_VERSION,
        'endpoints': {
            'produtos': '/api/v1/produtos',
            'aplicacoes': '/api/v1/aplicacoes',
            'contatos': '/api/v1/contatos',
            'buscar': '/api/v1/buscar',
            'health': '/api/v1/health'
        },
        'auth': 'Required for write operations',
        'pagination': {
            'max_per_page': MAX_RESULTS_PER_PAGE,
            'default_per_page': DEFAULT_RESULTS_PER_PAGE
        }
    })

# ===== PRODUTOS =====

@api_bp.route('/produtos', methods=['GET'])
def list_produtos():
    """Lista produtos com paginação e filtros"""
    try:
        # Parâmetros de paginação
        page = request.args.get('page', 1, type=int)
        per_page = min(
            request.args.get('per_page', DEFAULT_RESULTS_PER_PAGE, type=int),
            MAX_RESULTS_PER_PAGE
        )
        
        # Filtros específicos
        codigo = request.args.get('codigo')
        fornecedor = request.args.get('fornecedor')
        grupo = request.args.get('grupo')
        termo = request.args.get('q')  # Busca geral
        
        # Construção da query
        query = Produto.query.options(
            selectinload(Produto.aplicacoes),
            selectinload(Produto.imagens)
        )
        
        if codigo:
            query = query.filter(Produto.codigo.ilike(f'%{codigo}%'))
        if fornecedor:
            query = query.filter(Produto.fornecedor.ilike(f'%{fornecedor}%'))
        if grupo:
            query = query.filter(Produto.grupo.ilike(f'%{grupo}%'))
        if termo:
            query = query.filter(db.or_(
                Produto.nome.ilike(f'%{termo}%'),
                Produto.codigo.ilike(f'%{termo}%'),
                Produto.fornecedor.ilike(f'%{termo}%')
            ))
        
        # Ordenação
        order_by = request.args.get('order_by', 'codigo')
        order_dir = request.args.get('order_dir', 'asc')
        
        if hasattr(Produto, order_by):
            column = getattr(Produto, order_by)
            if order_dir.lower() == 'desc':
                query = query.order_by(desc(column))
            else:
                query = query.order_by(column)
        
        # Paginação
        produtos_paginados = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Serialização dos resultados
        produtos_data = [serialize_produto(produto) for produto in produtos_paginados.items]
        
        return api_response(data={
            'produtos': produtos_data,
            'pagination': {
                'page': produtos_paginados.page,
                'pages': produtos_paginados.pages,
                'per_page': produtos_paginados.per_page,
                'total': produtos_paginados.total,
                'has_next': produtos_paginados.has_next,
                'has_prev': produtos_paginados.has_prev,
                'next_num': produtos_paginados.next_num,
                'prev_num': produtos_paginados.prev_num
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao listar produtos: {str(e)}")
        return api_response(
            error="Erro interno do servidor",
            status_code=500
        )

@api_bp.route('/produtos/<int:produto_id>', methods=['GET'])
def get_produto(produto_id):
    """Obtém detalhes de um produto específico"""
    try:
        produto = Produto.query.options(
            selectinload(Produto.aplicacoes),
            selectinload(Produto.imagens),
            selectinload(Produto.similares)
        ).get_or_404(produto_id)
        
        return api_response(data={
            'produto': serialize_produto(produto)
        })
        
    except Exception as e:
        logger.error(f"Erro ao buscar produto {produto_id}: {str(e)}")
        return api_response(
            error="Produto não encontrado",
            status_code=404
        )

@api_bp.route('/produtos', methods=['POST'])
@login_required
def create_produto():
    """Cria um novo produto"""
    try:
        data = request.get_json()
        
        # Validação
        is_valid, error_msg = validate_produto_data(data)
        if not is_valid:
            return api_response(error=error_msg, status_code=400)
        
        # Verifica duplicatas (código + fornecedor único)
        fornecedor = data.get('fornecedor')
        existing = Produto.query.filter_by(
            codigo=data['codigo'],
            fornecedor=fornecedor
        ).first()
        
        if existing:
            return api_response(
                error=f"Produto com código '{data['codigo']}' já existe para o fornecedor '{fornecedor}'",
                status_code=409
            )
        
        # Cria novo produto
        produto = Produto(
            codigo=data['codigo'].upper(),
            nome=data['nome'].upper(),
            grupo=data.get('grupo', '').upper(),
            fornecedor=data.get('fornecedor', '').upper(),
            conversoes=data.get('conversoes'),
            medidas=data.get('medidas'),
            observacoes=data.get('observacoes')
        )
        
        db.session.add(produto)
        db.session.flush()  # Para obter o ID antes do commit
        
        # Adiciona aplicações se fornecidas
        if 'aplicacoes' in data:
            for app_data in data['aplicacoes']:
                aplicacao = Aplicacao(
                    produto_id=produto.id,
                    veiculo=app_data.get('veiculo'),
                    ano=app_data.get('ano'),
                    motor=app_data.get('motor'),
                    conf_mtr=app_data.get('conf_mtr'),
                    montadora=app_data.get('montadora')
                )
                db.session.add(aplicacao)
        
        db.session.commit()
        
        logger.info(f"Produto criado via API: {produto.codigo} (ID: {produto.id}) por usuário {current_user.username}")
        
        return api_response(
            data={'produto': serialize_produto(produto)},
            message="Produto criado com sucesso",
            status_code=201
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao criar produto via API: {str(e)}")
        return api_response(
            error="Erro interno do servidor",
            status_code=500
        )

@api_bp.route('/produtos/<int:produto_id>', methods=['PUT'])
@login_required
def update_produto(produto_id):
    """Atualiza um produto existente"""
    try:
        produto = Produto.query.get_or_404(produto_id)
        data = request.get_json()
        
        # Validação
        is_valid, error_msg = validate_produto_data(data)
        if not is_valid:
            return api_response(error=error_msg, status_code=400)
        
        # Atualiza campos do produto
        produto.codigo = data.get('codigo', produto.codigo).upper()
        produto.nome = data.get('nome', produto.nome).upper()
        produto.grupo = data.get('grupo', produto.grupo).upper() if data.get('grupo') else produto.grupo
        produto.fornecedor = data.get('fornecedor', produto.fornecedor).upper() if data.get('fornecedor') else produto.fornecedor
        produto.conversoes = data.get('conversoes', produto.conversoes)
        produto.medidas = data.get('medidas', produto.medidas)  
        produto.observacoes = data.get('observacoes', produto.observacoes)
        
        db.session.commit()
        
        logger.info(f"Produto atualizado via API: {produto.codigo} (ID: {produto.id}) por usuário {current_user.username}")
        
        return api_response(
            data={'produto': serialize_produto(produto)},
            message="Produto atualizado com sucesso"
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao atualizar produto {produto_id} via API: {str(e)}")
        return api_response(
            error="Erro interno do servidor",
            status_code=500
        )

@api_bp.route('/produtos/<int:produto_id>', methods=['DELETE'])
@login_required
def delete_produto(produto_id):
    """Remove um produto"""
    try:
        produto = Produto.query.get_or_404(produto_id)
        
        # Verifica se usuário tem permissão (apenas admins podem deletar)
        if not current_user.is_admin:
            return api_response(
                error="Acesso negado: apenas administradores podem deletar produtos",
                status_code=403
            )
        
        codigo_produto = produto.codigo
        db.session.delete(produto)
        db.session.commit()
        
        logger.info(f"Produto deletado via API: {codigo_produto} (ID: {produto_id}) por admin {current_user.username}")
        
        return api_response(
            message=f"Produto '{codigo_produto}' removido com sucesso"
        )
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Erro ao deletar produto {produto_id} via API: {str(e)}")
        return api_response(
            error="Erro interno do servidor", 
            status_code=500
        )

# ===== BUSCA =====

@api_bp.route('/buscar', methods=['GET'])
def search_produtos():
    """Endpoint de busca avançada"""
    try:
        # Parâmetros de busca
        termo = request.args.get('q', '')
        codigo_produto = request.args.get('codigo')
        montadora = request.args.get('montadora')
        aplicacao_termo = request.args.get('aplicacao')
        grupo = request.args.get('grupo')
        medidas = request.args.get('medidas')
        
        # Paginação
        page = request.args.get('page', 1, type=int)
        per_page = min(
            request.args.get('per_page', DEFAULT_RESULTS_PER_PAGE, type=int),
            MAX_RESULTS_PER_PAGE
        )
        
        # Usa a função de busca existente do sistema
        query = _build_search_query(
            termo, codigo_produto, montadora, aplicacao_termo, grupo, medidas
        )
        
        query = query.options(
            selectinload(Produto.aplicacoes),
            selectinload(Produto.imagens)
        )
        
        # Paginação
        resultados_paginados = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        # Serialização
        produtos_data = [serialize_produto(produto) for produto in resultados_paginados.items]
        
        return api_response(data={
            'produtos': produtos_data,
            'search_params': {
                'termo': termo,
                'codigo': codigo_produto,
                'montadora': montadora,
                'aplicacao': aplicacao_termo,
                'grupo': grupo,
                'medidas': medidas
            },
            'pagination': {
                'page': resultados_paginados.page,
                'pages': resultados_paginados.pages,
                'per_page': resultados_paginados.per_page,
                'total': resultados_paginados.total,
                'has_next': resultados_paginados.has_next,
                'has_prev': resultados_paginados.has_prev
            }
        })
        
    except Exception as e:
        logger.error(f"Erro na busca via API: {str(e)}")
        return api_response(
            error="Erro interno do servidor",
            status_code=500
        )

# ===== APLICAÇÕES =====

@api_bp.route('/aplicacoes', methods=['GET'])
def list_aplicacoes():
    """Lista aplicações com filtros"""
    try:
        # Parâmetros
        page = request.args.get('page', 1, type=int)
        per_page = min(
            request.args.get('per_page', DEFAULT_RESULTS_PER_PAGE, type=int),
            MAX_RESULTS_PER_PAGE
        )
        
        montadora = request.args.get('montadora')
        veiculo = request.args.get('veiculo')
        produto_id = request.args.get('produto_id', type=int)
        
        query = Aplicacao.query
        
        if montadora:
            query = query.filter(Aplicacao.montadora.ilike(f'%{montadora}%'))
        if veiculo:
            query = query.filter(Aplicacao.veiculo.ilike(f'%{veiculo}%'))
        if produto_id:
            query = query.filter(Aplicacao.produto_id == produto_id)
        
        aplicacoes_paginadas = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        aplicacoes_data = [serialize_aplicacao(app) for app in aplicacoes_paginadas.items]
        
        return api_response(data={
            'aplicacoes': aplicacoes_data,
            'pagination': {
                'page': aplicacoes_paginadas.page,
                'pages': aplicacoes_paginadas.pages,
                'total': aplicacoes_paginadas.total
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao listar aplicações: {str(e)}")
        return api_response(
            error="Erro interno do servidor",
            status_code=500
        )

# ===== ESTATÍSTICAS =====

@api_bp.route('/stats', methods=['GET'])
def get_statistics():
    """Retorna estatísticas gerais do sistema"""
    try:
        stats = {
            'produtos': {
                'total': Produto.query.count(),
                'por_fornecedor': dict(db.session.query(
                    Produto.fornecedor, func.count(Produto.id)
                ).group_by(Produto.fornecedor).all()),
                'por_grupo': dict(db.session.query(
                    Produto.grupo, func.count(Produto.id)
                ).group_by(Produto.grupo).all())
            },
            'aplicacoes': {
                'total': Aplicacao.query.count(),
                'por_montadora': dict(db.session.query(
                    Aplicacao.montadora, func.count(Aplicacao.id)
                ).group_by(Aplicacao.montadora).all())
            },
            'imagens': {
                'total': ImagemProduto.query.count()
            }
        }
        
        return api_response(data={'statistics': stats})
        
    except Exception as e:
        logger.error(f"Erro ao obter estatísticas: {str(e)}")
        return api_response(
            error="Erro interno do servidor",
            status_code=500
        )

# ===== CONTATOS =====

@api_bp.route('/contatos', methods=['GET'])
def list_contatos():
    """Lista contatos com paginação"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(
            request.args.get('per_page', DEFAULT_RESULTS_PER_PAGE, type=int),
            MAX_RESULTS_PER_PAGE
        )
        
        favoritos_apenas = request.args.get('favoritos', type=bool)
        busca = request.args.get('q')
        
        query = Contato.query
        
        if favoritos_apenas:
            query = query.filter(Contato.favorito == True)
        
        if busca:
            query = query.filter(db.or_(
                Contato.nome.ilike(f'%{busca}%'),
                Contato.empresa.ilike(f'%{busca}%'),
                Contato.email.ilike(f'%{busca}%')
            ))
        
        contatos_paginados = query.order_by(Contato.nome).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        contatos_data = []
        for contato in contatos_paginados.items:
            contatos_data.append({
                'id': contato.id,
                'nome': contato.nome,
                'empresa': contato.empresa,
                'telefone': contato.telefone,
                'whatsapp': contato.whatsapp,
                'email': contato.email,
                'cargo': contato.cargo,
                'endereco': contato.endereco,
                'observacoes': contato.observacoes,
                'favorito': contato.favorito,
                'criado_em': contato.criado_em.isoformat() if contato.criado_em else None,
                'atualizado_em': contato.atualizado_em.isoformat() if contato.atualizado_em else None
            })
        
        return api_response(data={
            'contatos': contatos_data,
            'pagination': {
                'page': contatos_paginados.page,
                'pages': contatos_paginados.pages,
                'total': contatos_paginados.total
            }
        })
        
    except Exception as e:
        logger.error(f"Erro ao listar contatos: {str(e)}")
        return api_response(
            error="Erro interno do servidor",
            status_code=500
        )

# ===== AUTH =====

@api_bp.route('/auth/login', methods=['POST'])
def api_login():
    """Login via JSON para clientes mobile/API"""
    from models import User
    data = request.get_json()
    if not data:
        return api_response(error="JSON body obrigatório", status_code=400)

    username = data.get('username', '').strip()
    password = data.get('password', '')

    if not username or not password:
        return api_response(error="Username e senha são obrigatórios", status_code=400)

    user = User.query.filter_by(username=username).first()
    if user is None or not user.check_password(password):
        return api_response(error="Usuário ou senha inválidos", status_code=401)

    login_user(user, remember=True)
    logger.info(f"Login via API: {user.username}")

    return api_response(data={
        'user': {
            'id': user.id,
            'username': user.username,
            'is_admin': user.is_admin
        }
    }, message="Login realizado com sucesso")


@api_bp.route('/auth/logout', methods=['POST'])
@login_required
def api_logout():
    """Logout para clientes mobile/API"""
    logout_user()
    return api_response(message="Logout realizado com sucesso")


@api_bp.route('/auth/me', methods=['GET'])
@login_required
def api_me():
    """Retorna dados do usuário autenticado"""
    return api_response(data={
        'user': {
            'id': current_user.id,
            'username': current_user.username,
            'is_admin': current_user.is_admin
        }
    })


# ===== CONTATOS CRUD =====

@api_bp.route('/contatos/<int:contato_id>', methods=['GET'])
@login_required
def get_contato(contato_id):
    """Retorna detalhes de um contato"""
    contato = Contato.query.get_or_404(contato_id)
    return api_response(data={'contato': {
        'id': contato.id,
        'nome': contato.nome,
        'empresa': contato.empresa,
        'telefone': contato.telefone,
        'whatsapp': contato.whatsapp,
        'email': contato.email,
        'cargo': contato.cargo,
        'endereco': contato.endereco,
        'observacoes': contato.observacoes,
        'favorito': contato.favorito,
    }})


@api_bp.route('/contatos', methods=['POST'])
@login_required
def create_contato():
    """Cria um novo contato"""
    data = request.get_json()
    if not data or not data.get('nome'):
        return api_response(error="Campo 'nome' é obrigatório", status_code=400)

    contato = Contato(
        nome=data['nome'],
        empresa=data.get('empresa'),
        telefone=data.get('telefone'),
        whatsapp=data.get('whatsapp'),
        email=data.get('email'),
        cargo=data.get('cargo'),
        endereco=data.get('endereco'),
        observacoes=data.get('observacoes'),
        favorito=bool(data.get('favorito', False)),
    )
    db.session.add(contato)
    db.session.commit()
    return api_response(data={'contato': {'id': contato.id, 'nome': contato.nome}},
                        message="Contato criado com sucesso", status_code=201)


@api_bp.route('/contatos/<int:contato_id>', methods=['PUT'])
@login_required
def update_contato(contato_id):
    """Atualiza um contato existente"""
    contato = Contato.query.get_or_404(contato_id)
    data = request.get_json()
    if not data:
        return api_response(error="JSON body obrigatório", status_code=400)

    if 'nome' in data:
        contato.nome = data['nome']
    for field in ('empresa', 'telefone', 'whatsapp', 'email', 'cargo', 'endereco', 'observacoes'):
        if field in data:
            setattr(contato, field, data[field])
    if 'favorito' in data:
        contato.favorito = bool(data['favorito'])

    db.session.commit()
    return api_response(data={'contato': {'id': contato.id, 'nome': contato.nome}},
                        message="Contato atualizado com sucesso")


@api_bp.route('/contatos/<int:contato_id>', methods=['DELETE'])
@login_required
def delete_contato(contato_id):
    """Remove um contato"""
    contato = Contato.query.get_or_404(contato_id)
    db.session.delete(contato)
    db.session.commit()
    return api_response(message="Contato removido com sucesso")


# ===== CARRINHO =====

def _cart_response(app_instance):
    """Helper: retorna estado atual do carrinho como dict"""
    from utils.cart_utils import get_cart_items, get_cart_count, get_cart_summary
    items = get_cart_items(app_instance)
    count = get_cart_count(app_instance)
    summary = get_cart_summary(app_instance)
    return {
        'items': [
            {
                'produto_id': item['produto_id'],
                'codigo': item.get('codigo'),
                'nome': item.get('nome'),
                'quantidade': item.get('quantidade', 1),
                'imagem': item.get('imagem'),
            }
            for item in (items or [])
        ],
        'total_items': count,
        'summary': summary,
    }


@api_bp.route('/carrinho', methods=['GET'])
@login_required
def api_get_carrinho():
    """Retorna o carrinho atual"""
    return api_response(data=_cart_response(current_app._get_current_object()))


@api_bp.route('/carrinho/adicionar', methods=['POST'])
@login_required
def api_add_carrinho():
    """Adiciona produto ao carrinho"""
    from utils.cart_utils import add_to_cart
    data = request.get_json()
    produto_id = data.get('produto_id') if data else None
    quantidade = int(data.get('quantidade', 1)) if data else 1
    if not produto_id:
        return api_response(error="produto_id é obrigatório", status_code=400)
    add_to_cart(current_app._get_current_object(), produto_id, quantidade)
    return api_response(data=_cart_response(current_app._get_current_object()),
                        message="Produto adicionado ao carrinho")


@api_bp.route('/carrinho/remover', methods=['POST'])
@login_required
def api_remove_carrinho():
    """Remove produto do carrinho"""
    from utils.cart_utils import remove_from_cart
    data = request.get_json()
    produto_id = data.get('produto_id') if data else None
    if not produto_id:
        return api_response(error="produto_id é obrigatório", status_code=400)
    remove_from_cart(current_app._get_current_object(), produto_id)
    return api_response(data=_cart_response(current_app._get_current_object()),
                        message="Produto removido do carrinho")


@api_bp.route('/carrinho/atualizar', methods=['POST'])
@login_required
def api_update_carrinho():
    """Atualiza quantidade de um item no carrinho"""
    from utils.cart_utils import update_cart_item
    data = request.get_json()
    produto_id = data.get('produto_id') if data else None
    quantidade = int(data.get('quantidade', 1)) if data else 1
    if not produto_id:
        return api_response(error="produto_id é obrigatório", status_code=400)
    update_cart_item(current_app._get_current_object(), produto_id, quantidade)
    return api_response(data=_cart_response(current_app._get_current_object()),
                        message="Carrinho atualizado")


@api_bp.route('/carrinho/limpar', methods=['POST'])
@login_required
def api_limpar_carrinho():
    """Limpa o carrinho"""
    from utils.cart_utils import clear_cart
    clear_cart(current_app._get_current_object())
    return api_response(data=_cart_response(current_app._get_current_object()),
                        message="Carrinho limpo")


# ===== TRATAMENTO DE ERROS =====

@api_bp.errorhandler(404)
def not_found(error):
    return api_response(
        error="Recurso não encontrado",
        status_code=404
    )

@api_bp.errorhandler(400)
def bad_request(error):
    return api_response(
        error="Requisição inválida",
        status_code=400
    )

@api_bp.errorhandler(403)
def forbidden(error):
    return api_response(
        error="Acesso negado",
        status_code=403
    )

@api_bp.errorhandler(500)
def internal_server_error(error):
    return api_response(
        error="Erro interno do servidor",
        status_code=500
    )