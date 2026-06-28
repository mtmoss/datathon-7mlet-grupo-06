"""Testes do log auditavel de decisoes (Etapa 5)."""

import json

from datathon_offerexp.contracts import DecisionRecord
from datathon_offerexp.decision_log import append_decision


def _record(decision_id: str) -> DecisionRecord:
    return DecisionRecord(
        decision_id=decision_id,
        event_id="evt_x",
        policy_version="policy-v1",
        selected_arm="educacao_financeira",
        mode="adaptive",
        exploration=False,
        reason_codes=("elegivel", "maior_score_estimado"),
        created_at="2026-06-28T20:00:00+00:00",
    )


def test_append_grava_linha_jsonl(tmp_path) -> None:
    log = tmp_path / "decision_log.jsonl"
    append_decision(_record("dec_1"), path=log)
    append_decision(_record("dec_2"), path=log)

    linhas = log.read_text(encoding="utf-8").strip().splitlines()
    assert len(linhas) == 2
    primeira = json.loads(linhas[0])
    assert primeira["decision_id"] == "dec_1"
    assert primeira["policy_version"] == "policy-v1"
    assert "maior_score_estimado" in primeira["reason_codes"]
