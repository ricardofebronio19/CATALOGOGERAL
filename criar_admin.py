#!/usr/bin/env python3
"""
Script para criar usuário admin temporário para teste.
"""

import sys
import os

# Adiciona o diretório atual ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, APP_DATA_PATH
from models import User, db
import logging
import secrets
import string

app = create_app()

with app.app_context():
    # Verifica se já existe um usuário admin
    admin = User.query.filter_by(username='admin').first()
    
    if admin:
        print("Usuário admin já existe")
    else:
        # Cria usuário admin com senha temporária gerada
        alphabet = string.ascii_letters + string.digits
        random_password = "".join(secrets.choice(alphabet) for _ in range(12))

        admin = User(username='admin', is_admin=True)
        admin.set_password(random_password)

        db.session.add(admin)
        db.session.commit()

        logging.basicConfig(level=logging.INFO)
        logging.info("Usuário admin criado com sucesso!")
        logging.info("Username: admin")
        # Grava a senha temporária em arquivo seguro dentro de APP_DATA_PATH
        try:
            os.makedirs(APP_DATA_PATH, exist_ok=True)
            password_file = os.path.join(APP_DATA_PATH, "initial_admin_password.txt")
            with open(password_file, "w", encoding="utf-8") as pf:
                pf.write(random_password)
            try:
                os.chmod(password_file, 0o600)
            except Exception:
                pass
            logging.warning(f"Senha temporária gravada em: {password_file}")
        except Exception:
            logging.warning("Usuário criado, mas falha ao gravar senha. Altere a senha manualmente.")