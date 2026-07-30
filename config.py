import os


class BaseConfig:
    """Configurações base lidas via variáveis de ambiente."""
    # Segurança
    SECRET_KEY = os.getenv("SECRET_KEY")

    # SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JSON responses in UTF-8
    JSON_AS_ASCII = os.getenv("JSON_AS_ASCII", "False").lower() not in ("false", "0", "no")

    # Uploads
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", 16 * 1024 * 1024))


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class ProductionConfig(BaseConfig):
    DEBUG = False
