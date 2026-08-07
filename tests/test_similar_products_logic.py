import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from routes import _score_related_product_relationship


def _produto(grupo, codigo, aplicacoes):
    return SimpleNamespace(
        grupo=grupo,
        codigo=codigo,
        conversoes="",
        fornecedor="",
        aplicacoes=aplicacoes,
    )


def _app(veiculo, ano, motor, montadora=""):
    return SimpleNamespace(veiculo=veiculo, ano=ano, motor=motor, montadora=montadora)


def test_similar_product_requires_same_group_and_vehicle_overlap():
    selected = _produto(
        "FILTRO",
        "ABC-123",
        [_app("UNO", "2010-2012", "1.0")],
    )

    same_group_same_apps = _produto(
        "FILTRO",
        "ABC-124",
        [_app("UNO", "2010-2012", "1.0")],
    )

    same_group_different_apps = _produto(
        "FILTRO",
        "ABC-125",
        [_app("PALIO", "2010-2012", "1.0")],
    )

    same_group_partial_overlap = _produto(
        "FILTRO",
        "ABC-127",
        [_app("UNO", "2011-2014", "1.0")],
    )

    different_group_same_apps = _produto(
        "VELA",
        "ABC-126",
        [_app("UNO", "2010-2012", "1.0")],
    )

    same_group_without_vehicle_data = _produto(
        "FILTRO",
        "ABC-128",
        [_app("", "2010-2012", "1.0")],
    )

    assert _score_related_product_relationship(selected, same_group_same_apps) > 0
    assert _score_related_product_relationship(selected, same_group_partial_overlap) > 0
    assert _score_related_product_relationship(selected, same_group_different_apps) == 0
    assert _score_related_product_relationship(selected, different_group_same_apps) == 0
    assert _score_related_product_relationship(selected, same_group_without_vehicle_data) == 0