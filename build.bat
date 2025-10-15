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
:: Configuração: por padrão não criamos instalador via Inno Setup.
:: Para habilitar, execute: set CREATE_INSTALLER=1 && build.bat
set "CREATE_INSTALLER=%CREATE_INSTALLER%"
set "SKIP_INNO=1"
set "INNO_COMPILER="
if "%CREATE_INSTALLER%"=="1" (
    :: Se o usuário pediu instalador, usamos o local padrão; ajuste manualmente se necessário.
    set "INNO_COMPILER=C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
    if exist "%INNO_COMPILER%" (
        set "SKIP_INNO=0"
    ) else (
        echo [AVISO] Inno Setup nao encontrado em '%INNO_COMPILER%'. Instalador sera pulado.
        set "SKIP_INNO=1"
    )
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

:: Verificação de erro do PyInstaller
:: 3. Localiza o launcher Python disponível (py, python, python3) e executa PyInstaller

echo [2/4] Empacotando a aplicacao com PyInstaller (modo --onefile)...

:: Detecta o Python a ser usado: preferimos .venv se existir, caso contrario usamos 'python' do PATH
set "PY_CMD=python"
if exist ".venv\Scripts\python.exe" (
    set "PY_CMD=.venv\Scripts\python.exe"
)

echo [INFO] Usando launcher Python: %PY_CMD%

:: Verifica/instala PyInstaller se necessario
%PY_CMD% -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo.
    echo [AVISO] PyInstaller nao encontrado no ambiente selecionado. Tentando instalar via pip...
    %PY_CMD% -m pip install pyinstaller
    if errorlevel 1 (
        echo [ERRO] Falha ao instalar PyInstaller. Instale manualmente e tente novamente.
        goto:end
    )
)

:: Se solicitado, copiaremos o DB local para data/catalogo.db e adicionaremos aos dados do PyInstaller
set "INCLUDE_DB=%INCLUDE_DB%"
set "PY_INSTALLER_ADDDATA=templates;templates;static;static"
if "%INCLUDE_DB%"=="1" (
    echo [INFO] INCLUDE_DB=1 detectado. Tentando copiar o banco local para 'data/catalogo.db'...
    "%PY_CMD%" scripts\copy_db.py || (
        echo [AVISO] Falha ao copiar o DB. Continuando sem incluir o DB.
    )
    if exist "data\catalogo.db" (
        echo [INFO] Banco presente em data\catalogo.db. Iremos incluir no empacotamento.
        set "PY_INSTALLER_ADDDATA=%PY_INSTALLER_ADDDATA%;data;data"
    ) else (
        echo [AVISO] Banco nao encontrado em data\catalogo.db apos tentativa de copia.
    )
)

:: Chamamos PyInstaller usando call para preservar corretamente os argumentos e evitar parsing inesperado em shells.
call "%PY_CMD%" -m PyInstaller --noconfirm --onefile --windowed --name "CatalogoDePecas" --icon="%ICON_FILE%" --add-data "templates;templates" --add-data "static;static" %ENTRY_SCRIPT%

:: Verificação de erro do PyInstaller
if errorlevel 1 (
    echo.
    echo [ERRO] O PyInstaller falhou. O script sera encerrado.
    goto:end
)
echo      PyInstaller concluiu com sucesso. O executavel esta em 'dist'.
echo.

:: 4. Executando o Inno Setup (pode ser pulado se Inno nao estiver instalado)
echo [3/4] Criando o instalador com Inno Setup...

if "%SKIP_INNO%"=="1" (
    echo [AVISO] Etapa do Inno Setup pulada. O executavel foi gerado em 'dist' mas o instalador nao sera criado.
) else (
    :: Verifica se o compilador do Inno Setup existe
    if not exist "%INNO_COMPILER%" (
        echo.
        echo [ERRO] Compilador do Inno Setup nao encontrado em "%INNO_COMPILER%".
        echo [ERRO] Verifique o caminho no script 'build.bat' e tente novamente.
        goto:end
    )

    :: Compila o script .iss, passando as variáveis dinamicamente via /D
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
)

echo.
echo [4/4] SUCESSO! Processo de build concluido.
if "%SKIP_INNO%"=="1" (
    echo       O executavel foi gerado na pasta 'dist'. (Instalador Inno Setup foi pulado)
) else (
    echo       O instalador foi gerado na pasta 'Output'.
)

:end
popd
pause