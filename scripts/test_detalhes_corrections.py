"""
Script de Teste - Funcionalidades da Página de Detalhes
Executa validações automáticas das correções aplicadas
"""

import sys
import os
import re

def validar_template():
    """Valida se o template contém as correções necessárias"""
    print("🔍 Validando template detalhe_peca.html...")
    
    template_path = "templates/detalhe_peca.html"
    if not os.path.exists(template_path):
        print(f"❌ Arquivo {template_path} não encontrado!")
        return False
    
    with open(template_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    validacoes = [
        ("setupApplicationSearch", "Função de busca de aplicações"),
        ("setupInteractiveConversions", "Função de conversões interativas"),
        ("debugApplicationSearch", "Função de debug da busca"),
        ("debugConversions", "Função de debug das conversões"),
        ("filterApplications", "Função de filtro aprimorada"),
        ("searchTermNormalized", "Normalização de texto implementada"),
        ("conversion-brand", "Classe CSS para marcas"),
        ("conversion-code", "Classe CSS para códigos"),
    ]
    
    resultados = []
    for item, descricao in validacoes:
        if item in content:
            print(f"   ✅ {descricao}")
            resultados.append(True)
        else:
            print(f"   ❌ {descricao}")
            resultados.append(False)
    
    return all(resultados)

def validar_css():
    """Valida se o CSS contém os estilos necessários"""
    print("\n🎨 Validando arquivo style.css...")
    
    css_path = "static/style.css"
    if not os.path.exists(css_path):
        print(f"❌ Arquivo {css_path} não encontrado!")
        return False
    
    with open(css_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    validacoes = [
        (".conversion-brand", "Estilos para marcas"),
        (".conversion-code", "Estilos para códigos"),
        (".conversion-code:hover", "Efeito hover nos códigos"),
        (".conversion-code.copied", "Estilo para códigos copiados"),
        (".application-row.filtered-match", "Estilo para aplicações filtradas"),
        ("brand-label", "Estilo para label de marca"),
        ("code-label", "Estilo para label de código"),
    ]
    
    resultados = []
    for item, descricao in validacoes:
        if item in content:
            print(f"   ✅ {descricao}")
            resultados.append(True)
        else:
            print(f"   ❌ {descricao}")
            resultados.append(False)
    
    # Verifica se não há duplicações problemáticas
    conversion_brand_count = content.count('.conversion-brand {')
    conversion_code_count = content.count('.conversion-code {')
    
    if conversion_brand_count <= 1 and conversion_code_count <= 1:
        print(f"   ✅ Sem duplicação de estilos CSS")
        resultados.append(True)
    else:
        print(f"   ❌ Duplicação detectada: .conversion-brand({conversion_brand_count}), .conversion-code({conversion_code_count})")
        resultados.append(False)
    
    return all(resultados)

def gerar_relatorio():
    """Gera relatório de status das correções"""
    print("\n📊 RELATÓRIO DE VALIDAÇÃO")
    print("=" * 50)
    
    template_ok = validar_template()
    css_ok = validar_css()
    
    print(f"\n📄 Template HTML: {'✅ VÁLIDO' if template_ok else '❌ PROBLEMAS'}")
    print(f"🎨 Arquivo CSS: {'✅ VÁLIDO' if css_ok else '❌ PROBLEMAS'}")
    
    if template_ok and css_ok:
        print("\n🎉 TODAS AS CORREÇÕES FORAM APLICADAS COM SUCESSO!")
        print("\n📝 Próximos passos:")
        print("1. Reinicie o servidor Flask")
        print("2. Acesse uma página de detalhes de produto")
        print("3. Teste a filtragem de aplicações")
        print("4. Verifique a diferenciação nas conversões")
        print("5. Abra o console do navegador para funções de debug")
        
        return True
    else:
        print("\n⚠️ HÁ PROBLEMAS QUE PRECISAM SER CORRIGIDOS")
        return False

def instrucoes_teste():
    """Exibe instruções de teste manual"""
    print("\n🧪 INSTRUÇÕES DE TESTE MANUAL")
    print("=" * 50)
    print("""
    1. TESTE DE FILTRAGEM DE APLICAÇÕES:
       - Acesse um produto com várias aplicações
       - Digite no campo "Filtrar aplicações..."
       - Verifique se as aplicações são filtradas instantaneamente
       - Confirme se há destaque visual (fundo amarelo)
       - Pressione ESC para limpar o filtro
    
    2. TESTE DE CONVERSÕES:
       - Acesse um produto com conversões
       - Verifique se marcas aparecem em azul com ícone 🏭
       - Verifique se códigos aparecem em laranja com ícone 🔗
       - Clique em um código para testare se copia
       - Confirme animação verde temporária
    
    3. FUNÇÕES DE DEBUG (Console do navegador):
       - Abra o console (F12)
       - Digite: window.debugApplicationSearch()
       - Digite: window.debugConversions()
       - Analise os logs detalhados
    """)

if __name__ == "__main__":
    print("🛠️ VALIDADOR DE CORREÇÕES - PÁGINA DE DETALHES DO PRODUTO")
    print("=" * 60)
    
    if gerar_relatorio():
        instrucoes_teste()
        sys.exit(0)
    else:
        print("\n❌ VALIDAÇÃO FALHOU - Verifique os problemas acima")
        sys.exit(1)