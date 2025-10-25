@echo off
if not exist build\package mkdir build\package
if not exist build\package\dist mkdir build\package\dist
copy /Y "dist\CatalogoDePecas.exe" "build\package\dist\"
if exist data\catalogo.db (
  if not exist build\package\data mkdir build\package\data
  copy /Y "data\catalogo.db" "build\package\data\"
)
if exist uploads (
  xcopy "uploads" "build\package\uploads" /E /I /Y
)
"C:\Progra~2\InnoSetup\ISCC.exe" /O"Output" /DMyAppVersion="1.7.2" /DMyExeName="CatalogoDePecas.exe" /DMyIconFile="E:\programa?ao\catalogo geral python\static\favicon.ico" "instalador.iss"
