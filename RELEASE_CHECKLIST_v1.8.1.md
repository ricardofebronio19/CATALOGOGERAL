# Checklist de Release - v1.8.1

## 📋 Pré-Release

### Verificações de Código
- [x] Versão atualizada em `version.json` (v1.8.1)
- [x] `update_config.json` atualizado com nova versão
- [x] Release notes criadas (`RELEASE_NOTES_v1.8.1.md`)
- [ ] Todos os arquivos commitados no Git
- [ ] Branch `1.8.1` criada e sincronizada

### Testes Manuais
- [ ] Testar página de detalhes do produto
  - [ ] Verificar alinhamento das colunas Ano e Motor
  - [ ] Testar tabela de similares
  - [ ] Verificar largura da coluna de imagem
- [ ] Testar página de resultados
  - [ ] Verificar largura da coluna de imagem
  - [ ] Testar ordenação
- [ ] Testar todos os formulários com botões atualizados:
  - [ ] Editar Peça
  - [ ] Editar Aplicação
  - [ ] Adicionar Peça
  - [ ] Adicionar Aplicação
  - [ ] Configurações (3 botões)
  - [ ] Tarefas (2 botões)
  - [ ] Gerenciar Usuários
  - [ ] Gerenciar Aplicações
- [ ] Testar modo desktop (run_gui.py)
- [ ] Testar modo navegador (run.py)

### Verificações Visuais
- [ ] Botões com estilo consistente (.button)
- [ ] Colunas de tabela alinhadas corretamente
- [ ] Imagens nas tabelas bem ajustadas (68px)
- [ ] Hover effects funcionando em todos os botões
- [ ] Tooltips de similares funcionando
- [ ] Responsividade mantida

## 🔨 Build

### Preparação
- [ ] Limpar diretórios de build anteriores
  ```powershell
  Remove-Item -Recurse -Force dist, build -ErrorAction SilentlyContinue
  ```
- [ ] Verificar que `.venv` está ativo
- [ ] Verificar dependências atualizadas

### Build Desktop (GUI)
- [ ] Executar `build_gui.bat`
- [ ] Verificar que `dist/CatalogoDePecas.exe` foi criado
- [ ] Testar executável localmente
- [ ] Verificar tamanho do executável (~25-30MB)

### Build Instalador
- [ ] Configurar variáveis de ambiente:
  ```powershell
  $env:CREATE_INSTALLER='1'
  $env:INCLUDE_DB='1'
  ```
- [ ] Executar build com Inno Setup
- [ ] Verificar `Output/CatalogoDePecas_Setup_v1.8.1.exe` criado
- [ ] Testar instalador em máquina limpa (opcional)

### Build Navegador (Opcional)
- [ ] Executar `build.bat` (se necessário versão navegador)
- [ ] Testar executável

## 📦 Empacotamento

### Arquivos para Release
- [ ] `instalador_CatalogoDePecas_v1.8.1.exe` (principal)
- [ ] `CatalogoDePecas.exe` (standalone - opcional)
- [ ] `RELEASE_NOTES_v1.8.1.md`
- [ ] Verificar tamanho total (~28MB)

### Checksums (Opcional)
- [ ] Gerar SHA256 do instalador
  ```powershell
  Get-FileHash Output/CatalogoDePecas_Setup_v1.8.1.exe -Algorithm SHA256
  ```
- [ ] Documentar checksum nas notas

## 🚀 Publicação

### GitHub
- [ ] Criar tag `v1.8.1`:
  ```bash
  git tag -a v1.8.1 -m "Release v1.8.1 - Melhorias visuais e UX"
  git push origin v1.8.1
  ```
- [ ] Criar release no GitHub
  - [ ] Tag: v1.8.1
  - [ ] Título: "Catálogo de Peças v1.8.1 - Melhorias Visuais"
  - [ ] Descrição: copiar de RELEASE_NOTES_v1.8.1.md
  - [ ] Anexar `instalador_CatalogoDePecas_v1.8.1.exe`
  - [ ] Marcar como "Latest release"

### Atualização do Repositório
- [ ] Fazer merge da branch 1.8.1 para main (se aplicável)
- [ ] Atualizar README.md com nova versão
- [ ] Verificar que `update_config.json` está no main

## ✅ Pós-Release

### Verificações
- [ ] Download do instalador funciona
- [ ] Link em `update_config.json` aponta corretamente
- [ ] Sistema de atualização automática detecta v1.8.1
- [ ] Testar atualização de v1.8.0 para v1.8.1

### Comunicação
- [ ] Notificar usuários sobre nova versão
- [ ] Documentar mudanças em changelog interno
- [ ] Atualizar documentação se necessário

### Monitoramento
- [ ] Verificar issues relacionadas a UI/UX
- [ ] Monitorar feedback sobre alinhamento de colunas
- [ ] Verificar se botões estão consistentes

## 📝 Notas

### Mudanças Principais
- Alinhamento de colunas Ano e Motor corrigido
- 10 botões padronizados com classe .button
- Largura de colunas de imagem otimizada (80px → 68px)
- CSS consolidado e organizado

### Compatibilidade
- ✅ 100% compatível com v1.8.0
- ✅ Sem mudanças no banco de dados
- ✅ Sem mudanças em funcionalidades
- ✅ Apenas melhorias visuais

### Riscos Identificados
- ⚠️ Baixo: CSS pode afetar layouts customizados
- ⚠️ Mínimo: Botões com estilos inline podem ter conflitos

## 🔄 Rollback Plan

Se necessário reverter:
1. Restaurar `version.json` para v1.8.0
2. Atualizar `update_config.json` para v1.8.0
3. Marcar release v1.8.0 como latest
4. Notificar usuários

---

**Responsável:** ricardofebronio19  
**Data:** 11 de novembro de 2025  
**Versão:** 1.8.1
