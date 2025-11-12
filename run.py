import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import webbrowser

from waitress import serve

from app import (
    APP_DATA_PATH,
    create_app,
    inicializar_banco,
    schedule_periodic_update_check,
)

# Cria a instância da aplicação
try:
    # Força UTF-8 para stdout/stderr e uso em I/O no Windows, evitando
    # UnicodeEncodeError ao imprimir caracteres (ex.: emojis) em consoles
    # configurados com cp1252. Também define PYTHONIOENCODING para o
    # processo e reconfigura os streams quando possível.
    os.environ.setdefault("PYTHONIOENCODING", "utf-8")
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    if hasattr(sys.stderr, "reconfigure"):
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
except Exception:
    # Não devemos falhar na inicialização do app por conta desta tentativa.
    pass

# Cria a instância da aplicação
app = create_app()


def executar_restauracao_de_backup():
    """
    Verifica se um arquivo de backup (.zip) está pendente para restauração
    e executa o processo. Esta função é chamada na inicialização da aplicação.
    """
    restore_filepath = os.path.join(APP_DATA_PATH, "backup_para_restaurar.zip")
    restart_trigger = os.path.join(APP_DATA_PATH, "RESTART_REQUIRED")

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
        with tempfile.NamedTemporaryFile(delete=False, suffix=".zip") as tmpf:
            temp_restore = tmpf.name
        shutil.copy2(restore_filepath, temp_restore)
    except Exception as e:
        print(f"Erro ao preparar arquivo temporário para restauração: {e}")
        return

    try:
        # 1. Faz um backup do diretório de dados atual, por segurança
        backup_dir_old = os.path.join(
            APP_DATA_PATH,
            f"../CatalogoDePecas_old_{os.path.getmtime(restore_filepath)}",
        )
        if os.path.exists(APP_DATA_PATH):
            shutil.move(APP_DATA_PATH, backup_dir_old)
            print(f"O diretório de dados antigo foi salvo em: {backup_dir_old}")

        # 2. Recria o diretório de dados e extrai o backup (usando o temporário)
        os.makedirs(APP_DATA_PATH, exist_ok=True)
        import zipfile

        with zipfile.ZipFile(temp_restore, "r") as zf:  # type: ignore
            zf.extractall(APP_DATA_PATH)

        # 3. Se o backup for do tipo SQL, executa o script SQL para recriar o banco
        sql_path = os.path.join(APP_DATA_PATH, "catalogo.db.sql")
        if os.path.exists(sql_path):
            import sqlite3

            db_path = os.path.join(APP_DATA_PATH, "catalogo.db")
            if os.path.exists(db_path):
                os.remove(db_path)
            conn = sqlite3.connect(db_path)
            with open(sql_path, "r", encoding="utf-8") as f:
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
    install_dir = os.path.dirname(
        os.path.abspath(sys.executable if getattr(sys, "frozen", False) else __file__)
    )

    try:
        import zipfile

        # Extrai o conteúdo do zip para o diretório de instalação, sobrescrevendo os arquivos existentes
        with zipfile.ZipFile(update_package, "r") as zip_ref:
            zip_ref.extractall(install_dir)

        os.remove(update_package)  # Remove o pacote de atualização após a extração
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
        # Alguns navegadores não aceitam 0.0.0.0 como host para abrir uma aba.
        # Usar 'localhost' quando o host for 0.0.0.0 ou equivalente garante que
        # o browser abra corretamente apontando para a máquina local.
        browser_url = url
        if host in ("0.0.0.0", "::", "", None):
            browser_url = f"http://localhost:{port}"
        try:
            webbrowser.open(browser_url, new=2)  # new=2 tenta abrir em nova aba
        except Exception as e:
            print(f"Não foi possível abrir o navegador automaticamente: {e}")

    # Inicia o servidor de produção
    # Use host='0.0.0.0' para permitir acesso de outras máquinas na rede
    serve(app, host=host, port=port)  # type: ignore


def reset_database():
    """Apaga todas as tabelas do banco de dados e as recria do zero."""
    confirm = input(
        "AVISO: Esta ação é irreversível e apagará TODOS os dados. Deseja continuar? (s/N): "
    )
    if confirm.lower() != "s":
        print("Operação cancelada.")
        return
    print("Iniciando a recriação do banco de dados...")
    inicializar_banco(app, reset=True)
    print("Banco de dados resetado com sucesso.")


