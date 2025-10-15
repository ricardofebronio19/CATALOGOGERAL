from waitress import serve
from app import app, inicializar_banco, APP_DATA_PATH, UPLOAD_FOLDER, carregar_config_aparencia
import os
import zipfile
import shutil
import webbrowser
import argparse
import sys
import threading

def perform_restore_from_backup():
    """Verifica e executa a restauração a partir de um arquivo de backup pendente."""
    backup_file = os.path.join(APP_DATA_PATH, "backup_para_restaurar.zip")
    if not os.path.exists(backup_file):
        # Limpa qualquer arquivo de gatilho de reinício que possa ter sobrado
        restart_trigger_file = os.path.join(APP_DATA_PATH, 'RESTART_REQUIRED')
        if os.path.exists(restart_trigger_file):
            os.remove(restart_trigger_file)
        return # Nenhum backup para restaurar

    print("Backup pendente encontrado. Iniciando processo de restauração...")

    # Lista de arquivos do banco de dados a serem removidos
    db_files_to_remove = [
        os.path.join(APP_DATA_PATH, "catalogo.db"),
        os.path.join(APP_DATA_PATH, "catalogo.db-shm"),
        os.path.join(APP_DATA_PATH, "catalogo.db-wal")
    ]
    for f_path in db_files_to_remove:
        if os.path.exists(f_path):
            os.remove(f_path)
            print(f"Arquivo de banco de dados antigo removido: {os.path.basename(f_path)}")

    # Extrai o backup
    with zipfile.ZipFile(backup_file, 'r') as zip_ref:
        zip_ref.extractall(APP_DATA_PATH)
    
    os.remove(backup_file) # Remove o arquivo de backup após a restauração
    print("Restauração do backup concluída com sucesso!")

def perform_update():
    """Verifica se um pacote de atualização existe e o instala."""
    update_package = os.path.join(APP_DATA_PATH, "update_package.zip")
    if not os.path.exists(update_package):
        return # Nenhuma atualização para instalar

    print("Pacote de atualização encontrado. Iniciando processo...")

    # O diretório de instalação é o diretório onde o executável está rodando
    install_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
    
    try:
        # Extrai o conteúdo do zip para o diretório de instalação, sobrescrevendo os arquivos antigos
        with zipfile.ZipFile(update_package, 'r') as zip_ref:
            zip_ref.extractall(install_dir)
        
        os.remove(update_package) # Remove o pacote de atualização após a extração
        print("Atualização aplicada com sucesso!")

    except Exception as e:
        print(f"ERRO CRÍTICO durante a atualização: {e}")
        # Mantém o pacote para uma nova tentativa

def run_server(host, port, open_browser):
    """Inicializa o banco de dados (se necessário) e inicia o servidor Waitress."""
    print("Garantindo que o banco de dados esteja inicializado...")
    inicializar_banco()

    # Inicia a verificação de atualizações em uma thread separada após o início do servidor
    threading.Timer(5.0, app.check_for_updates).start()

    url = f"http://{host}:{port}"
    print("\nServidor iniciado. Pronto para receber conexões.")
    print(f"Acesse em: {url}")
    print("Pressione Ctrl+C no terminal para parar o servidor.")

    if open_browser:
        webbrowser.open(url)
    
    # Inicia o servidor de produção
    # Use host='0.0.0.0' para permitir acesso de outras máquinas na rede
    serve(app, host=host, port=port)

def reset_database():
    """Apaga o banco de dados atual (fazendo um backup) e o recria do zero."""
    print("AVISO: Apagando e recriando o banco de dados...")
    db_path = os.path.join(APP_DATA_PATH, "catalogo.db")
    if os.path.exists(db_path):
        # Faz um backup do banco de dados corrompido antes de apagar
        backup_path = db_path + '.corrupted.bak'
        try:
            os.rename(db_path, backup_path)
            print(f"Banco de dados antigo movido. Um backup foi salvo em: {backup_path}")
        except OSError as e:
            print(f"ERRO ao mover o banco de dados antigo: {e}")
            return

    inicializar_banco()
    print("Banco de dados recriado com sucesso.")

def main():
    """Ponto de entrada principal para a interface de linha de comando."""
    parser = argparse.ArgumentParser(description="Servidor e gerenciador do Catálogo de Peças.")
    
    # Executa a restauração ANTES de qualquer outra coisa, se necessário.
    perform_restore_from_backup()
    
    # Executa a atualização, se um pacote estiver pendente
    perform_update()

    subparsers = parser.add_subparsers(dest='command', help='Comandos disponíveis')

    # Comando 'run' (padrão)
    parser.set_defaults(host='127.0.0.1', port=8000, no_browser=False)
    run_parser = subparsers.add_parser('run', help='Inicia o servidor da aplicação (padrão).')
    run_parser.add_argument('--host', type=str, help='O host para o servidor (ex: 0.0.0.0 para acesso na rede).')
    run_parser.add_argument('--port', type=int, help='A porta para o servidor.')
    run_parser.add_argument('--no-browser', action='store_true', help='Não abre o navegador automaticamente.')

    # Comando 'init-db'
    init_db_parser = subparsers.add_parser('init-db', help='Cria as tabelas do banco de dados, se não existirem.')
    
    # Comando 'reset-db'
    reset_db_parser = subparsers.add_parser('reset-db', help='Apaga e recria o banco de dados.')

    args = parser.parse_args()

    if args.command == 'init-db':
        inicializar_banco()
    elif args.command == 'reset-db':
        reset_database()
    else: # 'run' é o comando padrão
        run_server(args.host, args.port, not args.no_browser)

if __name__ == '__main__':
    # Lógica para lidar com o reinício solicitado pela restauração de backup
    restart_backup_trigger = os.path.join(APP_DATA_PATH, 'RESTART_REQUIRED')
    restart_update_trigger = os.path.join(APP_DATA_PATH, 'RESTART_FOR_UPDATE')

    if os.path.exists(restart_backup_trigger):
        os.remove(restart_backup_trigger) # Limpa o gatilho
        os.execv(sys.executable, [sys.executable] + sys.argv)
    elif os.path.exists(restart_update_trigger):
        os.remove(restart_update_trigger) # Limpa o gatilho
        os.execv(sys.executable, [sys.executable] + sys.argv)
    else:
        main()