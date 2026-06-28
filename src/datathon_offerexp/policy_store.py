"""Armazenamento da politica treinada (artefato versionado).

A API nao treina a cada chamada. Em vez disso:
1. treinamos a politica uma vez (sobre os eventos sinteticos);
2. exportamos o estado aprendido para um JSON com uma VERSAO;
3. a API carrega esse artefato e serve decisoes.

Isso separa treino de serving e da um conceito claro de "versao de politica"
(que a Etapa 7 usa para promover/reverter modelos).
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

from datathon_offerexp import evaluation as ev
from datathon_offerexp import synthetic as syn
from datathon_offerexp.policies import ContextualThompson

POLICY_VERSION = "policy-v1"
MODELS_DIR = Path("models")
POLICY_PATH = MODELS_DIR / f"{POLICY_VERSION}.json"


def train_and_export(version: str = POLICY_VERSION, seed: int = 0) -> Path:
    """Treina a politica proposta e salva o artefato versionado."""
    events = pd.read_csv(ev.EVENTS_PATH)
    policy = ContextualThompson(seed=seed)
    ev.run_simulation(policy, events, delayed=False)  # treina ate convergir

    artifact = {
        "policy_version": version,
        "policy_type": "thompson_contextual",
        "arms": list(syn.ARMS),
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "n_events": int(len(events)),
        "state": policy.export(),
    }
    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    path = MODELS_DIR / f"{version}.json"
    path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
    return path


def load_policy(path: Path = POLICY_PATH) -> tuple[ContextualThompson, str]:
    """Carrega a politica treinada do artefato. Treina se ainda nao existir."""
    if not path.exists():
        train_and_export()
    artifact = json.loads(path.read_text(encoding="utf-8"))
    policy = ContextualThompson()
    policy.load(artifact["state"])
    return policy, artifact["policy_version"]


if __name__ == "__main__":
    out = train_and_export()
    print(f"Politica treinada e salva em {out}")
