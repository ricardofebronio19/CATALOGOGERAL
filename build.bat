@echo off
setlocal
setlocal enabledelayedexpansion

:: =================================================================================
:: Script de Build Automatizado para o Catálogo de Peças
:: =================================================================================
:: Requisitos:
:: 1. Python e pip instalados e no PATH.
:: 2. PyInstaller instalado (`pip install pyinstaller`).
:: 3. Inno Setup 6 instalado (https://jrsoftware.org/isinfo.php).
:: =================================================================================

:: --- Configurações do Projeto ---
set APP_NAME=CatalogoDePecas
set APP_VERSION=1.5
set ENTRY_SCRIPT=run.py
set ICON_FILE=static/favicon.ico
set INNO_SCRIPT=instalador.iss

:: --- Detecção Automática do Compilador Inno Setup ---
set "INNO_COMPILER="
:: Tenta encontrar o Inno Setup no registro do Windows (local padrão)
for /f "tokens=2*" %%a in ('reg query "HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall\Inno Setup 6_is1" /v "InstallLocation" 2^>nul') do (
    set "INNO_PATH=%%b"
)
if defined INNO_PATH (
    set "INNO_COMPILER=%INNO_PATH%\ISCC.exe"
) else (
    echo [AVISO] Nao foi possivel encontrar o Inno Setup automaticamente.
    set "INNO_COMPILER=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    echo [AVISO] Tentando caminho padrao "%INNO_COMPILER%"
)

echo.
echo [BUILD] Iniciando o processo de build para %APP_NAME% v%APP_VERSION%... 
echo.

:: 1. Navega para o diretório do script para garantir caminhos relativos corretos
pushd "%~dp0"

:: 2. Limpeza de builds anteriores
echo [1/5] Limpando diretorios antigos: build, dist, Output...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "Output" rmdir /s /q "Output"
if exist "%APP_NAME%.spec" del "%APP_NAME%.spec"
echo      Limpeza concluida.
echo.
 
:: 3. Garante que as dependências estão instaladas no ambiente virtual
echo [2/5] Verificando e instalando dependencias do requirements.txt...
if not exist ".venv\Scripts\pip.exe" (
    echo [ERRO] Ambiente virtual (.venv) nao encontrado. Execute o setup inicial.
    goto:end
)
.venv\Scripts\pip.exe install -r requirements.txt

:: Verificação de erro do pip
if errorlevel 1 (
    echo.
    echo [ERRO] A instalacao de dependencias (pip install) falhou. O script sera encerrado.
    goto:end
)

:: 4. Executando o PyInstaller a partir do ambiente virtual para garantir o contexto correto
echo [3/5] Empacotando a aplicacao com PyInstaller (isso pode levar alguns minutos)...
.venv\Scripts\pyinstaller.exe ^
    --noconfirm ^
    --windowed ^
    --name "%APP_NAME%" ^
    --icon="%ICON_FILE%" ^
    --add-data "templates;templates" ^
    --add-data "static;static" ^
    --hidden-import "waitress" ^
    --hidden-import "packaging" ^
    --hidden-import "psycopg2" ^
    --hidden-import "urllib.parse" ^
    %ENTRY_SCRIPT%

:: Verificação de erro do PyInstaller
if errorlevel 1 (
    echo.
    echo [ERRO] O PyInstaller falhou. O script sera encerrado.
    goto:end
)
echo      PyInstaller concluiu com sucesso. O executavel esta em 'dist'.
echo.

:: 5. Executando o Inno Setup
echo [4/5] Criando o instalador com Inno Setup...

:: Verifica se o compilador do Inno Setup existe
if not exist "%INNO_COMPILER%" (
    echo.
    echo [ERRO] Compilador do Inno Setup nao encontrado em "%INNO_COMPILER%".
    echo [ERRO] Verifique o caminho no script 'build.bat' e tente novamente.
    goto:end
)

:: Compila o script .iss, passando as variáveis dinamicamente via /D
:: Isso evita ter que editar o arquivo .iss a cada mudança de versão ou nome.
if not exist "Output" mkdir "Output"
"!INNO_COMPILER!" /O"Output" /DMyAppVersion="%APP_VERSION%" /DMyExeName="CatalogoDePecas.exe" /DMyIconFile="%~dp0%ICON_FILE%" "%INNO_SCRIPT%"

:: Verificação de erro do Inno Setup
if errorlevel 1 (
    echo.
    echo [ERRO] O Inno Setup falhou. O script sera encerrado.
    goto:end
)
echo      Inno Setup concluiu com sucesso.
echo.

:: 6. Limpeza final (opcional)
echo [5/5] Limpando arquivos temporarios do build...
if exist "build" rmdir /s /q "build"
if exist "%APP_NAME%.spec" del "%APP_NAME%.spec"
echo      Limpeza final concluida.
echo.

echo.
echo SUCESSO! Processo de build concluido.
echo       O instalador foi gerado na pasta 'Output'.

:end
echo.
popd
pause