"""Testes das politicas e da simulacao (Etapa 3)."""

import pandas as pd

from datathon_offerexp import evaluation as ev
from datathon_offerexp.policies import (
    ContextualThompson,
    FixedArm,
    ThompsonSampling,
    UCB1,
)

CTX = {"segment": "novo", "channel": "app", "base_propensity": 0.1}


def test_fixed_arm_nao_aprende() -> None:
    pol = FixedArm("educacao_financeira")
    pol.update("oferta_deposito", 1.0, CTX)  # deve ser ignorado
    assert pol.select(CTX) == "educacao_financeira"


def test_thompson_aprende_o_melhor_braco() -> None:
    pol = ThompsonSampling(seed=1)
    # recompensa so para um braco -> greedy deve aponta-lo
    for _ in range(50):
        pol.update("simulador_credito", 1.0, CTX)
        pol.update("sem_oferta", 0.0, CTX)
    assert pol.greedy(CTX) == "simulador_credito"


def test_ucb1_joga_cada_braco_no_cold_start() -> None:
    pol = UCB1()
    escolhidos = set()
    for _ in range(len(pol.arms)):
        arm = pol.select(CTX)
        escolhidos.add(arm)
        pol.update(arm, 0.0, CTX)
    assert escolhidos == set(pol.arms)


def test_contextual_isola_segmentos() -> None:
    pol = ContextualThompson(seed=2)
    novo = {"segment": "novo"}
    recorrente = {"segment": "recorrente"}
    for _ in range(40):
        pol.update("educacao_financeira", 1.0, novo)
        pol.update("simulador_credito", 1.0, recorrente)
    assert pol.greedy(novo) == "educacao_financeira"
    assert pol.greedy(recorrente) == "simulador_credito"


def _mini_events() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "event_id": [f"e{i}" for i in range(20)],
            "occurred_at": pd.date_range("2026-01-01", periods=20, freq="h").astype(str),
            "segment": ["novo"] * 20,
            "channel": ["app"] * 20,
            "base_propensity": [0.2] * 20,
        }
    )


def test_simulacao_metrica_coerente() -> None:
    res = ev.run_simulation(FixedArm("educacao_financeira"), _mini_events(), delayed=False)
    assert res.n == 20
    assert 0 <= res.total_reward <= 20
    assert len(res.reward_curve) == 20
    assert res.exploration_rate == 0.0  # baseline nunca explora
