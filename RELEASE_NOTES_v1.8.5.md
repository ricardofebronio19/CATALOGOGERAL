# 📦 Catálogo de Peças v1.8.5

**Data de Lançamento:** 18 de novembro de 2025  
**Versão:** 1.8.5  
**Branch:** 1.8.0

---

## ✨ Novos Recursos

### Sistema de Medidas Estruturadas
- **8 Campos Específicos de Medidas:**
  - Largura (mm)
  - Altura (mm)
  - Comprimento (mm)
  - Diâmetro Externo (mm)
  - Diâmetro Interno (mm)
  - Elo (mm)
  - Estrias Internas (quantidade)
  - Estrias Externas (quantidade)
  - Campo adicional para medidas extras

### Busca Avançada por Medidas
- **Seção Expansível na Busca:**
  - Botão "Busca Avançada por Medidas" com ícone animado
  - Expansão/colapso suave com animação
  - Auto-expansão quando há parâmetros de medidas na URL
  - Grid responsivo com 8 campos de filtro
  - Dica informativa sobre o uso dos filtros

### Melhorias Visuais
- **Seção de Observações Destacada:**
  - Título "⚠️ OBSERVAÇÕES" em vermelho
  - Background vermelho claro (#fff5f5)
  - Borda esquerda grossa (8px) em vermelho
  - Sombra com tom avermelhado
  - Texto em vermelho escuro para máxima visibilidade

- **Menu Lateral Otimizado:**
  - Altura máxima de 600px com scroll automático
  - Scrollbar estilizada em laranja
  - Layout flexbox para melhor responsividade
  - Título fixo no topo, lista rolável

---

## 🔧 Funcionalidades Técnicas

### Processamento de Medidas
- **Formatação Automática:**
  - Campos de dimensão recebem "mm" automaticamente
  - Estrias não recebem unidade (são contagens)
  - Parsing bidirecional entre formulário e banco de dados
  - Compatibilidade com medidas antigas (texto livre)

### Sistema de Busca
- **Filtros Combinados:**
  - Busca por qualquer combinação de campos de medidas
  - Suporte a acentos (DIÂMETRO/DIAMETRO)
  - Operador AND lógico entre filtros
  - Persistência de valores na URL para paginação

### Interface de Formulários
- **Organização Lógica:**
  - Grid de 3 colunas responsivo
  - Placeholders informativos
  - Labels com unidades explícitas
  - Validação em tempo real

---

## 🎯 Melhorias de Usabilidade

1. **Entrada de Dados Padronizada:**
   - Campos estruturados substituem textarea de texto livre
   - Reduz erros de digitação e inconsistências
   - Facilita busca e comparação de produtos

2. **Busca Mais Precisa:**
   - Filtros específicos por cada dimensão
   - Possibilidade de combinar múltiplos critérios
   - Resultados mais relevantes

3. **Visual Aprimorado:**
   - Observações chamam atenção imediatamente
   - Menu lateral não ocupa espaço excessivo
   - Animações suaves para melhor experiência

---

## 📊 Detalhes de Implementação

### Arquivos Modificados
- `templates/adicionar_peca.html` - Campos estruturados de medidas
- `templates/editar_peca.html` - Campos estruturados de medidas
- `templates/detalhe_peca.html` - Destaque em observações
- `templates/partials/_search_form.html` - Busca avançada expansível
- `core_utils.py` - Funções de processamento e parsing de medidas
- `routes.py` - Captura e processamento de novos parâmetros
- `static/style.css` - Estilos para medidas, observações e sidebar

### Novas Funções
- `_processar_medidas_estruturadas()` - Converte campos em string formatada
- `_parsear_medidas_para_dict()` - Converte string em dicionário de campos
- `_build_search_query()` - Atualizada com 8 novos parâmetros de busca

---

## 🔄 Compatibilidade

### Retrocompatibilidade
✅ Produtos com medidas antigas (texto livre) funcionam normalmente  
✅ Sistema detecta e parseia formato antigo automaticamente  
✅ Busca funciona para ambos os formatos  

### Requisitos
- Python 3.12.9
- Flask + SQLAlchemy
- Waitress (servidor)
- Navegador moderno (Chrome, Firefox, Edge)

---

## 📦 Instalação

### Windows (Instalador)
1. Baixe `instalador_CatalogoDePecas_v1.8.5.exe`
2. Execute o instalador
3. Siga as instruções na tela
4. O aplicativo será instalado em `%LOCALAPPDATA%\CatalogoDePecas`

### Atualização Automática
Se você tem a versão 1.8.3 ou superior instalada:
1. Abra o aplicativo
2. Um banner verde aparecerá notificando a nova versão
3. Clique em "Baixar e Instalar"
4. O aplicativo será atualizado automaticamente

---

## 🐛 Correções Conhecidas

Nenhum bug conhecido nesta versão. Todas as funcionalidades foram testadas.

---

## 📝 Notas de Migração

### Para Desenvolvedores
- A função `_build_search_query()` agora aceita 8 parâmetros adicionais
- Formulários de produtos devem incluir os 8 campos de medidas
- CSS contém novos estilos para `.observacoes-section` e `.sidebar`

### Para Usuários
- Produtos antigos continuam funcionando normalmente
- Ao editar um produto antigo, as medidas serão parseadas automaticamente
- Novos produtos devem usar os campos estruturados

---

## 🚀 Próximos Passos (v1.9.0)

Planejado para futuras versões:
- [ ] Busca por range de valores (ex: largura entre 50-60mm)
- [ ] Filtros de medidas na página de resultados
- [ ] Comparação visual de medidas entre produtos
- [ ] Importação CSV com campos estruturados
- [ ] Exportação de medidas em formato padronizado

---

## 👥 Créditos

**Desenvolvedor:** ricardofebronio19  
**Repositório:** [CATALOGOGERAL](https://github.com/ricardofebronio19/CATALOGOGERAL)  
**Licença:** MIT

---

## 📞 Suporte

Em caso de dúvidas ou problemas:
1. Verifique a documentação no repositório
2. Abra uma issue no GitHub
3. Entre em contato com o desenvolvedor

---

**Versão estável e testada. Recomendada para todos os usuários!** ✅
