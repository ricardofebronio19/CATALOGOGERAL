from app import create_app
from utils.image_utils import vincular_imagens_por_codigo


# Função mantida para compatibilidade - redireciona para a versão consolidada
def vincular_imagens_por_codigo_legacy(app):
    """Função legacy - redireciona para a versão consolidada em utils/image_utils.py"""
    return vincular_imagens_por_codigo(app)


if __name__ == "__main__":
    app = create_app()
    print("⚠️  AVISO: Este script foi consolidado.")
    print("   Função movida para: utils/image_utils.py")
    print("   Use: python run.py link-images")
    print("\n🔄 Executando a função consolidada...")
    vincular_imagens_por_codigo(app)
