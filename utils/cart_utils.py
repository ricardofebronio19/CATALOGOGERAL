# -*- coding: utf-8 -*-
"""
Utilitários para gerenciamento do carrinho de peças.
Usa sessão Flask para armazenar itens do carrinho.
"""

from flask import session


def get_cart_items():
    """
    Retorna a lista de itens no carrinho com detalhes dos produtos.
    
    Returns:
        list: Lista de dicionários com informações do produto e quantidade
    """
    from models import Produto  # Importação tardia para evitar import circular
    
    cart = session.get('cart', [])
    items = []
    
    for item in cart:
        produto = Produto.query.get(item['produto_id'])
        if produto:
            items.append({
                'produto': produto,
                'quantidade': item.get('quantidade', 1),
                'observacoes': item.get('observacoes', '')
            })
    
    return items


def add_to_cart(produto_id, quantidade=1, observacoes=''):
    """
    Adiciona um produto ao carrinho ou atualiza a quantidade se já existir.
    
    Args:
        produto_id (int): ID do produto
        quantidade (int): Quantidade do produto
        observacoes (str): Observações adicionais
    
    Returns:
        bool: True se adicionado com sucesso
    """
    if 'cart' not in session:
        session['cart'] = []
    
    cart = session['cart']
    
    # Verifica se o produto já está no carrinho
    for item in cart:
        if item['produto_id'] == produto_id:
            item['quantidade'] += quantidade
            if observacoes:
                item['observacoes'] = observacoes
            session.modified = True
            return True
    
    # Adiciona novo item
    cart.append({
        'produto_id': produto_id,
        'quantidade': quantidade,
        'observacoes': observacoes
    })
    
    session.modified = True
    return True


def remove_from_cart(produto_id):
    """
    Remove um produto do carrinho.
    
    Args:
        produto_id (int): ID do produto a ser removido
    
    Returns:
        bool: True se removido com sucesso
    """
    if 'cart' not in session:
        return False
    
    cart = session['cart']
    session['cart'] = [item for item in cart if item['produto_id'] != produto_id]
    session.modified = True
    return True


def update_cart_item(produto_id, quantidade, observacoes=''):
    """
    Atualiza quantidade e observações de um item no carrinho.
    
    Args:
        produto_id (int): ID do produto
        quantidade (int): Nova quantidade
        observacoes (str): Novas observações
    
    Returns:
        bool: True se atualizado com sucesso
    """
    if 'cart' not in session:
        return False
    
    cart = session['cart']
    
    for item in cart:
        if item['produto_id'] == produto_id:
            if quantidade <= 0:
                # Remove item se quantidade é 0 ou negativa
                return remove_from_cart(produto_id)
            else:
                item['quantidade'] = quantidade
                item['observacoes'] = observacoes
                session.modified = True
                return True
    
    return False


def clear_cart():
    """
    Limpa todos os itens do carrinho.
    """
    session['cart'] = []
    session.modified = True


def get_cart_count():
    """
    Retorna o número total de itens no carrinho.
    
    Returns:
        int: Total de itens no carrinho
    """
    if 'cart' not in session:
        return 0
    
    return sum(item.get('quantidade', 1) for item in session['cart'])


def get_cart_summary():
    """
    Retorna um resumo do carrinho com contagem e itens.
    
    Returns:
        dict: Dicionário com count e items
    """
    items = get_cart_items()
    return {
        'count': get_cart_count(),
        'items': items,
        'total_produtos': len(items)
    }