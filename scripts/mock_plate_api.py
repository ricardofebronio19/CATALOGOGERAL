from flask import Flask, request, jsonify

app = Flask('mock_plate_api')

@app.route('/placa/consulta', methods=['POST'])
def consulta():
    data = request.get_json(force=True, silent=True) or {}
    plate = data.get('placa') or request.args.get('placa')
    # Resposta simulada simples
    if not plate:
        return jsonify({'message': 'placa não fornecida'}), 400
    # Retorna formato parecido com APIs públicas
    return jsonify({
        'modelo': 'Palio',
        'ano': '2010',
        'motor': '1.0',
        'montadora': 'Fiat',
        'placa': plate
    })

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5001)
