"""Testes da API de decisao (Etapa 5)."""

from fastapi.testclient import TestClient

from datathon_offerexp.app import app
from datathon_offerexp.synthetic import ARMS

client = TestClient(app)


def test_health() -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_decide_devolve_decisao_completa() -> None:
    r = client.post(
        "/decide",
        json={"segment": "recorrente", "channel": "web", "base_propensity": 0.2},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["selected_arm"] in ARMS
    assert body["policy_version"]
    assert body["reason_codes"]  # justificativa presente
    assert body["decision_id"].startswith("dec_")


def test_decide_segmento_invalido_422() -> None:
    r = client.post(
        "/decide",
        json={"segment": "inexistente", "channel": "web", "base_propensity": 0.2},
    )
    assert r.status_code == 422


def test_decide_propensao_fora_intervalo_422() -> None:
    r = client.post(
        "/decide",
        json={"segment": "novo", "channel": "app", "base_propensity": 1.5},
    )
    assert r.status_code == 422


def test_decide_braco_invalido_400() -> None:
    r = client.post(
        "/decide",
        json={
            "segment": "novo",
            "channel": "app",
            "base_propensity": 0.1,
            "available_arms": ["braco_que_nao_existe"],
        },
    )
    assert r.status_code == 400


def test_decide_respeita_bracos_disponiveis() -> None:
    r = client.post(
        "/decide",
        json={
            "segment": "novo",
            "channel": "app",
            "base_propensity": 0.1,
            "available_arms": ["sem_oferta", "simulador_credito"],
        },
    )
    assert r.json()["selected_arm"] in ("sem_oferta", "simulador_credito")
