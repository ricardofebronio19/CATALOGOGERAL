"""
Launcher GUI para o Catálogo de Peças usando pywebview.
Este script cria uma janela nativa em vez de abrir o navegador.
"""
import os
import sys
import threading
import time
import webview
from webview.menu import Menu, MenuAction, MenuSeparator

from waitress import serve

from app import APP_DATA_PATH, VERSION, create_app, inicializar_banco, schedule_periodic_update_check
from run import executar_atualizacao, executar_restauracao_de_backup

# Cria a instância da aplicação
try:
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
    pass

app = create_app()


class API:
    """API JavaScript para comunicação entre Python e a janela."""
    
    def __init__(self, window):
        self.window = window
    
    def get_version(self):
        """Retorna a versão da aplicação."""
        return VERSION
    
    def minimize_window(self):
        """Minimiza a janela."""
        self.window.minimize()
    
    def maximize_window(self):
        """Maximiza/restaura a janela."""
        self.window.toggle_fullscreen()
    
    def show_about(self):
        """Mostra informações sobre o aplicativo."""
        about_html = f"""
        <html>
        <head>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    text-align: center;
                }}
                .container {{
                    background: rgba(255, 255, 255, 0.1);
                    padding: 40px;
                    border-radius: 20px;
                    backdrop-filter: blur(10px);
                    box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
                }}
                h1 {{
                    margin: 0 0 10px 0;
                    font-size: 2.5em;
                }}
                p {{
                    margin: 10px 0;
                    font-size: 1.2em;
                }}
                .version {{
                    background: rgba(255, 255, 255, 0.2);
                    padding: 10px 20px;
                    border-radius: 25px;
                    display: inline-block;
                    margin-top: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚗 Catálogo de Peças</h1>
                <p>Sistema de Gestão de Peças Automotivas</p>
                <div class="version">Versão {VERSION}</div>
                <p style="margin-top: 30px; font-size: 0.9em;">
                    Desenvolvido por ricardofebronio19<br>
                    © 2025 Todos os direitos reservados
                </p>
            </div>
        </body>
        </html>
        """
        # Cria janela modal sobre
        about_window = webview.create_window(
            'Sobre o Catálogo de Peças',
            html=about_html,
            width=500,
            height=400,
            resizable=False,
            frameless=False
        )
        return about_window


def criar_menu():
    """Cria o menu nativo da aplicação."""
    menu_items = [
        Menu(
            'Arquivo',
            [
                MenuAction('Recarregar', lambda: print('Recarregando...')),
                MenuSeparator(),
                MenuAction('Sair', lambda: sys.exit(0))
            ]
        ),
        Menu(
            'Visualizar',
            [
                MenuAction('Tela Cheia', lambda: None),
                MenuAction('Zoom +', lambda: None),
                MenuAction('Zoom -', lambda: None),
                MenuSeparator(),
                MenuAction('Resetar Zoom', lambda: None)
            ]
        ),
        Menu(
            'Ajuda',
            [
                MenuAction('Documentação', lambda: None),
                MenuSeparator(),
                MenuAction('Sobre', lambda: None)
            ]
        )
    ]
    return menu_items


def iniciar_servidor_background(host="127.0.0.1", port=8000):
    """Inicia o servidor Flask em uma thread separada."""
    print(f"[SERVIDOR] Iniciando Flask em {host}:{port}...")
    try:
        inicializar_banco(app)
        print("[SERVIDOR] Banco de dados inicializado")
        
        # Inicia verificação de atualizações
        threading.Timer(5.0, schedule_periodic_update_check, args=[app]).start()
        print("[SERVIDOR] Sistema de atualizações agendado")
        
        # Servidor Waitress em thread para não bloquear a GUI
        print(f"[SERVIDOR] Aguardando conexões em http://{host}:{port}")
        serve(app, host=host, port=port, _quiet=False)
    except Exception as e:
        print(f"[SERVIDOR] ERRO CRÍTICO: {e}")
        import traceback
        traceback.print_exc()


