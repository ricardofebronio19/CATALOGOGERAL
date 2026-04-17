import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import webbrowser

try:
    from waitress import serve  # type: ignore
except Exception:
    serve = None
    _WAITRESS_MISSING = True
else:
    _WAITRESS_MISSING = False

def _fallback_serve(app, host, port, _max_request_body_size=None):
    # Fallback simples para desenvolvimento quando waitress não está instalado.
    # Usa Flask dev server em modo threaded não é recomendado para produção.
    # Nota: _max_request_body_size é ignorado — parâmetro mantido para compatibilidade de assinatura com waitress.serve()
    print("Aviso: pacote 'waitress' não encontrado. Usando servidor de desenvolvimento Flask como fallback.")
    print("Para instalar o Waitress (recomendado para produção): pip install waitress")
    try:
        app.run(host=host, port=port, threaded=True)
    except Exception as e:
        print(f"Erro ao iniciar servidor de fallback: {e}")

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

# Placeholder para a instância da aplicação. A `app` será criada dentro de `main()`
# para permitir opções de linha de comando que possam alterar o arquivo de DB
# antes da inicialização (ex: --use-repo-db).
app = None


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
            try:
                shutil.move(APP_DATA_PATH, backup_dir_old)
                print(f"O diretório de dados antigo foi salvo em: {backup_dir_old}")
            except Exception as e_move:
                # Em Windows é comum que arquivos (ex: sqlite DB) estejam abertos
                # e impeçam operações atômicas de rename/rmtree. Tentamos um
                # fallback que move/copia os itens individualmente, ignorando
                # arquivos que estejam em uso para não abortar a restauração.
                print(f"Falha ao mover diretório inteiro: {e_move}. Tentando mover itens individualmente.")
                os.makedirs(backup_dir_old, exist_ok=True)
                for name in os.listdir(APP_DATA_PATH):
                    src = os.path.join(APP_DATA_PATH, name)
                    dst = os.path.join(backup_dir_old, name)
                    try:
                        shutil.move(src, dst)
                    except Exception as e_item:
                        print(f"Não foi possível mover {src}: {e_item}. Tentando copiar e pular se travado.")
                        try:
                            if os.path.isdir(src):
                                shutil.copytree(src, dst)
                                try:
                                    shutil.rmtree(src)
                                except Exception:
                                    pass
                            else:
                                shutil.copy2(src, dst)
                                try:
                                    os.remove(src)
                                except Exception:
                                    pass
                        except Exception as e_copy:
                            print(f"Falha ao copiar {src}: {e_copy}. O item será mantido no local.")

        # 2. Extrai o backup para um diretório temporário e mescla no APP_DATA_PATH
        os.makedirs(APP_DATA_PATH, exist_ok=True)
        import zipfile

        temp_extract_dir = None
        try:
            temp_extract_dir = tempfile.mkdtemp(prefix="catalogo_restore_")
            with zipfile.ZipFile(temp_restore, "r") as zf:  # type: ignore
                zf.extractall(temp_extract_dir)

            # Função auxiliar: copia/mescla recusivamente, sobrescrevendo quando possível
            def _merge_copy(src_root, dst_root):
                for root, dirs, files in os.walk(src_root):
                    rel = os.path.relpath(root, src_root)
                    target_dir = os.path.join(dst_root, rel) if rel != "." else dst_root
                    os.makedirs(target_dir, exist_ok=True)
                    for d in dirs:
                        os.makedirs(os.path.join(target_dir, d), exist_ok=True)
                    for f in files:
                        s = os.path.join(root, f)
                        t = os.path.join(target_dir, f)
                        try:
                            # Tenta substituir o arquivo destino
                            shutil.copy2(s, t)
                        except PermissionError:
                            print(f"Arquivo em uso, não foi possível sobrescrever: {t}. Pulando.")
                        except Exception as e_f:
                            print(f"Erro ao copiar {s} -> {t}: {e_f}. Pulando.")

            _merge_copy(temp_extract_dir, APP_DATA_PATH)

        finally:
            # Limpa a extração temporária
            try:
                if temp_extract_dir and os.path.exists(temp_extract_dir):
                    shutil.rmtree(temp_extract_dir)
            except Exception:
                pass

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


