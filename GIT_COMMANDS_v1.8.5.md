# Comandos Git para Release v1.8.5

## 1. Verificar Status
```bash
git status
```

## 2. Adicionar Arquivos Modificados
```bash
git add version.json
git add update_config.json
git add instalador.iss
git add RELEASE_NOTES_v1.8.5.md
git add templates/adicionar_peca.html
git add templates/editar_peca.html
git add templates/detalhe_peca.html
git add templates/partials/_search_form.html
git add core_utils.py
git add routes.py
git add static/style.css
```

## 3. Commit das Alterações
```bash
git commit -m "Release v1.8.5 - Sistema de Medidas Estruturadas

✨ Novos Recursos:
- Sistema completo de medidas estruturadas (8 campos)
- Busca avançada por medidas com seção expansível
- Campos: Largura, Altura, Comprimento, Diâmetros, Elo, Estrias
- Destaque vermelho na seção de Observações
- Menu lateral com scroll otimizado

🔧 Funcionalidades:
- Formatação automática de medidas (mm para dimensões)
- Parsing bidirecional entre formulário e banco
- Filtros combinados na busca
- Compatibilidade com medidas antigas

🎨 Interface:
- Grid responsivo de 3 colunas
- Animações suaves na busca avançada
- Scrollbar estilizada no menu lateral
- Observações com destaque visual vermelho

📦 Arquivos:
- 8 campos estruturados em adicionar/editar
- Novas funções de processamento em core_utils
- Query de busca expandida com 8 parâmetros
- CSS otimizado para sidebar e medidas"
```

## 4. Push para o Repositório
```bash
git push origin 1.8.0
```

## 5. Criar Tag da Versão
```bash
git tag -a v1.8.5 -m "Release v1.8.5 - Sistema de Medidas Estruturadas e Busca Avançada

Principais mudanças:
- Sistema completo de medidas estruturadas (8 campos específicos)
- Busca avançada por medidas com interface expansível
- Destaque visual em observações importantes
- Menu lateral otimizado com scroll
- Processamento automático de unidades (mm)
- Filtros combinados na busca
- Compatibilidade total com versões anteriores"
```

## 6. Push da Tag
```bash
git push origin v1.8.5
```

## 7. Verificar Tags Remotas
```bash
git ls-remote --tags origin
```

## 8. Build do Executável (PowerShell)
```powershell
# Limpar builds anteriores
Remove-Item -Recurse -Force dist, build -ErrorAction SilentlyContinue

# Build com PyInstaller
pyinstaller CatalogoDePecas.spec --clean

# Verificar tamanho
(Get-Item "dist\CatalogoDePecas.exe").Length / 1MB
```

## 9. Build do Instalador (PowerShell)
```powershell
# Executar Inno Setup Compiler
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" instalador.iss

# Verificar instalador gerado
Get-Item "dist\Output\instalador_CatalogoDePecas_v1.8.5.exe"
```

## 10. Criar Release no GitHub
```
1. Acesse: https://github.com/ricardofebronio19/CATALOGOGERAL/releases/new
2. Escolha a tag: v1.8.5
3. Título: "Catálogo de Peças v1.8.5 - Sistema de Medidas Estruturadas"
4. Descrição: Copie o conteúdo de RELEASE_NOTES_v1.8.5.md
5. Anexe: dist\Output\instalador_CatalogoDePecas_v1.8.5.exe
6. Marque: "Set as the latest release"
7. Publique: Click "Publish release"
```

## 11. Atualizar update_config.json na Branch Main
```bash
# Checkout para main
git checkout main

# Pull das últimas alterações
git pull origin main

# Copiar apenas o update_config.json da branch 1.8.0
git checkout 1.8.0 -- update_config.json

# Adicionar e commitar
git add update_config.json
git commit -m "Update config: Release v1.8.5"

# Push para main
git push origin main

# Voltar para a branch de desenvolvimento
git checkout 1.8.0
```

## Resumo das Mudanças v1.8.5

### Arquivos Novos
- `RELEASE_NOTES_v1.8.5.md` - Documentação completa da release

### Arquivos Modificados
- `version.json` - v1.8.3 → v1.8.5
- `update_config.json` - Atualizado com notas da v1.8.5
- `instalador.iss` - Versão padrão 1.8.4 → 1.8.5
- `templates/adicionar_peca.html` - 8 campos estruturados de medidas
- `templates/editar_peca.html` - 8 campos estruturados de medidas
- `templates/detalhe_peca.html` - Destaque vermelho em observações
- `templates/partials/_search_form.html` - Busca avançada expansível
- `core_utils.py` - Funções de processamento e parsing de medidas
- `routes.py` - 8 novos parâmetros de busca
- `static/style.css` - Estilos para observações, medidas e sidebar

### Funcionalidades Adicionadas
1. Sistema de medidas estruturadas (8 campos)
2. Busca avançada por medidas com UI expansível
3. Formatação automática de unidades (mm)
4. Parsing bidirecional de medidas
5. Destaque visual vermelho em observações
6. Menu lateral com scroll otimizado
7. Filtros combinados na busca

### Tecnologias
- Python 3.12.9
- Flask + SQLAlchemy
- PyInstaller 6.16.0
- Inno Setup 6.5.3
- HTML5 + CSS3 + JavaScript

---

**Pronto para deployment! 🚀**
