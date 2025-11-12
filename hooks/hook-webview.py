# Hook para PyInstaller - webview
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

# Coletar todos os submódulos
hiddenimports = collect_submodules('webview')

# Coletar arquivos de dados
datas = collect_data_files('webview', include_py_files=True)
