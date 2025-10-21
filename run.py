from waitress import serve
import os
import subprocess
import shutil
import webbrowser
import argparse
import sys
import threading
import tempfile

from app import create_app, inicializar_banco, APP_DATA_PATH, check_for_updates, schedule_periodic_update_check
# Cria a instância da aplicação
app = create_app()


def executar_restauracao_de_backup():
    """
    Verifica se um arquivo de backup (.zip) está pendente para restauração
    e executa o processo. Esta função é chamada na inicialização da aplicação.
    """
    restore_filepath = os.path.join(APP_DATA_PATH, "backup_para_restaurar.zip")
    restart_trigger = os.path.join(APP_DATA_PATH, 'RESTART_REQUIRED')

    if not os.path.exists(restore_filepath):
        # Se não há backup para restaurar, remove o gatilho de reinício se ele existir
        if os.path.exists(restart_trigger):
            os.remove(restart_trigger)
        return

    print("Arquivo de backup para restauração encontrado. Iniciando o processo...")

    # Para evitar que o zip seja movido junto com o diretório de dados (o que
    # faz com que o caminho original deixe de existir), primeiro copiamos o
    # arquivo de restauração para um arquivo temporário e usamos esse
    # temporário para a extração.
    temp_restore = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as tmpf:
            temp_restore = tmpf.name
        shutil.copy2(restore_filepath, temp_restore)
    except Exception as e:
        print(f"Erro ao preparar arquivo temporário para restauração: {e}")
        return

    try:
        # 1. Faz um backup do diretório de dados atual, por segurança
        backup_dir_old = os.path.join(APP_DATA_PATH, f"../CatalogoDePecas_old_{os.path.getmtime(restore_filepath)}")
        if os.path.exists(APP_DATA_PATH):
            shutil.move(APP_DATA_PATH, backup_dir_old)
            print(f"O diretório de dados antigo foi salvo em: {backup_dir_old}")

        # 2. Recria o diretório de dados e extrai o backup (usando o temporário)
        os.makedirs(APP_DATA_PATH, exist_ok=True)
        import zipfile
        with zipfile.ZipFile(temp_restore, 'r') as zf: # type: ignore
            zf.extractall(APP_DATA_PATH)

        # 3. Se o backup for do tipo SQL, executa o script SQL para recriar o banco
        sql_path = os.path.join(APP_DATA_PATH, "catalogo.db.sql")
        if os.path.exists(sql_path):
            import sqlite3
            db_path = os.path.join(APP_DATA_PATH, "catalogo.db")
            if os.path.exists(db_path): os.remove(db_path)
            conn = sqlite3.connect(db_path)
            with open(sql_path, 'r', encoding='utf-8') as f:
                conn.executescript(f.read())
            conn.close()
            os.remove(sql_path)  # Limpa o arquivo sql após o uso

        # Remove o temporário usado para extração. Mantemos o zip original no
        # backup antigo para diagnóstico caso algo dê errado.
        try:
            if temp_restore and os.path.exists(temp_restore):
                os.remove(temp_restore)
        except Exception:
            pass

        print("Restauração do backup concluída com sucesso!")
    except zipfile.BadZipFile as e:
        print(f"Erro: Arquivo zip corrompido ou inválido: {e}")
        print("Certifique-se de que o arquivo de backup é um arquivo zip válido.")
    except (subprocess.CalledProcessError, FileNotFoundError, Exception) as e:
        print(f"ERRO CRÍTICO durante a restauração do backup: {e}")
        print("O arquivo de backup foi mantido para uma nova tentativa de restauração.")
        try:
            if temp_restore and os.path.exists(temp_restore):
                os.remove(temp_restore)
        except Exception:
            pass

def executar_atualizacao():
    """Verifica se um pacote de atualização existe e o instala."""
    update_package = os.path.join(APP_DATA_PATH, "update_package.zip")
    if not os.path.exists(update_package):
        return  # Nenhuma atualização para instalar

    print("Pacote de atualização encontrado. Iniciando o processo...")

    # O diretório de instalação é o diretório onde o executável está rodando
    install_dir = os.path.dirname(os.path.abspath(sys.executable if getattr(sys, 'frozen', False) else __file__))
    
    try:
        import zipfile
        # Extrai o conteúdo do zip para o diretório de instalação, sobrescrevendo os arquivos existentes
        with zipfile.ZipFile(update_package, 'r') as zip_ref:
            zip_ref.extractall(install_dir)

        os.remove(update_package) # Remove o pacote de atualização após a extração
        print("Atualização aplicada com sucesso!")

    except Exception as e:
        print(f"ERRO CRÍTICO durante a atualização: {e}")
        # Mantém o pacote de atualização para uma nova tentativa

