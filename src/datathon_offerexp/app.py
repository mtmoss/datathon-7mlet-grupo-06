"""API de decisao (FastAPI) — Etapa 5.

Recebe um contexto e devolve a oferta escolhida pela politica, com justificativa
(reason codes), versao da politica e um registro auditavel gravado em log.

A politica e carregada de um artefato versionado (policy_store), nao treinada a
cada chamada. Servir = explotar a melhor oferta estimada (greedy).

Contrato resumido:
- POST /decide  -> body DecisionRequest  -> DecisionResponse
- GET  /health  -> {"status": "ok"}
- GET  /policy  -> metadados da politica carregada

Exemplo:
    curl -X POST localhost:8000/decide -H "Content-Type: application/json" \\
      -d '{"segment":"novo","channel":"app","base_propensity":0.1}'
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Literal

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from datathon_offerexp import policy_store
from datathon_offerexp.contracts import DecisionRecord
from datathon_offerexp.decision_log import append_decision
from datathon_offerexp.synthetic import ARMS

app = FastAPI(title="OfferExp - API de Decisao", version="1.0.0")

# politica carregada uma vez, na subida do servico
_POLICY, _POLICY_VERSION = policy_store.load_policy()


class DecisionRequest(BaseModel):
    """Contrato de ENTRADA. Tipos invalidos -> 422 automatico."""

    segment: Literal["novo", "recorrente", "reativado"]
    channel: Literal["app", "web", "email"]
    base_propensity: float = Field(ge=0.0, le=1.0)
    available_arms: list[str] | None = None
    event_id: str | None = None
    subject_key: str | None = None


class DecisionResponse(BaseModel):
    """Contrato de SAIDA."""

    decision_id: str
    event_id: str
    selected_arm: str
    policy_version: str
    mode: str
    exploration: bool
    estimated_conversion: float
    reason_codes: list[str]
    created_at: str


@app.get("/health")
def health() -> dict[str, str]:
    """Checagem de saude do servico."""
    return {"status": "ok"}


@app.get("/policy")
def policy_info() -> dict[str, object]:
    """Metadados da politica em uso."""
    return {"policy_version": _POLICY_VERSION, "arms": list(ARMS)}


@app.post("/decide", response_model=DecisionResponse)
def decide(req: DecisionRequest) -> DecisionResponse:
    """Recebe contexto e devolve a oferta escolhida + registro auditavel."""
    ctx = {
        "segment": req.segment,
        "channel": req.channel,
        "base_propensity": req.base_propensity,
    }

    # define o conjunto elegivel
    available = req.available_arms or list(ARMS)
    invalid = [a for a in available if a not in ARMS]
    if invalid:
        raise HTTPException(status_code=400, detail=f"Bracos invalidos: {invalid}")
    if not available:
        raise HTTPException(status_code=400, detail="Lista de bracos elegiveis vazia.")

    # decisao: melhor braco estimado entre os elegiveis (explotacao)
    arm = _POLICY.best_among(ctx, available)
    score = round(_POLICY.estimated_mean(ctx, arm), 4)

    reason_codes = (
        "elegivel",
        f"segmento:{req.segment}",
        f"canal:{req.channel}",
        "maior_score_estimado",
        f"score={score}",
    )

    record = DecisionRecord(
        decision_id=f"dec_{uuid.uuid4().hex[:12]}",
        event_id=req.event_id or f"evt_{uuid.uuid4().hex[:12]}",
        policy_version=_POLICY_VERSION,
        selected_arm=arm,
        mode="adaptive",
        exploration=False,
        reason_codes=reason_codes,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
    append_decision(record)  # log auditavel em reports/decision_log.jsonl

    return DecisionResponse(
        decision_id=record.decision_id,
        event_id=record.event_id,
        selected_arm=arm,
        policy_version=_POLICY_VERSION,
        mode="adaptive",
        exploration=False,
        estimated_conversion=score,
        reason_codes=list(reason_codes),
        created_at=record.created_at,
    )
