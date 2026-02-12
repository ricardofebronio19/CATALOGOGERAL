# Release Notes - v1.8.6

**Data de lançamento**: 9 de dezembro de 2025  
**Tipo de release**: Patch (correções de interface)

---

## 🔧 CORREÇÕES

### Interface de Usuário
- **Botão de copiar código**: Substituído ícone SVG quebrado por texto "📋 Copiar" mais visível
- **Ícone de informação**: Corrigido ícone quebrado na seção de aplicações (substituído por emoji ℹ️)
- **Caracteres UTF-8**: Garantida preservação de caracteres especiais (Ç, acentos) em todos os campos através de `JSON_AS_ASCII = False`

---

## ✨ MELHORIAS VISUAIS

### Estilização de Botões
- **Gradiente laranja**: Botão de copiar com gradiente da cor principal
- **Efeitos hover**: Elevação visual ao passar o mouse (translateY + shadow)
- **Transições suaves**: Animações de 0.3s para melhor feedback
- **Sombra colorida**: Consistência visual com a paleta do sistema

### Confiabilidade de Ícones
- **Emojis nativos**: Uso de emojis Unicode (📋, ℹ️) eliminando dependência de arquivos SVG
- **Melhor compatibilidade**: Funcionam em todos os sistemas sem arquivos externos

---

## 🔍 DETALHES TÉCNICOS

### Arquivos Modificados
- `templates/detalhe_peca.html` (linhas 17-25, 87-89):
  - Botão de copiar: `<img src="copy-icon.svg">` → `📋 Copiar`
  - Ícone info: `<img src="info-icon.svg">` → `ℹ️`
  
- `static/style.css` (nova classe `.btn-copy-code`):
  ```css
  .btn-copy-code {
      background: linear-gradient(135deg, var(--cor-principal), #ff8533);
      color: white;
      border: none;
      padding: 6px 12px;
      border-radius: 4px;
      cursor: pointer;
      font-size: 0.9em;
      font-weight: 600;
      transition: all 0.3s ease;
  }
  ```

- `app.py` (linha 169):
  ```python
  app.config["JSON_AS_ASCII"] = False  # Preserva caracteres UTF-8
  ```

---

## 📦 MANTÉM TODAS AS FUNCIONALIDADES

Esta versão mantém **100% das funcionalidades** da v1.8.5:

✅ Sistema de medidas estruturadas (8 campos específicos)  
✅ Busca avançada por medidas com seção expansível  
✅ Destaque vermelho na seção de Observações  
✅ Menu lateral de montadoras com scroll customizado  
✅ Sistema de atualização automática  
✅ Backup/Restore completo  
✅ Gestão de produtos similares  

---

## 🚀 INSTALAÇÃO

### Atualização Automática
Usuários da v1.8.5 ou anterior receberão notificação automática de atualização.

### Instalação Manual
1. Baixe `instalador_CatalogoDePecas_v1.8.6.exe`
2. Execute o instalador
3. Siga as instruções na tela

### Migração de Dados
- ✅ Dados preservados automaticamente
- ✅ Configurações mantidas
- ✅ Imagens de produtos mantidas

---

## 🐛 PROBLEMAS CONHECIDOS

Nenhum problema conhecido nesta versão.

---

## 📝 NOTAS DE DESENVOLVIMENTO

### Motivação
Esta release corrige dois problemas de UX identificados em produção:
1. Ícones SVG quebrados (dependência de arquivos externos)
2. Falta de feedback visual nos botões de ação

### Abordagem
- **Minimalista**: Substituição de SVG por emojis Unicode
- **CSS moderno**: Gradientes e transições suaves
- **UTF-8 nativo**: Configuração Flask para preservar caracteres especiais

### Compatibilidade
- ✅ Windows 10/11
- ✅ Python 3.12.9
- ✅ Navegadores modernos (Chrome, Edge, Firefox)

---

## 🔗 LINKS ÚTEIS

- **Repositório**: https://github.com/ricardofebronio19/CATALOGOGERAL
- **Issues**: https://github.com/ricardofebronio19/CATALOGOGERAL/issues
- **Documentação completa**: Ver `README.md` no repositório

---

## 👥 CRÉDITOS

Desenvolvido por: **ricardofebronio19**  
Versão: **1.8.6**  
Branch: **1.8.0**
