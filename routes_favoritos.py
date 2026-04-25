"""
Rotas para Sistema de Favoritos Avançado
Gerenciamento de listas personalizadas, compartilhamento e recomendações
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_required, current_user
from datetime import datetime
import secrets

from app import db
from models_favoritos import (
    ListaFavoritos, ItemListaFavoritos, HistoricoVisualizacao, 
    ProdutoRecomendado, CompartilhamentoLista,
    gerar_recomendacoes_usuario
)
from models import Produto, User
from core_utils import _normalize_for_search

favorites_bp = Blueprint('favorites', __name__, url_prefix='/favoritos')


@favorites_bp.route('/')
@login_required
def index():
    """Dashboard de favoritos do usuário"""
    listas = current_user.get_listas_favoritos()
    historico = current_user.get_historico_recent(limit=10)
    recomendacoes = current_user.get_recomendacoes_ativas(limit=6)
    
    # Estatísticas
    total_favoritos = sum(lista.total_itens for lista in listas)
    listas_publicas = sum(1 for lista in listas if lista.publica)
    
    return render_template('favoritos/dashboard.html',
                         listas=listas,
                         historico=historico,
                         recomendacoes=recomendacoes,
                         total_favoritos=total_favoritos,
                         listas_publicas=listas_publicas)


@favorites_bp.route('/listas')
@login_required
def listar_listas():
    """Lista todas as listas do usuário"""
    listas = current_user.get_listas_favoritos()
    
    return render_template('favoritos/listar_listas.html', listas=listas)


@favorites_bp.route('/lista/criar', methods=['GET', 'POST'])
@login_required
def criar_lista():
    """Criar nova lista de favoritos"""
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        descricao = request.form.get('descricao', '').strip()
        cor = request.form.get('cor', '#ff6600')
        icone = request.form.get('icone', '⭐')
        publica = request.form.get('publica') == 'on'
        
        if not nome:
            flash('Nome da lista é obrigatório', 'error')
            return redirect(url_for('favorites.criar_lista'))
        
        # Verifica se já existe uma lista com esse nome para o usuário
        existing = ListaFavoritos.query.filter_by(
            user_id=current_user.id, nome=nome
        ).first()
        
        if existing:
            flash('Você já possui uma lista com esse nome', 'error')
            return redirect(url_for('favorites.criar_lista'))
        
        nova_lista = ListaFavoritos(
            nome=nome,
            descricao=descricao,
            cor=cor,
            icone=icone,
            publica=publica,
            user_id=current_user.id
        )
        
        db.session.add(nova_lista)
        db.session.commit()
        
        flash(f'Lista "{nome}" criada com sucesso!', 'success')
        return redirect(url_for('favorites.ver_lista', lista_id=nova_lista.id))
    
    return render_template('favoritos/criar_lista.html')


@favorites_bp.route('/lista/<int:lista_id>')
@login_required
def ver_lista(lista_id):
    """Visualizar uma lista específica"""
    lista = ListaFavoritos.query.get_or_404(lista_id)
    
    # Verifica permissão de acesso
    if lista.user_id != current_user.id:
        # Verifica se a lista é pública ou se o usuário tem permissão de compartilhamento
        if not lista.publica:
            compartilhamento = CompartilhamentoLista.query.filter_by(
                lista_id=lista_id,
                compartilhado_com=current_user.id,
                ativo=True
            ).first()
            
            if not compartilhamento:
                flash('Você não tem permissão para acessar esta lista', 'error')
                return redirect(url_for('favorites.index'))
    
    # Busca produtos da lista ordenados
    itens = ItemListaFavoritos.query.filter_by(
        lista_id=lista_id
    ).order_by(ItemListaFavoritos.ordem.asc()).all()
    
    return render_template('favoritos/ver_lista.html', 
                         lista=lista, 
                         itens=itens)


@favorites_bp.route('/lista/<int:lista_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_lista(lista_id):
    """Editar configurações da lista"""
    lista = ListaFavoritos.query.get_or_404(lista_id)
    
    if lista.user_id != current_user.id:
        flash('Você não tem permissão para editar esta lista', 'error')
        return redirect(url_for('favorites.index'))
    
    if request.method == 'POST':
        lista.nome = request.form.get('nome', '').strip()
        lista.descricao = request.form.get('descricao', '').strip()
        lista.cor = request.form.get('cor', '#ff6600')
        lista.icone = request.form.get('icone', '⭐')
        lista.publica = request.form.get('publica') == 'on'
        lista.atualizada_em = datetime.utcnow()
        
        db.session.commit()
        
        flash(f'Lista "{lista.nome}" atualizada com sucesso!', 'success')
        return redirect(url_for('favorites.ver_lista', lista_id=lista.id))
    
    return render_template('favoritos/editar_lista.html', lista=lista)


@favorites_bp.route('/lista/<int:lista_id>/excluir', methods=['POST'])
@login_required
def excluir_lista(lista_id):
    """Excluir lista de favoritos"""
    lista = ListaFavoritos.query.get_or_404(lista_id)
    
    if lista.user_id != current_user.id:
        flash('Você não tem permissão para excluir esta lista', 'error')
        return redirect(url_for('favorites.index'))
    
    nome_lista = lista.nome
    db.session.delete(lista)
    db.session.commit()
    
    flash(f'Lista "{nome_lista}" excluída com sucesso!', 'success')
    return redirect(url_for('favorites.index'))


@favorites_bp.route('/adicionar', methods=['POST'])
@login_required
def adicionar_produto():
    """Adicionar produto a uma lista de favoritos (via AJAX)"""
    try:
        data = request.get_json() or request.form.to_dict()
        lista_id = int(data.get('lista_id'))
        produto_id = int(data.get('produto_id'))
        observacoes = data.get('observacoes', '')
        
        # Verifica se a lista pertence ao usuário
        lista = ListaFavoritos.query.get_or_404(lista_id)
        if lista.user_id != current_user.id:
            return jsonify({'success': False, 'message': 'Permissão negada'})
        
        # Verifica se o produto existe
        produto = Produto.query.get_or_404(produto_id)
        
        success, result = current_user.add_to_lista(lista_id, produto_id, observacoes)
        
        if success:
            return jsonify({
                'success': True, 
                'message': f'Produto adicionado à lista "{lista.nome}"'
            })
        else:
            return jsonify({'success': False, 'message': result})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@favorites_bp.route('/remover', methods=['POST'])
@login_required
def remover_produto():
    """Remover produto de uma lista de favoritos (via AJAX)"""
    try:
        data = request.get_json() or request.form.to_dict()
        lista_id = int(data.get('lista_id'))
        produto_id = int(data.get('produto_id'))
        
        # Verifica se a lista pertence ao usuário
        lista = ListaFavoritos.query.get_or_404(lista_id)
        if lista.user_id != current_user.id:
            return jsonify({'success': False, 'message': 'Permissão negada'})
        
        success, message = current_user.remove_from_lista(lista_id, produto_id)
        
        return jsonify({'success': success, 'message': message})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@favorites_bp.route('/reordenar', methods=['POST'])
@login_required
def reordenar_itens():
    """Reordenar itens em uma lista (drag & drop)"""
    try:
        data = request.get_json()
        lista_id = int(data.get('lista_id'))
        novos_ordem = data.get('novos_ordem', [])  # Array de [item_id, nova_ordem]
        
        # Verifica se a lista pertence ao usuário
        lista = ListaFavoritos.query.get_or_404(lista_id)
        if lista.user_id != current_user.id:
            return jsonify({'success': False, 'message': 'Permissão negada'})
        
        # Atualiza ordem dos itens
        for item_id, nova_ordem in novos_ordem:
            item = ItemListaFavoritos.query.get(item_id)
            if item and item.lista_id == lista_id:
                item.ordem = nova_ordem
        
        lista.atualizada_em = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Ordem atualizada com sucesso'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@favorites_bp.route('/compartilhar/<int:lista_id>')
@login_required
def compartilhar_lista(lista_id):
    """Interface para compartilhar lista"""
    lista = ListaFavoritos.query.get_or_404(lista_id)
    
    if lista.user_id != current_user.id:
        flash('Você não tem permissão para compartilhar esta lista', 'error')
        return redirect(url_for('favorites.index'))
    
    compartilhamentos = CompartilhamentoLista.query.filter_by(
        lista_id=lista_id, ativo=True
    ).all()
    
    return render_template('favoritos/compartilhar_lista.html', 
                         lista=lista,
                         compartilhamentos=compartilhamentos)


@favorites_bp.route('/compartilhar', methods=['POST'])
@login_required
def criar_compartilhamento():
    """Criar compartilhamento de lista"""
    try:
        data = request.get_json() or request.form.to_dict()
        lista_id = int(data.get('lista_id'))
        email_usuario = data.get('email_usuario', '').strip()
        permissao = data.get('permissao', 'read')
        gerar_link_publico = data.get('link_publico') == True
        
        lista = ListaFavoritos.query.get_or_404(lista_id)
        if lista.user_id != current_user.id:
            return jsonify({'success': False, 'message': 'Permissão negada'})
        
        # Se for link público
        if gerar_link_publico:
            # Gera token único
            token = secrets.token_urlsafe(16)
            
            compartilhamento = CompartilhamentoLista(
                lista_id=lista_id,
                compartilhado_por=current_user.id,
                compartilhado_com=None,  # Link público
                permissao='read',
                token_publico=token
            )
            
            db.session.add(compartilhamento)
            db.session.commit()
            
            link_publico = request.host_url.rstrip('/') + url_for('favorites.lista_publica', token=token)
            
            return jsonify({
                'success': True, 
                'message': 'Link público criado',
                'link_publico': link_publico
            })
        
        # Se for compartilhamento com usuário específico
        if email_usuario:
            usuario_destino = User.query.filter_by(email=email_usuario).first()
            if not usuario_destino:
                return jsonify({'success': False, 'message': 'Usuário não encontrado'})
            
            # Verifica se já existe compartilhamento
            existing = CompartilhamentoLista.query.filter_by(
                lista_id=lista_id,
                compartilhado_com=usuario_destino.id,
                ativo=True
            ).first()
            
            if existing:
                return jsonify({'success': False, 'message': 'Lista já compartilhada com este usuário'})
            
            compartilhamento = CompartilhamentoLista(
                lista_id=lista_id,
                compartilhado_por=current_user.id,
                compartilhado_com=usuario_destino.id,
                permissao=permissao
            )
            
            db.session.add(compartilhamento)
            db.session.commit()
            
            return jsonify({
                'success': True, 
                'message': f'Lista compartilhada com {usuario_destino.nome or usuario_destino.email}'
            })
        
        return jsonify({'success': False, 'message': 'Dados insuficientes para compartilhamento'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@favorites_bp.route('/publico/<token>')
def lista_publica(token):
    """Visualizar lista via link público"""
    compartilhamento = CompartilhamentoLista.query.filter_by(
        token_publico=token, ativo=True
    ).first()
    
    if not compartilhamento:
        flash('Link inválido ou expirado', 'error')
        return redirect(url_for('index'))
    
    lista = compartilhamento.lista
    itens = ItemListaFavoritos.query.filter_by(
        lista_id=lista.id
    ).order_by(ItemListaFavoritos.ordem.asc()).all()
    
    return render_template('favoritos/lista_publica.html', 
                         lista=lista, 
                         itens=itens,
                         compartilhamento=compartilhamento)


@favorites_bp.route('/recomendacoes')
@login_required
def recomendacoes():
    """Página de recomendações personalizadas"""
    recomendacoes = current_user.get_recomendacoes_ativas(limit=20)
    
    # Se não tem recomendações, gera algumas
    if len(recomendacoes) < 5:
        count = gerar_recomendacoes_usuario(current_user.id, limit=15)
        recomendacoes = current_user.get_recomendacoes_ativas(limit=20)
        
        if count > 0:
            flash(f'{count} novas recomendações geradas para você!', 'info')
    
    return render_template('favoritos/recomendacoes.html', 
                         recomendacoes=recomendacoes)


@favorites_bp.route('/historico')
@login_required
def historico():
    """Histórico de produtos visualizados"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    visualizacoes = HistoricoVisualizacao.query.filter_by(
        user_id=current_user.id
    ).order_by(
        HistoricoVisualizacao.visualizado_em.desc()
    ).paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('favoritos/historico.html', 
                         visualizacoes=visualizacoes)


