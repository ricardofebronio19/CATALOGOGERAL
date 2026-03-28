#!/usr/bin/env powershell
# Script para preparar release v2.0.2

param(
    [switch]$BuildOnly,
    [switch]$CreateRelease,
    [switch]$SkipBuild
)

Write-Host "=== Preparando Release v2.0.2 ===" -ForegroundColor Green

# 1. Verificar se estamos no diretório correto
if (!(Test-Path "build.bat")) {
    Write-Error "Execute este script no diretório raiz do projeto!"
    exit 1
}

# 2. Limpar builds anteriores
if (Test-Path "dist") {
    Write-Host "Limpando builds anteriores..." -ForegroundColor Yellow
    Remove-Item -Path "dist" -Recurse -Force
}

if (Test-Path "Output") {
    Write-Host "Limpando instaladores anteriores..." -ForegroundColor Yellow
    Remove-Item -Path "Output" -Recurse -Force
}

# 3. Build da aplicação
if (!$SkipBuild) {
    Write-Host "Iniciando build da aplicação..." -ForegroundColor Cyan
    $env:CREATE_INSTALLER = '1'
    $env:INCLUDE_DB = '1'
    $env:INNO_COMPILER = 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe'
    
    & .\build.bat
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Falha no build! Verifique os erros acima."
        exit 1
    }
    
    Write-Host "Build concluído com sucesso!" -ForegroundColor Green
}

if ($BuildOnly) {
    Write-Host "Build concluído. Use -CreateRelease para criar o release no GitHub." -ForegroundColor Yellow
    exit 0
}

# 4. Verificar se o instalador foi criado
$installerPath = "Output\instalador_CatalogoDePecas_v2.0.2.exe"
if (!(Test-Path $installerPath)) {
    Write-Error "Instalador não encontrado em: $installerPath"
    exit 1
}

Write-Host "Instalador criado: $installerPath" -ForegroundColor Green

# 5. Preparar informações do release
$tagName = "v2.0.2"
$releaseName = "CatalogoDePecas v2.0.2"
$releaseNotes = @"
# 🚀 Catálogo de Peças v2.0.2

## Melhorias desta Versão

### 🔧 Correções e Melhorias
- Correções de bugs menores identificados na versão anterior
- Melhorias na estabilidade geral do sistema
- Otimizações de performance para consultas no banco de dados
- Atualização de dependências para versões mais seguras
- Refinamentos na interface de usuário

### 🛠️ Manutenção
- Limpeza de código e refatoração de componentes internos
- Melhoria no tratamento de erros e logs
- Atualização da documentação interna

## 📦 Instalação

### Nova Instalação
1. Baixe o instalador abaixo
2. Execute como administrador
3. Siga as instruções do instalador

### Atualização Automática
- Usuários de versões anteriores serão notificados automaticamente
- Clique em "Baixar e Instalar" quando a notificação aparecer

## 📋 Arquivos de Release

- **instalador_CatalogoDePecas_v2.0.2.exe** - Instalador completo (~35MB)

---
**Compatibilidade:** Windows 10/11
**Data:** 20/10/2025
"@

# 6. Criar release no GitHub (se solicitado)
if ($CreateRelease) {
    Write-Host "Criando release no GitHub..." -ForegroundColor Cyan
    
    if (!(Get-Command gh -ErrorAction SilentlyContinue)) {
        Write-Error "GitHub CLI (gh) não está instalado. Instale em: https://cli.github.com/"
        Write-Host "Alternativamente, crie o release manualmente em: https://github.com/ricardofebronio19/CATALOGOGERAL/releases/new" -ForegroundColor Yellow
        Write-Host "Tag: $tagName" -ForegroundColor White
        Write-Host "Título: $releaseName" -ForegroundColor White
        Write-Host "Arquivo: $installerPath" -ForegroundColor White
        exit 1
    }
    
    try {
        # Criar release
        gh release create $tagName $installerPath --title $releaseName --notes $releaseNotes --repo "ricardofebronio19/CATALOGOGERAL"
        
        Write-Host "Release criado com sucesso!" -ForegroundColor Green
        Write-Host "URL: https://github.com/ricardofebronio19/CATALOGOGERAL/releases/tag/$tagName" -ForegroundColor Cyan
        
        # Atualizar update_config.json no repositório
        Write-Host "Atualizando configuração de atualização..." -ForegroundColor Yellow
        
        $updateConfig = @{
            latest_version = "1.7.2"
            download_url = "https://github.com/ricardofebronio19/CATALOGOGERAL/releases/download/v1.7.2/instalador_CatalogoDePecas_v1.7.2.exe"
            release_notes = "🚀 Sistema de Atualização Automática`n✨ Interface visual melhorada`n🎨 Destaque das montadoras e alternância de cores`n🔧 Correções de bugs e melhorias de performance"
            size_mb = "35"
        } | ConvertTo-Json -Depth 10
        
        $updateConfig | Out-File -FilePath "update_config.json" -Encoding UTF8
        
        Write-Host "Configuração de atualização preparada em: update_config.json" -ForegroundColor Green
        Write-Host "Lembre-se de fazer commit e push deste arquivo para ativar as atualizações automáticas!" -ForegroundColor Yellow
        
    } catch {
        Write-Error "Erro ao criar release: $_"
        Write-Host "Crie o release manualmente em: https://github.com/ricardofebronio19/CATALOGOGERAL/releases/new" -ForegroundColor Yellow
        exit 1
    }
}

Write-Host "`n=== Preparação Concluída ===" -ForegroundColor Green
Write-Host "Instalador: $installerPath" -ForegroundColor White
Write-Host "Notas de release: RELEASE_NOTES_v1.7.2.md" -ForegroundColor White
Write-Host "Config de atualização: update_config.json" -ForegroundColor White

if (!$CreateRelease) {
    Write-Host "`nPara criar o release no GitHub, execute:" -ForegroundColor Yellow
    Write-Host ".\prepare_release.ps1 -CreateRelease" -ForegroundColor White
}