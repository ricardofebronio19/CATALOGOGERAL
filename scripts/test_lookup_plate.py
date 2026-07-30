import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app import create_app
from unittest.mock import patch, Mock

app = create_app()
# Apontar para o mock local (iniciado em scripts/mock_plate_api.py)
app.config['VEHICLE_API_URL'] = 'http://127.0.0.1:5001/placa/consulta'
app.config['VEHICLE_API_METHOD'] = 'POST'

with app.test_client() as client:
    # Inicia mock server embutido para garantir disponibilidade durante o teste
    try:
        from mock_plate_api import app as mock_app
        from werkzeug.serving import make_server
        import threading

        server = make_server('127.0.0.1', 5001, mock_app)
        server_thread = threading.Thread(target=server.serve_forever)
        server_thread.daemon = True
        server_thread.start()

        rv = client.get('/api/lookup_plate?plate=FMR7534')
        print('Status code:', rv.status_code)
        try:
            print('Response JSON:')
            print(rv.get_data(as_text=True))
        except Exception as e:
            print('Erro ao imprimir resposta:', e)
    finally:
        try:
            server.shutdown()
        except Exception:
            pass