@favorites_bp.route('/buscar_produto')
@login_required
def buscar_produto():
    """Buscar produtos para adicionar a listas (via AJAX)"""
    query = request.args.get('q', '').strip()
    
    if not query:
        return jsonify({'produtos': []})
    
    # Busca produtos por código, descrição ou grupo
    normalized_query = _normalize_for_search(query)
    
    produtos = Produto.query.filter(
        db.or_(
            Produto.codigo.ilike(f'%{query}%'),
            Produto.nome.ilike(f'%{query}%'),
            Produto.grupo.ilike(f'%{query}%'),
            Produto.fornecedor.ilike(f'%{query}%')
        )
    ).limit(10).all()
    
    return jsonify({
        'produtos': [{
            'id': p.id,
            'codigo': p.codigo,
            'nome': p.nome,
            'grupo': p.grupo,
            'fornecedor': p.fornecedor
        } for p in produtos]
    })


@favorites_bp.route('/modal_adicionar')
@login_required  
def modal_adicionar():
    """Modal para adicionar produto a listas (via AJAX)"""
    produto_id = request.args.get('produto_id', type=int)
    
    if not produto_id:
        return jsonify({'error': 'produto_id é obrigatório'})
    
    produto = Produto.query.get_or_404(produto_id)
    listas = current_user.get_listas_favoritos()
    
    # Verifica quais listas já contêm o produto
    listas_com_produto = set()
    for lista in listas:
        if ItemListaFavoritos.query.filter_by(lista_id=lista.id, produto_id=produto_id).first():
            listas_com_produto.add(lista.id)
    
    return render_template('favoritos/modal_adicionar.html',
                         produto=produto,
                         listas=listas,
                         listas_com_produto=listas_com_produto)


