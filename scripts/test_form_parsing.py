# Script de teste para simular parsing de formulario de aplicacoes
# Executar dentro do ambiente do projeto para verificar a limpeza de 'id' vazio

def filter_aplicacoes(aplicacoes_form_values):
    cleaned = []
    for data in aplicacoes_form_values:
        if not data.get('veiculo'):
            continue
        # comportamento igual ao que implementamos em routes.py
        filtered = {k: v for k, v in data.items() if k != 'id'}
        cleaned.append(filtered)
    return cleaned


def main():
    # Simula dados vindos do request.form
    sample = [
        {'id': '', 'veiculo': 'AMAROK', 'ano': '2010/...', 'motor': '2.0 16V', 'conf_mtr': '', 'montadora': 'VOLKSWAGEN'},
        {'id': '123', 'veiculo': 'GOLF', 'ano': '2015', 'motor': '1.4', 'conf_mtr': '', 'montadora': 'VOLKSWAGEN'},
        {'id': '', 'veiculo': '', 'ano': '', 'motor': '', 'conf_mtr': '', 'montadora': ''},
    ]

    print('Antes:')
    for s in sample:
        print(s)

    cleaned = filter_aplicacoes(sample)
    print('\nDepois (filtrado):')
    for c in cleaned:
        print(c)

if __name__ == '__main__':
    main()
