from waitress import serve
from app import app, db, inicializar_banco, APP_DATA_PATH, UPLOAD_FOLDER, carregar_config_aparencia, check_for_updates, DATABASE_URL
import os
import zipfile
import shutil
import webbrowser
import argparse
from datetime import datetime
import sys
import threading

# Verifica qual banco de dados está em uso
IS_POSTGRES = DATABASE_URL and DATABASE_URL.startswith('postgres')

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

    if IS_POSTGRES:
        print("AVISO: A restauração automática é suportada apenas para SQLite.")
        print("Para PostgreSQL, a restauração deve ser feita manualmente.")
        return

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

def run_server(host, port, open_browser):
    """Inicializa o banco de dados (se necessário) e inicia o servidor Waitress."""
    # Adiciona o caminho dos binários do PostgreSQL ao PATH do sistema, se configurado.
    # Isso garante que ferramentas como pg_dump e pg_restore sejam encontradas.
    config = carregar_config_aparencia()
    pg_bin_path = config.get('postgres_bin_path')
    if pg_bin_path and os.path.isdir(pg_bin_path):
        os.environ['PATH'] = pg_bin_path + os.pathsep + os.environ['PATH']
        print(f"Adicionado ao PATH: {pg_bin_path}")

    print("Garantindo que o banco de dados esteja inicializado...")
    inicializar_banco()

    # Inicia a verificação de atualizações em uma thread separada após o início do servidor
    threading.Timer(5.0, check_for_updates).start()

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
    print("AVISO: Esta operação irá apagar todos os dados existentes.")
    confirm = input("Tem certeza que deseja continuar? (s/N): ")
    if confirm.lower() != 's':
        print("Operação cancelada.")
        return

    if IS_POSTGRES:
        print("Resetando banco de dados PostgreSQL (apagando e recriando todas as tabelas)...")
        with app.app_context():
            db.drop_all()
    else: # Lógica para SQLite
        print("Resetando banco de dados SQLite...")
        db_path = os.path.join(APP_DATA_PATH, "catalogo.db")
        if os.path.exists(db_path):
            backup_path = db_path + f'.bak.{datetime.now().strftime("%Y%m%d%H%M%S")}'
            shutil.move(db_path, backup_path)
            print(f"Backup do banco de dados antigo salvo em: {backup_path}")

    # Para ambos os casos, a inicialização recria as tabelas e o usuário admin
    inicializar_banco()
    print("Banco de dados recriado com sucesso.")

def main():
    # Lógica para lidar com o reinício solicitado pela restauração de backup
    update_trigger_file = os.path.join(APP_DATA_PATH, 'RESTART_FOR_UPDATE')
    if os.path.exists(update_trigger_file):
        os.remove(update_trigger_file) # Limpa o gatilho de reinício

        update_package_path = os.path.join(APP_DATA_PATH, "update_package.zip")
        if os.path.exists(update_package_path):
            print("Pacote de atualização encontrado. Iniciando processo...")
            install_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
            
            try:
                with zipfile.ZipFile(update_package_path, 'r') as zip_ref:
                    zip_ref.extractall(install_dir)
                os.remove(update_package_path)
                print("Atualização aplicada com sucesso! Reiniciando a aplicação...")
            except Exception as e:
                print(f"ERRO CRÍTICO durante a atualização: {e}")
        else:
            print("Gatilho de atualização encontrado, mas o pacote 'update_package.zip' não foi localizado.")

        # Reinicia a aplicação para carregar os novos arquivos
        os.execv(sys.executable, [sys.executable] + sys.argv)
    else:
        # A lógica de restauração de backup deve ser verificada se não houver atualização pendente
        restart_backup_trigger = os.path.join(APP_DATA_PATH, 'RESTART_REQUIRED')

        if os.path.exists(restart_backup_trigger):
            os.remove(restart_backup_trigger) # Limpa o gatilho
            perform_restore_from_backup()
            os.execv(sys.executable, [sys.executable] + sys.argv)
        else:
            # Se não houver gatilhos de reinício, inicia a aplicação normalmente
            pass # Continua para a lógica principal

    """Ponto de entrada principal para a interface de linha de comando."""
    parser = argparse.ArgumentParser(description="Servidor e gerenciador do Catálogo de Peças.")
    # Adiciona os argumentos do servidor ao parser principal para que possam ser usados sem o comando 'run'
    parser.add_argument('--host', type=str, default='0.0.0.0', help='O host para o servidor (ex: 0.0.0.0 para acesso na rede).')
    parser.add_argument('--port', type=int, default=8000, help='A porta para o servidor.')
    parser.add_argument('--no-browser', action='store_true', help='Não abre o navegador automaticamente.')

    subparsers = parser.add_subparsers(dest='command', help='Comandos disponíveis. Se nenhum for especificado, "run" será usado.')
    # Comando 'run' (padrão)
    subparsers.add_parser('run', help='Inicia o servidor da aplicação (padrão).')

    # Comando 'init-db'
    init_db_parser = subparsers.add_parser('init-db', help='Cria as tabelas do banco de dados, se não existirem.')
    
    # Comando 'reset-db'
    reset_db_parser = subparsers.add_parser('reset-db', help='Apaga e recria o banco de dados.')

    args = parser.parse_args()

    # Define 'run' como o comando padrão se nenhum for fornecido
    if args.command is None:
        args.command = 'run'

    if args.command == 'init-db':
        inicializar_banco()
    elif args.command == 'reset-db':
        reset_database()
    elif args.command == 'run':
        # Os argumentos agora são lidos diretamente do objeto args
        run_server(args.host, args.port, not args.no_browser)

if __name__ == '__main__':
    main()