# Comandos Git para Release v1.8.1

## 📝 Preparação

### 1. Verificar status atual
```bash
git status
git diff
```

### 2. Adicionar todos os arquivos modificados
```bash
git add .
```

### 3. Verificar o que será commitado
```bash
git status
```

## 💾 Commit

### Commit das mudanças
```bash
git commit -m "Release v1.8.1 - Melhorias visuais e UX

- Corrigido alinhamento das colunas Ano e Motor
- Padronizados 10 botões em 8 templates
- Otimizada largura das colunas de imagem (80px → 68px)
- Consolidados estilos CSS (vertical-list, tooltips)
- Melhorias em UX e consistência visual

Arquivos modificados:
- version.json: v1.7.4 → v1.8.1
- update_config.json: atualizado release notes
- static/style.css: múltiplas melhorias de layout
- 10 templates: botões padronizados
- Documentação: 3 novos arquivos MD"
```

## 🏷️ Tag

### Criar tag anotada
```bash
git tag -a v1.8.1 -m "Release v1.8.1 - Melhorias visuais

- Alinhamento de colunas corrigido
- Botões padronizados (10 arquivos)
- Largura de imagens otimizada
- CSS consolidado e organizado"
```

### Verificar tag criada
```bash
git tag -l v1.8.1
git show v1.8.1
```

## 🚀 Push

### Push da branch
```bash
git push origin 1.8.1
```

### Push da tag
```bash
git push origin v1.8.1
```

### Ou push de tudo de uma vez
```bash
git push origin 1.8.1 --tags
```

## 📦 GitHub Release

### Via Interface Web
1. Ir para: https://github.com/ricardofebronio19/CATALOGOGERAL/releases/new
2. Selecionar tag: `v1.8.1`
3. Título: `Catálogo de Peças v1.8.1 - Melhorias Visuais e UX`
4. Descrição: Copiar conteúdo de `RELEASE_NOTES_v1.8.1.md`
5. Anexar arquivo: `Output/CatalogoDePecas_Setup_v1.8.1.exe`
6. Marcar como "Latest release"
7. Publicar

### Via GitHub CLI (gh)
```bash
gh release create v1.8.1 \
  --title "Catálogo de Peças v1.8.1 - Melhorias Visuais e UX" \
  --notes-file RELEASE_NOTES_v1.8.1.md \
  Output/CatalogoDePecas_Setup_v1.8.1.exe
```

## 🔄 Merge para Main (Opcional)

Se quiser fazer merge da branch 1.8.1 para main:

```bash
git checkout main
git merge 1.8.1
git push origin main
```

## ✅ Verificações Pós-Push

### Verificar no GitHub
```bash
# Abrir página de releases
start https://github.com/ricardofebronio19/CATALOGOGERAL/releases

# Abrir página de tags
start https://github.com/ricardofebronio19/CATALOGOGERAL/tags

# Verificar update_config.json no main
start https://github.com/ricardofebronio19/CATALOGOGERAL/blob/main/update_config.json
```

### Testar download do instalador
```bash
# URL do instalador (atualizar após criar release)
start https://github.com/ricardofebronio19/CATALOGOGERAL/releases/download/v1.8.1/instalador_CatalogoDePecas_v1.8.1.exe
```

## 📊 Estatísticas

### Ver arquivos modificados
```bash
git diff --stat v1.8.0..v1.8.1
```

### Ver todas as mudanças
```bash
git log v1.8.0..v1.8.1 --oneline
```

### Contar linhas modificadas
```bash
git diff v1.8.0..v1.8.1 --shortstat
```

## 🔙 Rollback (Se Necessário)

### Deletar tag local
```bash
git tag -d v1.8.1
```

### Deletar tag remota
```bash
git push origin :refs/tags/v1.8.1
```

### Reverter commit
```bash
git revert HEAD
git push origin 1.8.1
```

## 📝 Exemplo Completo

```bash
# 1. Verificar mudanças
git status
git diff

# 2. Adicionar tudo
git add .

# 3. Commit
git commit -m "Release v1.8.1 - Melhorias visuais e UX"

# 4. Tag
git tag -a v1.8.1 -m "Release v1.8.1"

# 5. Push
git push origin 1.8.1
git push origin v1.8.1

# 6. Criar release no GitHub (interface web)

# 7. Verificar
git log --oneline -5
git tag -l
```

---

**Branch:** 1.8.1  
**Tag:** v1.8.1  
**Repositório:** ricardofebronio19/CATALOGOGERAL
