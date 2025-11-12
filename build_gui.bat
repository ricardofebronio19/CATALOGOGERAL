@echo off
setlocal

:: =================================================================================
:: Script de Build para Versão GUI (pywebview) do Catálogo de Peças
:: =================================================================================

set APP_NAME=CatalogoDePecas
if "%APP_VERSION%"=="" (
    for /f "usebackq delims=" %%i in (`git describe --tags --abbrev^=0 2^>nul`) do set APP_VERSION=%%i
)
if "%APP_VERSION%"=="" (
    set APP_VERSION=1.8.0
)
set ENTRY_SCRIPT=run_gui.py
set ICON_FILE=static\favicon.ico
set INNO_SCRIPT=instalador_gui.iss

echo.
echo [BUILD GUI] Iniciando build da versao desktop (pywebview)...
echo [BUILD GUI] Versao: %APP_VERSION%
echo.

pushd "%~dp0"

:: Detecta Python
set "PY_CMD=python"
if exist ".venv\Scripts\python.exe" (
    set "PY_CMD=.venv\Scripts\python.exe"
)

echo [INFO] Usando Python: %PY_CMD%

:: Instala pywebview se necessário
echo [1/4] Verificando dependencias...
"%PY_CMD%" -m pip show pywebview >nul 2>&1
if errorlevel 1 (
    echo [INFO] Instalando pywebview...
    "%PY_CMD%" -m pip install pywebview
)

:: Limpeza
echo [2/4] Limpando builds anteriores...
if exist "build" rmdir /s /q "build"
if exist "dist" rmdir /s /q "dist"
if exist "Output" rmdir /s /q "Output"
if exist "run_gui.spec" del "run_gui.spec"

:: Gera version.json
echo {"version":"%APP_VERSION%"} > version.json

:: Build com PyInstaller
echo [3/4] Empacotando com PyInstaller (modo GUI)...

set "PY_INSTALLER_ADDDATA=templates;templates;static;static;version.json;."

:: Opcionalmente inclui DB
set "INCLUDE_DB=%INCLUDE_DB%"
if "%INCLUDE_DB%"=="1" (
    echo [INFO] INCLUDE_DB=1 detectado. Copiando banco de dados...
    "%PY_CMD%" scripts\copy_db.py
    if exist "data\catalogo.db" (
        set "PY_INSTALLER_ADDDATA=%PY_INSTALLER_ADDDATA%;data;data"
    )
)

:: Chama PyInstaller com configurações otimizadas para GUI
call "%PY_CMD%" -m PyInstaller --noconfirm ^
    --onefile ^
    --windowed ^
    --name "CatalogoDePecas" ^
    --icon="%ICON_FILE%" ^
    --add-data "templates;templates" ^
    --add-data "static;static" ^
    --add-data "version.json;." ^
    --hidden-import=webview ^
    --hidden-import=waitress ^
    --hidden-import=flask ^
    --collect-all=webview ^
    %ENTRY_SCRIPT%

if errorlevel 1 (
    echo.
    echo [ERRO] PyInstaller falhou!
    goto:end
)

echo [4/4] Build concluído com sucesso!
echo.
echo Executavel gerado: dist\CatalogoDePecas.exe
echo.
echo Para testar: .\dist\CatalogoDePecas.exe
echo.

:end
popd
pause
