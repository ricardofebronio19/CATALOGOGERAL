# Release Notes - Versão 2.1.3

**Data**: 21 de maio de 2026  
**Versão**: 2.1.3  
**Status**: Pronto para produção

---

## 📋 Resumo das Mudanças

A versão 2.1.3 traz melhorias significativas na **ordenação de produtos similares** e **personalização de cores** da seção de conversões, proporcionando mais flexibilidade e controle visual ao usuário.

---

## ✨ Novidades

### 1. Ordenação de Produtos Similares
- **Cabeçalhos Clicáveis**: Os títulos das colunas **Nome**, **Código** e **Veículo** na tabela de similares agora são clicáveis
- **Alternância de Ordem**: Primeiro clique ordena crescente (A-Z), segundo clique ordena decrescente (Z-A)
- **Indicadores Visuais**:
  - `↕` - Coluna ordenável (padrão)
  - `▲` - Ordem crescente ativa
  - `▼` - Ordem decrescente ativa
- **Compatibilidade**: Funcionamento integrado com filtros existentes por clique em aplicação

### 2. Configuração de Cores de Conversões
- **Cor do Fabricante**: Customize a cor do texto do nome do fabricante (padrão: azul `#0066cc`)
- **Cor do Código**: Customize a cor do texto do código de produto (padrão: laranja `#c05000`)
- **Localização**: Novos controles na aba **Configurações → Aparência**
- **Prévia em Tempo Real**: Visualize as cores antes de salvar

### 3. Restauração de Padrões
- Botão **"Restaurar Cores Padrão"** agora restaura também as novas cores de conversões

---

## 🛠️ Melhorias Técnicas

- **Responsividade Aprimorada**: Tabela de similares mantém usabilidade em todos os tamanhos de tela
- **Armazenamento**: Preferências de cor persistem no `config.json`
- **Acessibilidade**: Cabeçalhos têm título descritivo e cursor `pointer` para indicar interatividade
- **Performance**: Ordenação utiliza `localeCompare` para comparação correta com acentos (pt-BR)

---

## 📝 Detalhes Técnicos

### Arquivos Modificados
- `version.json` - Atualizado para 2.1.3
- `CHANGELOG.md` - Adicionado novo entry
- `templates/detalhe_peca.html` - Implementação de ordenação de similares + variáveis CSS
- `templates/configuracoes.html` - Novos campos de cor + prévia visual
- `routes.py` - Persistência de cores no backend
- `app.py` - Defaults para cores novas
- `static/style.css` - Aplicação de variáveis de cor

### Variáveis de Configuração Novas
```json
{
  "cor_texto_conversao_fabricante": "#0066cc",
  "cor_texto_conversao_codigo": "#c05000"
}
```

---

## ✅ Testes Recomendados

1. **Ordenação de Similares**:
   - Acessar página de detalhe de um produto com similares
   - Clicar nos cabeçalhos Nome, Código, Veículo
   - Verificar alternância de crescente/decrescente
   - Verificar indicadores visuais

2. **Configuração de Cores**:
   - Acessar Configurações → Aparência
   - Alterar cores de Fabricante e Código
   - Visualizar mudança em tempo real na prévia
   - Salvar e verificar aplicação na página de detalhes

3. **Compatibilidade**:
   - Clicar em uma aplicação e verificar se ordenação continua funcionando após filtro
   - Restaurar cores padrão e verificar reposição

---

## 📦 Instalação

### Atualização do Executável
- Baixar `instalador_CatalogoDePecas_v2.1.3.exe` da aba Releases
- Executar instalador normalmente

### Atualização Manual (Desenvolvimento)
```bash
git pull origin main
git tag v2.1.3
# Ou fazer build: python -m PyInstaller CatalogoDePecas.spec
```

---

## 🔄 Migração de Versões Anteriores

Usuários da versão 2.1.2 serão automaticamente atualizados. As cores padrão serão aplicadas:
- Fabricante: Azul (`#0066cc`)
- Código: Laranja (`#c05000`)

---

## 📞 Suporte

Para relatar bugs ou sugerir melhorias, abra uma **Issue** no repositório GitHub:  
https://github.com/ricardofebronio19/CATALOGOGERAL/issues

---

**Desenvolvido com ❤️ por Ricardo Febronio**
