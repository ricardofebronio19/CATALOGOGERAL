from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

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
    conversoes = db.Column(db.Text, nullable=True)
    medidas = db.Column(db.String(255), nullable=True)
    observacoes = db.Column(db.Text, nullable=True)

    similares = db.relationship('Produto', secondary=similares_association,
                                primaryjoin=(similares_association.c.produto_id == id),
                                secondaryjoin=(similares_association.c.similar_id == id),
                                backref=db.backref('similar_to'))

    aplicacoes = db.relationship('Aplicacao', backref='produto', lazy=True, cascade="all, delete-orphan")
    imagens = db.relationship('ImagemProduto', backref='produto', lazy=True, cascade="all, delete-orphan", order_by='ImagemProduto.ordem')

    def __repr__(self):
        return f'<Produto {self.nome}>'

class Aplicacao(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    veiculo = db.Column(db.String(100), nullable=True)
    ano = db.Column(db.String(10), nullable=True)
    motor = db.Column(db.String(100), nullable=True)
    conf_mtr = db.Column(db.String(100), nullable=True)
    montadora = db.Column(db.String(100), nullable=True)

    def __repr__(self):
        return f'<Aplicacao {self.montadora} {self.veiculo}>'

class ImagemProduto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    produto_id = db.Column(db.Integer, db.ForeignKey('produto.id'), nullable=False)
    filename = db.Column(db.String(100), nullable=False)
    ordem = db.Column(db.Integer, default=0)

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