def iniciar_servidor(host, port, abrir_navegador):
    """Inicializa o banco de dados (se necessário) e inicia o servidor Waitress."""
    print("Garantindo que o banco de dados esteja inicializado...")
    inicializar_banco(app)

    # Inicia a verificação de atualizações e agenda verificações periódicas
    threading.Timer(5.0, schedule_periodic_update_check, args=[app]).start()

    url = f"http://{host}:{port}"
    print("\nServidor iniciado. Pronto para receber conexões.")
    print(f"Acesse em: {url}")
    print("Pressione Ctrl+C no terminal para parar o servidor.")

    if abrir_navegador:
        webbrowser.open(url)
    
    # Inicia o servidor de produção
    # Use host='0.0.0.0' para permitir acesso de outras máquinas na rede
    serve(app, host=host, port=port) # type: ignore

def reset_database():
    """Apaga todas as tabelas do banco de dados e as recria do zero."""
    confirm = input("AVISO: Esta ação é irreversível e apagará TODOS os dados. Deseja continuar? (s/N): ")
    if confirm.lower() != 's':
        print("Operação cancelada.")
        return
    print("Iniciando a recriação do banco de dados...")
    inicializar_banco(app, reset=True)
    print("Banco de dados resetado com sucesso.")

def main():
    """Ponto de entrada principal para a interface de linha de comando."""
    parser = argparse.ArgumentParser(description="Servidor e gerenciador para a aplicação Catálogo de Peças.")
    subparsers = parser.add_subparsers(dest='command', help='Comandos disponíveis')

    # Comando 'run' (padrão)
    parser.set_defaults(host='0.0.0.0', port=8000, no_browser=False)
    run_parser = subparsers.add_parser('run', help='Inicia o servidor da aplicação (comando padrão).')
    run_parser.add_argument('--host', type=str, help='O host a ser usado pelo servidor (ex: 0.0.0.0 para acesso na rede).')
    run_parser.add_argument('--port', type=int, help='A porta a ser usada pelo servidor.')
    run_parser.add_argument('--no-browser', action='store_true', help='Impede que o navegador seja aberto automaticamente.')

    # Comando 'reset-db'
    subparsers.add_parser('reset-db', help='Apaga todas as tabelas e recria o banco de dados do zero.')

    # Comando 'link-images'
    subparsers.add_parser('link-images', help='Varre a pasta de uploads e vincula imagens aos produtos.')

    # Comando 'import-csv'
    import_parser = subparsers.add_parser('import-csv', help='Importa dados de um arquivo CSV para o banco de dados.')
    import_parser.add_argument('filepath', type=str, help='O caminho para o arquivo CSV a ser importado.')

    args = parser.parse_args()

    if args.command == 'reset-db':
        reset_database()
    elif args.command == 'link-images':
        from vincular_imagens import vincular_imagens_por_codigo
        print("Iniciando a vinculação de imagens...")
        vincular_imagens_por_codigo(app)
        print("Processo de vinculação de imagens concluído.")
    elif args.command == 'import-csv':
        from importar_pecas import importar_pecas_de_csv
        print(f"Iniciando a importação do arquivo: {args.filepath}")
        importar_pecas_de_csv(app, args.filepath)
        print("Processo de importação de CSV concluído.")
    else: # 'run' é o comando padrão
        # Executa a restauração e atualização apenas quando o servidor está sendo iniciado.
        # Isso evita que um 'reset-db' seja precedido por uma restauração.
        executar_restauracao_de_backup()
        executar_atualizacao()

        # Inicia o servidor
        iniciar_servidor(args.host, args.port, not args.no_browser)

if __name__ == '__main__':
    # Lógica para lidar com o reinício solicitado pela restauração de backup
    # ou por uma atualização.
    restart_triggers = [
        os.path.join(APP_DATA_PATH, 'RESTART_REQUIRED'),
        os.path.join(APP_DATA_PATH, 'RESTART_FOR_UPDATE')
    ]

    # Verifica se qualquer um dos arquivos de gatilho de reinício existe
    if any(os.path.exists(trigger) for trigger in restart_triggers):
        for trigger in restart_triggers:
            if os.path.exists(trigger):
                os.remove(trigger) # Limpa o gatilho encontrado
        os.execv(sys.executable, [sys.executable] + sys.argv)
    else:
        main()