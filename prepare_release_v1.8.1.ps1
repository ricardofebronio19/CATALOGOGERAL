# Script de Build e Release - v1.8.1
# Execute este script para preparar a release

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Catálogo de Peças - Build v1.8.1" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Verificar ambiente
Write-Host "[1/6] Verificando ambiente..." -ForegroundColor Yellow
if (-not (Test-Path ".venv\Scripts\python.exe")) {
    Write-Host "ERRO: Virtual environment não encontrado!" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Virtual environment OK" -ForegroundColor Green

# 2. Limpar builds anteriores
Write-Host "`n[2/6] Limpando builds anteriores..." -ForegroundColor Yellow
Remove-Item -Recurse -Force dist, build -ErrorAction SilentlyContinue
Write-Host "✓ Diretórios limpos" -ForegroundColor Green

# 3. Verificar versão
Write-Host "`n[3/6] Verificando versão..." -ForegroundColor Yellow
$version = (Get-Content version.json | ConvertFrom-Json).version
if ($version -ne "v1.8.1") {
    Write-Host "ERRO: Versão em version.json não é v1.8.1!" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Versão: $version" -ForegroundColor Green

# 4. Build Desktop
Write-Host "`n[4/6] Iniciando build desktop (GUI)..." -ForegroundColor Yellow
Write-Host "Isso pode levar alguns minutos..." -ForegroundColor Gray
& .\build_gui.bat
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERRO: Build falhou!" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Build desktop concluído" -ForegroundColor Green

# 5. Verificar executável
Write-Host "`n[5/6] Verificando executável..." -ForegroundColor Yellow
if (-not (Test-Path "dist\CatalogoDePecas.exe")) {
    Write-Host "ERRO: Executável não encontrado!" -ForegroundColor Red
    exit 1
}
$size = (Get-Item "dist\CatalogoDePecas.exe").Length / 1MB
Write-Host "✓ Executável criado: $([math]::Round($size, 2)) MB" -ForegroundColor Green

# 6. Build Instalador (opcional)
Write-Host "`n[6/6] Deseja criar o instalador com Inno Setup? (S/N)" -ForegroundColor Yellow
$response = Read-Host
if ($response -eq "S" -or $response -eq "s") {
    Write-Host "Criando instalador..." -ForegroundColor Yellow
    $env:CREATE_INSTALLER = '1'
    $env:INCLUDE_DB = '1'
    $env:INNO_COMPILER = 'C:\Program Files (x86)\Inno Setup 6\ISCC.exe'
    
    if (Test-Path $env:INNO_COMPILER) {
        & .\build_gui.bat
        if (Test-Path "Output\CatalogoDePecas_Setup_v1.8.1.exe") {
            $installerSize = (Get-Item "Output\CatalogoDePecas_Setup_v1.8.1.exe").Length / 1MB
            Write-Host "✓ Instalador criado: $([math]::Round($installerSize, 2)) MB" -ForegroundColor Green
        } else {
            Write-Host "⚠ Instalador não encontrado" -ForegroundColor Yellow
        }
    } else {
        Write-Host "⚠ Inno Setup não encontrado em: $env:INNO_COMPILER" -ForegroundColor Yellow
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Build Concluído!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Próximos passos:" -ForegroundColor White
Write-Host "1. Testar o executável: .\dist\CatalogoDePecas.exe" -ForegroundColor Gray
Write-Host "2. Commitar mudanças: git add . && git commit -m 'Release v1.8.1'" -ForegroundColor Gray
Write-Host "3. Criar tag: git tag -a v1.8.1 -m 'Release v1.8.1'" -ForegroundColor Gray
Write-Host "4. Push: git push origin 1.8.1 && git push origin v1.8.1" -ForegroundColor Gray
Write-Host "5. Criar release no GitHub com o instalador" -ForegroundColor Gray
Write-Host ""

# Perguntar se deseja testar
Write-Host "Deseja executar o programa agora para testar? (S/N)" -ForegroundColor Yellow
$testResponse = Read-Host
if ($testResponse -eq "S" -or $testResponse -eq "s") {
    Write-Host "Iniciando aplicação..." -ForegroundColor Green
    & .\dist\CatalogoDePecas.exe
}