# API Routes para integração externa
@favorites_bp.route('/api/listas')
@login_required
def api_listas():
    """API: Listar listas do usuário"""
    listas = current_user.get_listas_favoritos()
    
    return jsonify([{
        'id': lista.id,
        'nome': lista.nome,
        'descricao': lista.descricao,
        'cor': lista.cor,
        'icone': lista.icone,
        'publica': lista.publica,
        'total_itens': lista.total_itens,
        'criada_em': lista.criada_em.isoformat(),
        'atualizada_em': lista.atualizada_em.isoformat()
    } for lista in listas])


@favorites_bp.route('/api/lista/<int:lista_id>')
@login_required
def api_lista_detalhes(lista_id):
    """API: Detalhes de uma lista específica"""
    lista = ListaFavoritos.query.get_or_404(lista_id)
    
    if lista.user_id != current_user.id and not lista.publica:
        return jsonify({'error': 'Acesso negado'}), 403
    
    itens = ItemListaFavoritos.query.filter_by(
        lista_id=lista_id
    ).order_by(ItemListaFavoritos.ordem.asc()).all()
    
    return jsonify({
        'id': lista.id,
        'nome': lista.nome,
        'descricao': lista.descricao,
        'cor': lista.cor,
        'icone': lista.icone,
        'publica': lista.publica,
        'total_itens': lista.total_itens,
        'criada_em': lista.criada_em.isoformat(),
        'atualizada_em': lista.atualizada_em.isoformat(),
        'itens': [{
            'produto_id': item.produto_id,
            'produto_codigo': item.produto.codigo,
            'produto_descricao': item.produto.descricao,
            'observacoes': item.observacoes,
            'ordem': item.ordem,
            'adicionado_em': item.adicionado_em.isoformat()
        } for item in itens]
    })


# Hook para registrar visualizações automaticamente
def registrar_visualizacao(produto_id, origem='web'):
    """Função helper para registrar visualizações (chamada de outras rotas)"""
    if current_user.is_authenticated:
        current_user.register_view(produto_id, origem)