def _verificar_porta_livre(host, port):
    """Retorna True se a porta estiver disponível para uso."""
    import socket
    bind_host = "127.0.0.1" if host in ("0.0.0.0", "::", "", None) else host
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((bind_host, port))
            return True
        except OSError:
            return False


def iniciar_servidor(app_instance, host, port, abrir_navegador):
    """Inicializa o banco de dados (se necessário) e inicia o servidor Waitress."""
    # Verifica se a porta está disponível ANTES de tentar iniciar
    if not _verificar_porta_livre(host, port):
        print(f"\n[ERRO] A porta {port} já está em uso.")
        print("Verifique se o aplicativo já está aberto ou se outro serviço está usando esta porta.")
        input("Pressione Enter para sair...")
        return

    print("Garantindo que o banco de dados esteja inicializado...")
    inicializar_banco(app_instance)

    # Inicia a verificação de atualizações e agenda verificações periódicas
    threading.Timer(5.0, schedule_periodic_update_check, args=[app_instance]).start()

    url = f"http://{host}:{port}"
    print("\nServidor iniciado. Pronto para receber conexões.")
    print(f"Acesse em: {url}")
    print("Pressione Ctrl+C no terminal para parar o servidor.")

    if abrir_navegador:
        # Abre o navegador com um delay para garantir que o servidor já está
        # escutando antes da primeira requisição chegar.
        browser_host = "localhost" if host in ("0.0.0.0", "::", "", None) else host
        browser_url = f"http://{browser_host}:{port}"
        def _abrir_browser():
            import time
            time.sleep(1.5)
            try:
                webbrowser.open(browser_url, new=2)
            except Exception as e:
                print(f"Não foi possível abrir o navegador automaticamente: {e}")
        threading.Thread(target=_abrir_browser, daemon=True).start()

    # Inicia o servidor de produção
    # Use host='0.0.0.0' para permitir acesso de outras máquinas na rede
    # Ajusta `max_request_body_size` para permitir uploads grandes (padrão 512MB),
    # pode ser sobrescrito pela variável de ambiente `MAX_REQUEST_BODY_SIZE`.
    max_body = int(os.getenv("MAX_REQUEST_BODY_SIZE", 536870912))
    if _WAITRESS_MISSING or serve is None:
        _fallback_serve(app_instance, host, port, _max_request_body_size=max_body)
    else:
        try:
            serve(app_instance, host=host, port=port, max_request_body_size=max_body)  # type: ignore
        except OSError as e:
            if "Address already in use" in str(e) or "WinError 10048" in str(e):
                print(f"\n[ERRO] A porta {port} já está em uso.")
                print("Verifique se o aplicativo já está aberto ou se outro serviço está usando esta porta.")
                input("Pressione Enter para sair...")
            else:
                raise e


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

    # Se nenhum comando conhecido for encontrado, assume 'run' como padrão
    if len(sys.argv) == 1 or sys.argv[1] not in known_cmds:
        sys.argv.insert(1, "run")

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
    run_parser.add_argument(
        "--use-repo-db",
        action="store_true",
        dest="use_repo_db",
        help="Copia 'data/catalogo.db' do repositório para o APP_DATA_PATH, sobrescrevendo. Útil em desenvolvimento.",
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

    # Se o usuário pediu para usar o DB do repositório, copie-o para APP_DATA_PATH
    if getattr(args, 'use_repo_db', False):
        try:
            repo_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', 'catalogo.db')
            target_db = os.path.join(APP_DATA_PATH, 'catalogo.db')
            if os.path.exists(repo_db):
                os.makedirs(APP_DATA_PATH, exist_ok=True)
                shutil.copy2(repo_db, target_db)
                print(f"Arquivo de DB do repositório copiado para: {target_db}")
            else:
                print(f"Arquivo {repo_db} não encontrado no repositório.")
        except Exception as e:
            print(f"Falha ao copiar DB do repositório: {e}")

    # Cria a instância da aplicação (depois de possíveis operações no DB)
    global app
    if app is None:
        app = create_app()

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
        iniciar_servidor(app, host, port, not no_browser)


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
