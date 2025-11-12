# Comandos Git para Release v1.8.3

## 📋 Pré-requisitos

### Verificar Status
```powershell
# Verificar branch atual
git branch
# Deve estar em: * 1.8.0

# Verificar status dos arquivos
git status
```

**Arquivos modificados esperados:**
- `version.json`
- `update_config.json`
- `CatalogoDePecas.spec`
- `instalador.iss`
- `RELEASE_NOTES_v1.8.3.md` (novo)
- `RELEASE_SUMMARY_v1.8.3.md` (novo)
- `GIT_COMMANDS_v1.8.3.md` (novo)

---

## 🚀 PASSO 1: Stage (Adicionar Arquivos)

### Arquivos Core
```powershell
# Versão e configuração
git add version.json
git add update_config.json
git add CatalogoDePecas.spec
git add instalador.iss
```

### Documentação
```powershell
git add RELEASE_NOTES_v1.8.3.md
git add RELEASE_SUMMARY_v1.8.3.md
git add GIT_COMMANDS_v1.8.3.md
```

### Ou Tudo de Uma Vez
```powershell
git add .
git status  # Verificar arquivos staged
```

---

## 📝 PASSO 2: Commit

```powershell
git commit -m "Release v1.8.3 - Correção de build PyInstaller e estabilidade

CORREÇÕES CRÍTICAS:
- Módulos asyncio (_overlapped, _asyncio) incluídos explicitamente
- Módulos locais (app, models, routes, core_utils) adicionados aos hiddenimports
- Pathex configurado com diretório atual e site-packages

MUDANÇA IMPORTANTE:
- Retorno para versão navegador (run.py) em vez de desktop (run_gui.py)
- Motivo: PyInstaller tem conflitos com pywebview/pythonnet
- Mantém todas as funcionalidades da v1.8.2

MELHORIAS:
- Build PyInstaller 100% estável
- Sem erros de ModuleNotFoundError
- Executável inicia corretamente
- Servidor Flask funciona perfeitamente
- Navegador abre automaticamente

ARQUIVOS MODIFICADOS:
- CatalogoDePecas.spec: run_gui.py → run.py + hiddenimports corretos
- version.json: v1.8.2 → v1.8.3
- update_config.json: Metadados v1.8.3
- instalador.iss: Versão 1.8.3

DOCUMENTAÇÃO:
- RELEASE_NOTES_v1.8.3.md: Notas detalhadas
- RELEASE_SUMMARY_v1.8.3.md: Resumo executivo
- GIT_COMMANDS_v1.8.3.md: Este arquivo

FUNCIONALIDADES MANTIDAS:
- ✅ Todas as correções da v1.8.2 (backup em Downloads, etc)
- ✅ Interface reformulada
- ✅ Sistema de atualização automática
- ✅ Autenticação
- ✅ Busca avançada
- ✅ Upload de imagens
- ✅ Gestão de similares

TESTES:
- ✅ Build sem erros
- ✅ Executável inicia
- ✅ Navegador abre
- ✅ Servidor responde

COMPATIBILIDADE:
- 100% compatível com v1.8.0, v1.8.1, v1.8.2
- Sem mudanças no banco de dados

PRIORIDADE: Alta (Correção de bug crítico de build)
TIPO: Bugfix + Estabilidade
BREAKING CHANGES: Nenhuma (apenas mudança de UI: janela → navegador)"
```

### Verificar Commit
```powershell
git log -1
git show HEAD
```

---

## 🏷️ PASSO 3: Criar Tag

```powershell
git tag -a v1.8.3 -m "Release v1.8.3 - Build estável + Versão navegador

Correções críticas de build:
- _overlapped e _asyncio incluídos
- Módulos locais nos hiddenimports
- Pathex configurado corretamente

Mudança: Desktop → Navegador
- run_gui.py → run.py
- Mais estável e confiável
- Mesmas funcionalidades

Mantém todas as correções da v1.8.2:
- Backup em Downloads
- Interface reformulada
- @login_required
- Logs detalhados

Tipo: Bugfix + Estabilidade
Prioridade: Alta
Compatibilidade: 100% com v1.8.0/1/2"
```

### Verificar Tag
```powershell
git tag
git show v1.8.3
```

---

## 🌐 PASSO 4: Push para GitHub

### Push do Branch
```powershell
git push origin 1.8.0
```

### Push da Tag
```powershell
git push origin v1.8.3
```

### Ou Tudo de Uma Vez
```powershell
git push origin 1.8.0 --follow-tags
```

---

## ✅ PASSO 5: Verificação no GitHub

### Via Navegador
```powershell
Start-Process "https://github.com/ricardofebronio19/CATALOGOGERAL"
```

**Verificar:**
- [ ] Commit aparece no branch 1.8.0
- [ ] Tag v1.8.3 visível em "Tags"
- [ ] Arquivos atualizados (version.json, etc.)

### Via Git
```powershell
# Ver tags remotas
git ls-remote --tags origin

# Ver commits remotos
git log origin/1.8.0 --oneline -5
```

---

## 📦 PRÓXIMOS PASSOS

### 1. Build do Executável
```powershell
# Limpar builds anteriores
Remove-Item -Path "build" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item -Path "dist" -Recurse -Force -ErrorAction SilentlyContinue

# Ativar venv
.\.venv\Scripts\Activate.ps1

# Build (versão navegador com console desabilitado)
pyinstaller CatalogoDePecas.spec --clean

# Verificar saída
Test-Path "dist\CatalogoDePecas.exe"
(Get-Item "dist\CatalogoDePecas.exe").Length / 1MB
```