def criar_splash_screen():
    """Retorna o HTML do splash screen para ser usado na janela principal."""
    splash_html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {
                margin: 0;
                padding: 0;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                color: white;
            }
            .splash-container {
                text-align: center;
                animation: fadeIn 0.5s ease-in;
            }
            @keyframes fadeIn {
                from { opacity: 0; transform: translateY(-20px); }
                to { opacity: 1; transform: translateY(0); }
            }
            .logo {
                font-size: 5em;
                margin-bottom: 20px;
                animation: bounce 1s infinite;
            }
            @keyframes bounce {
                0%, 100% { transform: translateY(0); }
                50% { transform: translateY(-10px); }
            }
            h1 {
                margin: 0;
                font-size: 2.5em;
                font-weight: 300;
                letter-spacing: 2px;
            }
            .loader {
                width: 50px;
                height: 50px;
                border: 5px solid rgba(255, 255, 255, 0.3);
                border-top-color: white;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 30px auto;
            }
            @keyframes spin {
                to { transform: rotate(360deg); }
            }
            .status {
                margin-top: 20px;
                font-size: 1.1em;
                opacity: 0.8;
            }
        </style>
        <script>
            // Redireciona para a aplicação após aguardar servidor inicializar
            let countdown = 4;
            
            function updateStatus(message) {
                const statusEl = document.querySelector('.status');
                if (statusEl) {
                    statusEl.textContent = message;
                }
            }
            
            function updateCountdown() {
                if (countdown > 0) {
                    updateStatus(`Aguardando servidor inicializar... ${countdown}s`);
                    countdown--;
                    setTimeout(updateCountdown, 1000);
                } else {
                    updateStatus('Carregando aplicação...');
                    setTimeout(() => {
                        window.location.href = '/';
                    }, 500);
                }
            }
            
            // Inicia contagem regressiva
            updateStatus('Iniciando servidor Flask...');
            setTimeout(updateCountdown, 1000);
        </script>
    </head>
    <body>
        <div class="splash-container">
            <div class="logo">🚗</div>
            <h1>CATÁLOGO DE PEÇAS</h1>
            <div class="loader"></div>
            <div class="status">Inicializando sistema...</div>
        </div>
    </body>
    </html>
    """
    
    return splash_html


def criar_janela_principal(host="127.0.0.1", port=8000):
    """Cria a janela principal do aplicativo."""
    url = f"http://{host}:{port}"
    
    # Configurações da janela principal
    window_config = {
        'title': f'Catálogo de Peças v{VERSION}',
        'url': url,
        'width': 1366,
        'height': 900,
        'resizable': True,
        'fullscreen': False,
        'min_size': (1024, 768),
        'background_color': '#667eea',  # Cor do gradiente enquanto carrega
        'text_select': True,
        'confirm_close': False,
        'easy_drag': False,
    }
    
    # Cria a janela principal
    window = webview.create_window(**window_config)
    
    return window


def main():
    """Ponto de entrada principal para a versão GUI."""
    print("=" * 60)
    print(f"Catálogo de Peças v{VERSION} - Versão Desktop")
    print("=" * 60)
    
    # Executa restauração e atualização se necessário
    executar_restauracao_de_backup()
    executar_atualizacao()
    
    # Configurações do servidor
    HOST = "127.0.0.1"  # Localhost apenas - mais seguro
    PORT = 8000
    
    # Inicia servidor em thread separada
    print("\n[GUI] Iniciando servidor Flask em background...")
    server_thread = threading.Thread(
        target=iniciar_servidor_background, 
        args=(HOST, PORT),
        daemon=True  # Thread morre quando janela fecha
    )
    server_thread.start()
    
    # Aguarda servidor estar pronto antes de abrir janela
    print("[GUI] Aguardando servidor inicializar...")
    url = f"http://{HOST}:{PORT}"
    for tentativa in range(30):  # Tenta por 6 segundos
        try:
            import requests
            response = requests.get(url, timeout=1)
            if response.status_code == 200:
                print("[GUI] ✓ Servidor pronto!")
                break
        except:
            pass
        time.sleep(0.2)
    
    # Cria a janela principal
    print("[GUI] Abrindo janela principal...")
    window = criar_janela_principal(HOST, PORT)
    
    # Adiciona API depois que a janela é criada
    api = API(window)
    
    # Configurações avançadas do webview
    print("[GUI] Iniciando interface gráfica...\n")
    webview.start(
        debug=False,  # Mude para True durante desenvolvimento
        http_server=False,  # Não precisamos do servidor embutido
        # menu=criar_menu(),  # Descomente para adicionar menu nativo
    )
    
    print("\n" + "=" * 60)
    print("Aplicação encerrada com sucesso.")
    print("=" * 60)


if __name__ == "__main__":
    # Lógica de reinício (mesma do run.py)
    restart_triggers = [
        os.path.join(APP_DATA_PATH, "RESTART_REQUIRED"),
        os.path.join(APP_DATA_PATH, "RESTART_FOR_UPDATE"),
    ]
    
    if any(os.path.exists(trigger) for trigger in restart_triggers):
        for trigger in restart_triggers:
            if os.path.exists(trigger):
                os.remove(trigger)
        os.execv(sys.executable, [sys.executable] + sys.argv)
    else:
        main()
