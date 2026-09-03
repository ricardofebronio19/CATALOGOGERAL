from routes import _parsear_medidas_para_dict, _processar_medidas_estruturadas


def test_processar_medidas_estruturadas_inclui_campos_customizados():
    form_data = {
        "largura": "50",
        "custom_medida_label_0": "Espessura",
        "custom_medida_value_0": "5",
        "custom_medida_label_1": "Observação",
        "custom_medida_value_1": "Ajuste final",
    }

    resultado = _processar_medidas_estruturadas(form_data)

    assert "LARGURA: 50MM" in resultado
    assert "ESPESSURA: 5" in resultado
    assert "OBSERVAÇÃO: AJUSTE FINAL" in resultado


def test_parsear_medidas_para_dict_recupera_campos_customizados():
    resultado = _parsear_medidas_para_dict(
        "LARGURA: 50MM\nESPESSURA: 5\nOBSERVAÇÃO: Ajuste final"
    )

    assert resultado["largura"] == "50"
    assert resultado["custom_fields"] == [
        {"label": "ESPESSURA", "value": "5"},
        {"label": "OBSERVAÇÃO", "value": "Ajuste final"},
    ]
