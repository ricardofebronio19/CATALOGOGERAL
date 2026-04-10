"""
Extensões do modelo de dados para Sistema de Favoritos Avançado
Adiciona novas tabelas para listas personalizadas de produtos
"""

from datetime import datetime
from flask_login import UserMixin
from app import db


class ListaFavoritos(db.Model):
    """
    Listas personalizadas de produtos favoritos criadas pelos usuários
    """
    __tablename__ = 'lista_favoritos'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    cor = db.Column(db.String(7), default='#ff6600')  # Hex color
    icone = db.Column(db.String(50), default='⭐')  # Emoji ou nome de ícone
    publica = db.Column(db.Boolean, default=False)  # Lista pública ou privada
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    criada_em = db.Column(db.DateTime, default=datetime.utcnow)
    atualizada_em = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relacionamentos
    user = db.relationship('User', backref='listas_favoritos')
    itens = db.relationship('ItemListaFavoritos', backref='lista', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<ListaFavoritos {self.nome}>'
    
    @property
    def total_itens(self):
        """Retorna o número total de itens na lista"""
        return len(self.itens)
    
    @property
    def produtos_unicos(self):
        """Retorna lista de produtos únicos na lista"""
        return [item.produto for item in self.itens]


class ItemListaFavoritos(db.Model):
    """
    Item individual em uma lista de favoritos
    """
    __tablename__ = 'item_lista_favoritos'
    
    id = db.Column(db.Integer, primary_key=True)
    lista_id = db.Column(db.Integer, db.ForeignKey('lista_favoritos.id'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    observacoes = db.Column(db.Text, nullable=True)  # Notas específicas sobre este item
    ordem = db.Column(db.Integer, default=0)  # Para ordenação personalizada
    adicionado_em = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relacionamentos
    produto = db.relationship('Produto', backref='favoritos')
    
    # Constraint para evitar duplicatas
    __table_args__ = (
        db.UniqueConstraint('lista_id', 'produto_id', name='uq_lista_produto'),
    )
    
    def __repr__(self):
        return f'<ItemListaFavoritos Lista:{self.lista_id} Produto:{self.produto_id}>'


class HistoricoVisualizacao(db.Model):
    """
    Histórico de visualizações de produtos por usuário
    """
    __tablename__ = 'historico_visualizacao'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    visualizado_em = db.Column(db.DateTime, default=datetime.utcnow)
    origem = db.Column(db.String(50), default='web')  # web, api, search, etc.
    
    # Relacionamentos
    user = db.relationship('User', backref='visualizacoes')
    produto = db.relationship('Produto', backref='visualizacoes')
    
    def __repr__(self):
        return f'<HistoricoVisualizacao User:{self.user_id} Produto:{self.produto_id}>'


class ProdutoRecomendado(db.Model):
    """
    Recomendações personalizadas baseadas no histórico do usuário
    """
    __tablename__ = 'produto_recomendado'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    score = db.Column(db.Float, default=0.0)  # Score de confiança da recomendação
    algoritmo = db.Column(db.String(50), nullable=False)  # collaborative, content, hybrid
    motivo = db.Column(db.String(200), nullable=True)  # Explicação da recomendação
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    expirado = db.Column(db.Boolean, default=False)
    
    # Relacionamentos
    user = db.relationship('User', backref='recomendacoes')
    produto = db.relationship('Produto', backref='recomendacoes')
    
    # Constraint para evitar duplicatas ativas
    __table_args__ = (
        db.UniqueConstraint('user_id', 'produto_id', name='uq_user_produto_recomendacao'),
    )
    
    def __repr__(self):
        return f'<ProdutoRecomendado User:{self.user_id} Produto:{self.produto_id} Score:{self.score}>'


class CompartilhamentoLista(db.Model):
    """
    Compartilhamento de listas entre usuários
    """
    __tablename__ = 'compartilhamento_lista'
    
    id = db.Column(db.Integer, primary_key=True)
    lista_id = db.Column(db.Integer, db.ForeignKey('lista_favoritos.id'), nullable=False)
    compartilhado_por = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    compartilhado_com = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False) 
    permissao = db.Column(db.String(20), default='read')  # read, write
    token_publico = db.Column(db.String(32), nullable=True, unique=True)  # Para links públicos
    criado_em = db.Column(db.DateTime, default=datetime.utcnow)
    ativo = db.Column(db.Boolean, default=True)
    
    # Relacionamentos
    lista = db.relationship('ListaFavoritos', backref='compartilhamentos')
    usuario_proprietario = db.relationship('User', foreign_keys=[compartilhado_por], backref='compartilhamentos_criados')
    usuario_destinatario = db.relationship('User', foreign_keys=[compartilhado_com], backref='compartilhamentos_recebidos')
    
    def __repr__(self):
        return f'<CompartilhamentoLista Lista:{self.lista_id} De:{self.compartilhado_por} Para:{self.compartilhado_com}>'


# Extensões para o modelo User existente (adicionar via método)
def add_user_favorites_methods():
    """Adiciona métodos relacionados a favoritos ao modelo User existente"""
    
    def get_listas_favoritos(self):
        """Retorna todas as listas de favoritos do usuário"""
        return ListaFavoritos.query.filter_by(user_id=self.id).order_by(ListaFavoritos.atualizada_em.desc()).all()
    
    def get_produtos_favoritados(self):
        """Retorna todos os produtos que estão em alguma lista de favoritos do usuário"""
        from models import Produto
        produto_ids = db.session.query(ItemListaFavoritos.produto_id).join(
            ListaFavoritos
        ).filter(ListaFavoritos.user_id == self.id).distinct().all()
        
        return Produto.query.filter(Produto.id.in_([pid[0] for pid in produto_ids])).all()
    
    def get_historico_recent(self, limit=20):
        """Retorna histórico recente de visualizações"""
        return HistoricoVisualizacao.query.filter_by(
            user_id=self.id
        ).order_by(HistoricoVisualizacao.visualizado_em.desc()).limit(limit).all()
    
    def get_recomendacoes_ativas(self, limit=10):
        """Retorna recomendações ativas para o usuário"""
        return ProdutoRecomendado.query.filter_by(
            user_id=self.id, expirado=False
        ).order_by(ProdutoRecomendado.score.desc()).limit(limit).all()
    
    def add_to_lista(self, lista_id, produto_id, observacoes=None):
        """Adiciona produto a uma lista de favoritos"""
        # Verifica se o item já existe
        existing = ItemListaFavoritos.query.filter_by(
            lista_id=lista_id, produto_id=produto_id
        ).first()
        
        if existing:
            return False, "Produto já está na lista"
        
        # Adiciona o item
        item = ItemListaFavoritos(
            lista_id=lista_id,
            produto_id=produto_id,
            observacoes=observacoes,
            ordem=self._get_next_order(lista_id)
        )
        
        db.session.add(item)
        
        # Atualiza timestamp da lista
        lista = ListaFavoritos.query.get(lista_id)
        if lista:
            lista.atualizada_em = datetime.utcnow()
        
        db.session.commit()
        return True, item
    
    def remove_from_lista(self, lista_id, produto_id):
        """Remove produto de uma lista de favoritos"""
        item = ItemListaFavoritos.query.filter_by(
            lista_id=lista_id, produto_id=produto_id
        ).first()
        
        if not item:
            return False, "Item não encontrado na lista"
        
        db.session.delete(item)
        
        # Atualiza timestamp da lista
        lista = ListaFavoritos.query.get(lista_id)
        if lista:
            lista.atualizada_em = datetime.utcnow()
        
        db.session.commit()
        return True, "Item removido da lista"
    
    def _get_next_order(self, lista_id):
        """Retorna a próxima ordem para item na lista"""
        last_item = ItemListaFavoritos.query.filter_by(
            lista_id=lista_id
        ).order_by(ItemListaFavoritos.ordem.desc()).first()
        
        return (last_item.ordem + 1) if last_item else 1
    
    def register_view(self, produto_id, origem='web'):
        """Registra visualização de produto"""
        # Remove visualizações muito antigas do mesmo produto (mantém só as 5 mais recentes)
        old_views = HistoricoVisualizacao.query.filter_by(
            user_id=self.id, produto_id=produto_id
        ).order_by(HistoricoVisualizacao.visualizado_em.desc()).offset(5).all()
        
        for view in old_views:
            db.session.delete(view)
        
        # Adiciona nova visualização
        nova_view = HistoricoVisualizacao(
            user_id=self.id,
            produto_id=produto_id,
            origem=origem
        )
        
        db.session.add(nova_view)
        db.session.commit()
        
        return nova_view
    
    # Adiciona métodos ao modelo User
    from models import User
    User.get_listas_favoritos = get_listas_favoritos
    User.get_produtos_favoritados = get_produtos_favoritados
    User.get_historico_recent = get_historico_recent
    User.get_recomendacoes_ativas = get_recomendacoes_ativas
    User.add_to_lista = add_to_lista
    User.remove_from_lista = remove_from_lista
    User._get_next_order = _get_next_order
    User.register_view = register_view


# Utility functions
def criar_lista_default(user_id):
    """Cria lista padrão de favoritos para novo usuário"""
    lista_default = ListaFavoritos(
        nome="Meus Favoritos",
        descricao="Lista padrão de produtos favoritos",
        cor="#ff6600",
        icone="⭐",
        user_id=user_id,
        publica=False
    )
    
    db.session.add(lista_default)
    db.session.commit()
    
    return lista_default


def gerar_recomendacoes_usuario(user_id, limit=10):
    """
    Gera recomendações automáticas para um usuário
    Baseado em histórico de visualizações e produtos similares
    """
    from models import Produto, Aplicacao
    from sqlalchemy import func, desc
    
    # Remove recomendações expiradas
    ProdutoRecomendado.query.filter_by(user_id=user_id, expirado=True).delete()
    
    # Busca grupos mais visualizados pelo usuário
    grupos_populares = db.session.query(
        Produto.grupo,
        func.count(HistoricoVisualizacao.id).label('count')
    ).join(HistoricoVisualizacao).filter(
        HistoricoVisualizacao.user_id == user_id
    ).group_by(Produto.grupo).order_by(desc('count')).limit(3).all()
    
    recommendations = []
    
    for grupo, count in grupos_populares:
        # Busca produtos similares no mesmo grupo que o usuário ainda não viu
        produtos_recomendados = Produto.query.filter(
            Produto.grupo == grupo,
            ~Produto.id.in_(
                db.session.query(HistoricoVisualizacao.produto_id).filter_by(user_id=user_id)
            )
        ).order_by(func.random()).limit(3).all()
        
        for produto in produtos_recomendados:
            score = min(0.7 + (count * 0.1), 0.95)  # Score baseado na popularidade do grupo
            
            recomendacao = ProdutoRecomendado(
                user_id=user_id,
                produto_id=produto.id,
                score=score,
                algoritmo='content_based',
                motivo=f'Baseado no seu interesse em {grupo}'
            )
            
            recommendations.append(recomendacao)
    
    # Salva recomendações
    for rec in recommendations:
        existing = ProdutoRecomendado.query.filter_by(
            user_id=user_id, produto_id=rec.produto_id
        ).first()
        if not existing:
            db.session.add(rec)
    
    db.session.commit()
    
    return len(recommendations)


def limpar_historico_antigo(dias=90):
    """Remove histórico de visualizações muito antigo"""
    from datetime import datetime, timedelta
    
    cutoff_date = datetime.utcnow() - timedelta(days=dias)
    
    old_views = HistoricoVisualizacao.query.filter(
        HistoricoVisualizacao.visualizado_em < cutoff_date
    ).all()
    
    for view in old_views:
        db.session.delete(view)
    
    db.session.commit()
    
    return len(old_views)