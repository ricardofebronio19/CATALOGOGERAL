@echo off
setlocal

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
set ICON_FILE=static\favicon.ico
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
    echo [AVISO] Tentando caminho padrao "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    set "INNO_COMPILER=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
)

echo.
echo [BUILD] Iniciando o processo de build para %APP_NAME% v%APP_VERSION%...
echo.

:: 1. Navega para o diretório do script para garantir caminhos relativos corretos
pushd "%~dp0"

:: 2. Limpeza de builds anteriores
echo [1/4] Limpando diretorios antigos (build, dist, Output)...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "Output" rmdir /s /q "Output"
if exist "run.spec" del "run.spec"
echo      Limpeza concluida.
echo.

:: 3. Executando o PyInstaller no modo --onedir (pasta única)
:: Este modo é mais simples e cria um único executável, facilitando a distribuição.
echo [2/4] Empacotando a aplicacao com PyInstaller (modo --onefile)...
py -m PyInstaller --noconfirm --onefile --windowed --name "CatalogoDePecas" --icon="%ICON_FILE%" --add-data "templates;templates" --add-data "static;static" --hidden-import "waitress" %ENTRY_SCRIPT%

:: Verificação de erro do PyInstaller
if errorlevel 1 (
    echo.
    echo [ERRO] O PyInstaller falhou. O script sera encerrado.
    goto:end
)
echo      PyInstaller concluiu com sucesso. O executavel esta em 'dist'.
echo.

:: 4. Executando o Inno Setup
echo [3/4] Criando o instalador com Inno Setup...

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
"%INNO_COMPILER%" /O"Output" /DMyAppVersion="%APP_VERSION%" /DMyExeName="CatalogoDePecas.exe" /DMyIconFile="%~dp0%ICON_FILE%" "%INNO_SCRIPT%"

:: Verificação de erro do Inno Setup
if errorlevel 1 (
    echo.
    echo [ERRO] O Inno Setup falhou. O script sera encerrado.
    goto:end
)
echo      Inno Setup concluiu com sucesso.
echo.

echo.
echo [4/4] SUCESSO! Processo de build concluido.
echo       O instalador foi gerado na pasta 'Output'.

:end
popd
pause