# Release Notes - Versão 1.8.1

**Data de Lançamento:** 11 de novembro de 2025

## 🎨 Melhorias Visuais e Interface

### Correções de Alinhamento
- ✅ **Corrigido alinhamento das colunas Ano e Motor** na tela de detalhes do produto
  - Definidas larguras fixas para melhor organização (Ano: 15%, Motor: 20%)
  - Alinhamento centralizado para coluna Ano
  - Tabela de aplicações mais consistente e legível

### Padronização de Botões
- ✅ **Padronizados 10 botões de formulário** em toda aplicação com classe `.button`
  - "Salvar Alterações" (editar_peca.html e editar_aplicacao.html)
  - "Adicionar Peça" (adicionar_peca.html)
  - "Cadastrar Aplicação" (adicionar_aplicacao.html)
  - "Salvar Aparência", "Importar CSV", "Salvar Ícone" (configuracoes.html)
  - "Iniciar Importação", "Iniciar Vinculação" (tarefas.html)
  - "Adicionar Usuário" (gerenciar_usuarios.html)
  - "Adicionar Aplicação" (gerenciar_aplicacoes.html)
- 🎯 Visual consistente: cor laranja (#ff6600), texto branco, negrito
- ✨ Efeito hover padronizado em todos os botões

### Otimização de Tabelas
- ✅ **Ajustada largura da coluna de imagem** nas tabelas
  - Tabela de Resultados: coluna reduzida de 80px para 68px
  - Tabela de Similares: coluna reduzida de 80px para 68px
  - Padding otimizado (4px) para melhor aproveitamento de espaço
  - Imagens 60x60px agora se ajustam perfeitamente à coluna

### Reorganização de CSS
- ✅ **Consolidados estilos duplicados**
  - `.vertical-list` e tooltips movidos de template inline para CSS global
  - `.more-apps` centralizado em style.css
  - Melhor manutenibilidade e consistência
- ✅ **Removidos estilos inline** dos cabeçalhos de tabela
- ✅ **Larguras específicas** definidas para:
  - Tabela de Aplicações (4 colunas)
  - Tabela de Similares (7 colunas)
  - Tabela de Resultados (5 colunas)

## 📋 Arquivos Modificados

### Templates
- `templates/detalhe_peca.html` - Removidos estilos inline, consolidados no CSS
- `templates/resultados.html` - Adicionada classe `.results-table`
- `templates/editar_peca.html` - Botão padronizado
- `templates/editar_aplicacao.html` - Botão padronizado
- `templates/adicionar_peca.html` - Botão padronizado
- `templates/adicionar_aplicacao.html` - Botão padronizado
- `templates/configuracoes.html` - 3 botões padronizados
- `templates/tarefas.html` - 2 botões padronizados
- `templates/gerenciar_usuarios.html` - Botão padronizado
- `templates/gerenciar_aplicacoes.html` - Botão padronizado

### CSS
- `static/style.css` - Múltiplas melhorias:
  - Larguras de colunas definidas para todas as tabelas
  - Estilos `.vertical-list` e tooltips adicionados
  - Classe `.results-table` com larguras específicas
  - Melhor organização e documentação dos estilos

## 🔧 Detalhes Técnicos

### Larguras de Colunas Implementadas

#### Tabela de Aplicações (detalhe_peca.html)
- Veículo: 35%
- Ano: 15% (centralizado)
- Motor: 20%
- Configuração: 30%

#### Tabela de Similares
- Imagem: 68px (4px padding)
- Nome: 20%
- Código: 12%
- Veículo: 18%
- Ano: 12% (centralizado)
- Motor: 15%
- Ações: 120px (centralizado)

#### Tabela de Resultados
- Imagem: 68px (4px padding, centralizado)
- Código: 12%
- Nome: auto (espaço restante)
- Fornecedor: 15%
- Aplicações: 25%

## 📊 Impacto

- ✅ **Consistência visual** em 100% dos botões de formulário
- ✅ **Melhor legibilidade** nas tabelas de produtos e aplicações
- ✅ **Aproveitamento de espaço** otimizado em ~15% nas colunas de imagem
- ✅ **Manutenibilidade** melhorada com CSS centralizado
- ✅ **UX aprimorada** com alinhamento correto de dados

## 🚀 Instalação

### Windows (Instalador)
Baixe e execute: `instalador_CatalogoDePecas_v1.8.1.exe`

### Atualização Automática
Se você já tem a versão 1.8.0 instalada, será notificado automaticamente sobre a atualização.

## 📝 Notas

- Esta é uma versão focada em **melhorias visuais e UX**
- Nenhuma alteração em funcionalidades ou banco de dados
- 100% compatível com versões anteriores
- Recomendado para todos os usuários da v1.8.0

## 🐛 Correções

- Desalinhamento de colunas Ano e Motor (relatado por usuário)
- Botões inconsistentes em formulários
- Colunas de imagem ocupando espaço excessivo

---

**Desenvolvedor:** ricardofebronio19  
**Repositório:** [CATALOGOGERAL](https://github.com/ricardofebronio19/CATALOGOGERAL)  
**Branch:** 1.8.1
