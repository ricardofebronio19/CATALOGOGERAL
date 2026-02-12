# Comandos Git para Release v1.8.6

**Data**: 9 de dezembro de 2025  
**Branch atual**: 1.8.0  
**Tipo de release**: Patch (correções de interface)

---

## 📋 CHECKLIST PRÉ-RELEASE

- [x] Versão atualizada em `version.json` → v1.8.6
- [x] Versão atualizada em `update_config.json` → 1.8.6
- [x] Versão atualizada em `instalador.iss` → 1.8.6
- [x] Release notes criadas: `RELEASE_NOTES_v1.8.6.md`
- [x] Correções implementadas:
  - [x] Botão copiar código (detalhe_peca.html)
  - [x] Ícone de informação (detalhe_peca.html)
  - [x] CSS .btn-copy-code (style.css)
  - [x] UTF-8 config (app.py)

---

## 🔧 PASSO 1: Adicionar arquivos modificados

```powershell
# Arquivos de versão
git add version.json
git add update_config.json
git add instalador.iss

# Documentação da release
git add RELEASE_NOTES_v1.8.6.md
git add GIT_COMMANDS_v1.8.6.md

# Código modificado
git add templates/detalhe_peca.html
git add static/style.css
git add app.py

# Verificar status
git status
```

---

## 💾 PASSO 2: Commit das alterações

```powershell
git commit -m "Release v1.8.6 - Correções de Interface e UTF-8

🔧 Correções:
- Botão copiar código: SVG quebrado → texto '📋 Copiar'
- Ícone de informação: SVG quebrado → emoji ℹ️
- Preservação UTF-8 com JSON_AS_ASCII = False

✨ Melhorias visuais:
- Estilização .btn-copy-code com gradiente e hover
- Efeitos de elevação e transições suaves
- Maior visibilidade dos controles de ação

📦 Mantém 100% das funcionalidades v1.8.5"
```

---

## 🚀 PASSO 3: Push para o repositório

```powershell
# Push do branch 1.8.0
git push origin 1.8.0

# Criar tag anotada
git tag -a v1.8.6 -m "Release v1.8.6 - Correções de Interface e UTF-8

Correções:
- Botão copiar código mais visível
- Ícone de informação corrigido
- Preservação de caracteres UTF-8 (Ç, acentos)

Melhorias visuais:
- Gradiente laranja no botão copiar
- Efeitos hover com elevação
- Transições suaves"

# Push da tag
git push origin v1.8.6

# Verificar tags remotas
git ls-remote --tags origin
```

---

## 🏗️ PASSO 4: Build do executável e instalador

### Opção 1: Build completo com instalador (Recomendado)

```powershell
# Executar build com todas as flags
$env:CREATE_INSTALLER='1'
$env:INCLUDE_DB='1'
.\build.bat
```

**Saídas esperadas:**
- `dist\CatalogoDePecas.exe` (executável standalone ~28 MB)
- `Output\instalador_CatalogoDePecas_v1.8.6.exe` (instalador Inno Setup)

### Opção 2: Via VS Code Task

1. Abra Command Palette (Ctrl+Shift+P)
2. Execute: `Tasks: Run Task`
3. Selecione: `Build + Staging + Installer (Inno)`

---

## 📦 PASSO 5: Criar release no GitHub

### Via interface web:

1. Acesse: https://github.com/ricardofebronio19/CATALOGOGERAL/releases/new?tag=v1.8.6

2. Preencha:
   - **Tag**: `v1.8.6` (selecione da lista)
   - **Release title**: `v1.8.6 - Correções de Interface e UTF-8`
   - **Description**: Copie de `RELEASE_NOTES_v1.8.6.md` (seções principais)

3. Upload do instalador:
   - Arraste `Output\instalador_CatalogoDePecas_v1.8.6.exe` para a área de anexos
   - Aguarde upload completo (~28 MB)

4. Marque:
   - [ ] "Set as a pre-release" (deixe desmarcado)
   - [ ] "Set as the latest release" (marque esta opção)

