from app import create_app
from utils.image_utils import vincular_imagens_por_codigo


if __name__ == "__main__":
    app = create_app()
    vincular_imagens_por_codigo(app)