def main():
    """Ponto de entrada principal para a interface de linha de comando."""
    # --- INÍCIO DO CÓDIGO DE DIAGNÓSTICO ---
    try:
        import datetime
        log_path = os.path.join(tempfile.gettempdir(), "catalogo_diag_args.txt")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"Timestamp: {datetime.datetime.now()}\n")
            f.write(f"CWD: {os.getcwd()}\n")
            f.write(f"sys.executable: {sys.executable}\n")
            f.write("sys.argv:\n")
            for i, arg in enumerate(sys.argv):
                f.write(f"  [{i}]: {arg}\n")
        # Para o diagnóstico, podemos sair aqui para não executar o resto do app.
        # Comente a linha abaixo para permitir que o app continue normalmente.
        # sys.exit(0) 
    except Exception as e:
        # Se o logging falhar, não impede a execução normal
        pass
    # --- FIM DO CÓDIGO DE DIAGNÓSTICO ---

    # Compatibilidade: aceitar ser chamado com 'run.py' como primeiro argumento
    # (ex.: quando usuários chamam o executável passando o nome do script por engano)
    if len(sys.argv) > 1:
        first = os.path.basename(sys.argv[1])
        # Alguns wrappers/atalhos injetam o nome do script ('run.py') como
        # primeiro argumento. Em vez de substituir por 'run' (o que causa
        # confusão quando o comando real vem em seguida), removemos essa
        # entrada para que o subcomando esperado ocupe a posição correta.
        if first.lower() == "run.py":
            del sys.argv[1]
    # Normaliza o argv buscando um subcomando conhecido em qualquer posição
    # Isso ajuda quando empacotadores ou atalhos injetam argumentos em posições
    # diferentes (ex: alguns wrappers podem colocar o comando após opções).
    known_cmds = {"run", "reset-db", "link-images", "import-csv"}
    if len(sys.argv) > 1:
        for i, a in enumerate(sys.argv[1:], start=1):
            if a in known_cmds:
                if i != 1:
                    # Move o comando para a posição 1, preservando a ordem dos demais
                    rest = sys.argv[1:i] + sys.argv[i + 1:]
                    sys.argv = [sys.argv[0], a] + rest
                break

    parser = argparse.ArgumentParser(
        description="Servidor e gerenciador para a aplicação Catálogo de Peças."
    )
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponíveis")

    # Comando 'run' (padrão)
    run_parser = subparsers.add_parser(
        "run", help="Inicia o servidor da aplicação (comando padrão)."
    )
    run_parser.add_argument(
        "--host",
        type=str,
        default="0.0.0.0",
        help="O host a ser usado pelo servidor (ex: 0.0.0.0 para acesso na rede).",
    )
    run_parser.add_argument(
        "--port", 
        type=int, 
        default=8000,
        help="A porta a ser usada pelo servidor."
    )
    run_parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Impede que o navegador seja aberto automaticamente.",
    )

    # Comando 'reset-db'
    subparsers.add_parser(
        "reset-db", help="Apaga todas as tabelas e recria o banco de dados do zero."
    )

    # Comando 'link-images'
    subparsers.add_parser(
        "link-images", help="Varre a pasta de uploads e vincula imagens aos produtos."
    )

    # Comando 'import-csv'
    import_parser = subparsers.add_parser(
        "import-csv", help="Importa dados de um arquivo CSV para o banco de dados."
    )
    import_parser.add_argument(
        "filepath", type=str, help="O caminho para o arquivo CSV a ser importado."
    )

    args = parser.parse_args()

    if args.command == "reset-db":
        reset_database()
    elif args.command == "link-images":
        from utils.image_utils import vincular_imagens_por_codigo

        print("Iniciando a vinculação de imagens...")
        vincular_imagens_por_codigo(app)
        print("Processo de vinculação de imagens concluído.")
    elif args.command == "import-csv":
        from importar_pecas import importar_pecas_de_csv

        print(f"Iniciando a importação do arquivo: {args.filepath}")
        importar_pecas_de_csv(app, args.filepath)
        print("Processo de importação de CSV concluído.")
    else:  # 'run' é o comando padrão
        # Define valores padrão se não foram especificados
        host = getattr(args, 'host', None) or "0.0.0.0"
        port = getattr(args, 'port', None) or 8000
        no_browser = getattr(args, 'no_browser', False)
        
        # Executa a restauração e atualização apenas quando o servidor está sendo iniciado.
        # Isso evita que um 'reset-db' seja precedido por uma restauração.
        executar_restauracao_de_backup()
        executar_atualizacao()

        # Inicia o servidor
        iniciar_servidor(host, port, not no_browser)


if __name__ == "__main__":
    # Lógica para lidar com o reinício solicitado pela restauração de backup
    # ou por uma atualização.
    restart_triggers = [
        os.path.join(APP_DATA_PATH, "RESTART_REQUIRED"),
        os.path.join(APP_DATA_PATH, "RESTART_FOR_UPDATE"),
    ]

    # Verifica se qualquer um dos arquivos de gatilho de reinício existe
    if any(os.path.exists(trigger) for trigger in restart_triggers):
        for trigger in restart_triggers:
            if os.path.exists(trigger):
                os.remove(trigger)  # Limpa o gatilho encontrado
        os.execv(sys.executable, [sys.executable] + sys.argv)
    else:
        main()
