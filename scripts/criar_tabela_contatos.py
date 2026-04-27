#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para criar a tabela de contatos no banco de dados existente.
Execute este script após adicionar as novas funcionalidades de contato.
"""

import os
import sys

# Adiciona o diretório pai ao path para importar os módulos
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from models import Contato

def main():
    """Cria a tabela de contatos se ela não existir"""
    app = create_app()
    
    with app.app_context():
        print("Verificando se a tabela de contatos precisa ser criada...")
        
        try:
            # Tenta fazer uma consulta na tabela de contatos
            Contato.query.first()
            print("✅ Tabela de contatos já existe!")
        except Exception as e:
            print(f"📋 Tabela de contatos não encontrada. Criando...")
            
            try:
                # Cria a tabela
                db.create_all()
                print("✅ Tabela de contatos criada com sucesso!")
                
                # Verifica se a criação funcionou
                Contato.query.first()
                print("✅ Verificação da tabela concluída!")
                
            except Exception as create_error:
                print(f"❌ Erro ao criar a tabela de contatos: {create_error}")
                return False
    
    return True

if __name__ == "__main__":
    if main():
        print("🎉 Migração concluída com sucesso!")
    else:
        print("💥 Falha na migração!")
        sys.exit(1)