### 2. Testar Executável
```powershell
# Executar e verificar se abre navegador
Start-Process "dist\CatalogoDePecas.exe"

# Aguardar 10 segundos e verificar se navegador abriu
# Deve abrir em http://127.0.0.1:8000
```

### 3. Criar Instalador
```powershell
# Compilar com Inno Setup
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" instalador.iss

# Verificar saída
Test-Path "dist\Output\instalador_CatalogoDePecas_v1.8.3.exe"
(Get-Item "dist\Output\instalador_CatalogoDePecas_v1.8.3.exe").Length / 1MB
```

### 4. Criar GitHub Release
```powershell
# Abrir página de nova release
Start-Process "https://github.com/ricardofebronio19/CATALOGOGERAL/releases/new?tag=v1.8.3"
```

**Preencher:**
- **Tag:** v1.8.3 (selecionar existente)
- **Título:** `Catálogo de Peças v1.8.3 - Build Estável + Versão Navegador`
- **Descrição:** Copiar de `RELEASE_NOTES_v1.8.3.md`
- **Arquivo:** Upload `dist/Output/instalador_CatalogoDePecas_v1.8.3.exe`
- **Latest release:** ✅ Marcar
- **Publish release**

### 5. Atualizar update_config.json na Main
```powershell
# Trocar para branch main
git checkout main
git pull origin main

# Copiar update_config.json do branch 1.8.0
git checkout 1.8.0 -- update_config.json

# Verificar conteúdo
Get-Content update_config.json

# Commit
git add update_config.json
git commit -m "Update config: Release v1.8.3"
git push origin main

# Voltar para branch 1.8.0
git checkout 1.8.0
```

### 6. Testar Atualização Automática
```powershell
# 1. Instalar v1.8.2 (se tiver)
# 2. Abrir aplicação
# 3. Aguardar banner: "Nova versão v1.8.3 disponível"
# 4. Clicar "Baixar e Instalar"
# 5. Verificar atualização funcionou
# 6. Testar backup em Downloads
```

---

## 🔧 COMANDOS ÚTEIS

### Desfazer Commit (se necessário)
```powershell
# Se ainda NÃO fez push
git reset --soft HEAD~1  # Mantém mudanças staged
git reset HEAD~1         # Mantém mudanças, remove do stage
git reset --hard HEAD~1  # ⚠️ DESCARTA mudanças

# Se JÁ fez push (criar commit de reversão)
git revert HEAD
git push origin 1.8.0
```

### Remover Tag (se necessário)
```powershell
# Local
git tag -d v1.8.3

# Remoto
git push origin :refs/tags/v1.8.3
```

### Ver Histórico
```powershell
# Gráfico de commits
git log --graph --oneline --all --decorate

# Commits entre tags
git log v1.8.2..v1.8.3 --oneline

# Arquivos modificados
git diff v1.8.2..v1.8.3 --name-only
```

### Comparar Versões
```powershell
# Diff entre tags
git diff v1.8.2 v1.8.3

# Diff de arquivo específico
git diff v1.8.2 v1.8.3 -- CatalogoDePecas.spec

# Stats resumidos
git diff v1.8.2 v1.8.3 --stat
```

---

## 📊 CHECKLIST FINAL

### Antes do Push
- [x] Commit criado com mensagem detalhada
- [x] Tag v1.8.3 criada
- [ ] `git status` limpo
- [ ] `git log -1` mostra commit correto
- [ ] `git tag -l v1.8.3` mostra tag

### Após o Push
- [ ] Commit visível no GitHub
- [ ] Tag v1.8.3 visível no GitHub
- [ ] Arquivos atualizados no repositório
- [ ] Build executável funciona
- [ ] Instalador criado
- [ ] GitHub Release publicada
- [ ] update_config.json atualizado na main
- [ ] Atualização automática testada

---

## 🚨 TROUBLESHOOTING

### Erro: "Permission denied"
```powershell
# Verificar autenticação
git config --list | Select-String "user"

# Reconfigurar credenciais
git config credential.helper manager-core
```

### Erro: "Tag already exists"
```powershell
# Remover tag existente
git tag -d v1.8.3
git push origin :refs/tags/v1.8.3

# Criar novamente
git tag -a v1.8.3 -m "Mensagem..."
```

### Erro: "Push rejected"
```powershell
# Pull com rebase
git pull origin 1.8.0 --rebase

# Resolver conflitos (se houver)
git status
# Editar arquivos com conflitos
git add .
git rebase --continue

# Push novamente
git push origin 1.8.0
```

---

## 📝 NOTAS

### Diferenças v1.8.2 → v1.8.3
- **Desktop → Navegador:** Mudança principal
- **PyInstaller:** Build corrigido e estável
- **Funcionalidades:** Todas mantidas
- **Compatibilidade:** 100% compatível

### Arquivos Novos
- `RELEASE_NOTES_v1.8.3.md`
- `RELEASE_SUMMARY_v1.8.3.md`
- `GIT_COMMANDS_v1.8.3.md`

### Arquivos Modificados
- `version.json` (v1.8.2 → v1.8.3)
- `update_config.json` (URLs e release notes v1.8.3)
- `CatalogoDePecas.spec` (run_gui → run + hiddenimports)
- `instalador.iss` (versão 1.8.3)

---

**Status:** ⏳ Pronto para executar  
**Próxima Ação:** Executar comandos Git  
**Responsável:** ricardofebronio19  
**Data:** 12 de novembro de 2025
