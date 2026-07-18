"""Teste dos 5 casos de exemplo (Etapa 4 simplificada)."""

from datathon_offerexp import examples
from datathon_offerexp.synthetic import ARMS


def test_cinco_casos_com_oferta_valida() -> None:
    rows = examples.build_cases()
    assert len(rows) == 5
    for r in rows:
        assert r["oferta"] in ARMS
        assert r["fez_sentido"]  # tem justificativa
        assert 0.0 <= r["score"] <= 1.0
