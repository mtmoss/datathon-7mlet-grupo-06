"""Testes do golden set e da avaliacao offline (Etapa 4)."""

import pandas as pd

from datathon_offerexp import golden as gold
from datathon_offerexp import offline_eval as off
from datathon_offerexp.policies import FixedArm


def test_golden_tem_pelo_menos_20_casos(tmp_path) -> None:
    cases = gold.build_golden_set(tmp_path / "g.jsonl")
    assert len(cases) >= 20
    for c in cases:
        assert "context" in c and "segment" in c["context"]
        assert "pass_criterion" in c


def test_adversarial_reprova_braco_proibido(tmp_path) -> None:
    cases = gold.build_golden_set(tmp_path / "g.jsonl")
    adv = [c for c in cases if c["category"] == "adversarial"]
    assert adv  # existem casos adversariais
    # politica que sempre manda a oferta proibida deve falhar todos os adversariais
    results, _ = gold.evaluate_golden(FixedArm("oferta_deposito"), adv)
    assert all(not r["passed"] for r in results)


def test_evaluate_golden_retorna_taxa() -> None:
    cases = gold.load_golden_set() if gold.GOLDEN_PATH.exists() else gold.build_golden_set()
    _, rate = gold.evaluate_golden(FixedArm("educacao_financeira"), cases)
    assert 0.0 <= rate <= 1.0


def _mini_events() -> pd.DataFrame:
    segs = ["novo"] * 10 + ["recorrente"] * 6 + ["reativado"] * 4
    return pd.DataFrame(
        {
            "event_id": [f"e{i}" for i in range(20)],
            "occurred_at": pd.date_range("2026-01-01", periods=20, freq="h").astype(str),
            "segment": segs,
            "channel": ["app"] * 20,
            "base_propensity": [0.2] * 20,
        }
    )


def test_fairness_exposicao_soma_100() -> None:
    fair = off.fairness_exposure(_mini_events())
    arms_cols = [c for c in fair.columns if c not in ("segmento", "impressoes")]
    soma = fair[arms_cols].sum(axis=1)
    assert ((soma - 100).abs() < 1.0).all()  # cada segmento ~100%