5. Clique em **"Publish release"**

### Via PowerShell (alternativa):

```powershell
# Usando GitHub CLI (se instalado)
gh release create v1.8.6 `
  --title "v1.8.6 - Correções de Interface e UTF-8" `
  --notes-file RELEASE_NOTES_v1.8.6.md `
  Output\instalador_CatalogoDePecas_v1.8.6.exe
```

---

## 🔄 PASSO 6: Atualizar branch main com novo update_config.json

```powershell
# Fazer checkout do main
git checkout main

# Atualizar do remoto
git pull origin main

# Copiar o update_config.json atualizado do branch 1.8.0
git checkout 1.8.0 -- update_config.json

# Commit e push
git add update_config.json
git commit -m "Update config: v1.8.6 disponível"
git push origin main

# Voltar para branch 1.8.0
git checkout 1.8.0
```

---

## ✅ PASSO 7: Verificação pós-release

### Verificar URLs e downloads:

```powershell
# Testar URL do instalador
Start-Process "https://github.com/ricardofebronio19/CATALOGOGERAL/releases/download/v1.8.6/instalador_CatalogoDePecas_v1.8.6.exe"

# Verificar update_config.json no main
Start-Process "https://raw.githubusercontent.com/ricardofebronio19/CATALOGOGERAL/main/update_config.json"
```

### Testar atualização automática:

1. Instale uma versão anterior (v1.8.5)
2. Aguarde 6 horas ou force checagem reiniciando
3. Verifique se notificação de v1.8.6 aparece
4. Teste o download e instalação automática

---

## 📊 RESUMO DOS COMANDOS (sequência completa)

```powershell
# 1. Adicionar e commitar
git add version.json update_config.json instalador.iss
git add RELEASE_NOTES_v1.8.6.md GIT_COMMANDS_v1.8.6.md
git add templates/detalhe_peca.html static/style.css app.py
git commit -m "Release v1.8.6 - Correções de Interface e UTF-8"

# 2. Push e tag
git push origin 1.8.0
git tag -a v1.8.6 -m "Release v1.8.6"
git push origin v1.8.6

# 3. Build
$env:CREATE_INSTALLER='1'; $env:INCLUDE_DB='1'; .\build.bat

# 4. Criar release no GitHub (via web)
# → Fazer upload de Output\instalador_CatalogoDePecas_v1.8.6.exe

# 5. Atualizar main
git checkout main
git pull origin main
git checkout 1.8.0 -- update_config.json
git add update_config.json
git commit -m "Update config: v1.8.6 disponível"
git push origin main
git checkout 1.8.0
```

---

## 🐛 TROUBLESHOOTING

### Erro: "tag already exists"
```powershell
# Deletar tag local e remota
git tag -d v1.8.6
git push origin :refs/tags/v1.8.6
# Recriar tag
git tag -a v1.8.6 -m "Release v1.8.6"
git push origin v1.8.6
```

### Erro: "build.bat not found"
```powershell
# Verificar se está no diretório correto
Get-Location
# Deve mostrar: e:\programaçao\CGI
```

### Erro: "ISCC.exe not found"
```powershell
# Verificar instalação do Inno Setup
Test-Path "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
# Se false, instalar Inno Setup 6.5.3 ou superior
```

### Upload do instalador lento
- Tamanho normal: ~28 MB
- Tempo estimado: 2-5 minutos (depende da conexão)
- Aguarde até ver "Uploaded successfully"

---

## 📝 NOTAS IMPORTANTES

- ⚠️ **Sempre faça backup** do banco de dados antes de releases
- ✅ **Teste localmente** o executável antes de publicar
- 🔍 **Verifique a tag** no GitHub após push
- 📦 **Confirme o hash** do instalador se possível
- 🔄 **Update config no main** é crítico para atualizações automáticas

---

**Versão deste guia**: 1.0  
**Última atualização**: 9 de dezembro de 2025
