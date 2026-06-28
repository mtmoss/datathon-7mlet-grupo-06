"""Golden set: casos de avaliacao com criterio pass/fail (Etapa 4).

O golden set e um conjunto fixo de casos com a resposta esperada. Funciona como
uma "prova" da politica: rodamos a politica em cada caso e comparamos a decisao
com o esperado. Cobre casos tipicos, de borda, por segmento e adversariais.

A acao esperada de cada caso e o braco OTIMO segundo o modelo verdadeiro
(`synthetic.true_conv_prob`) naquele contexto. Assim o golden set vira uma barra
de qualidade: onde a politica falha, descobrimos suas limitacoes.
"""

from __future__ import annotations

import json
from pathlib import Path

from datathon_offerexp import synthetic as syn

GOLDEN_PATH = Path("data/golden_set/evaluation_cases.jsonl")


def _best_arm(p0: float, segment: str, channel: str) -> tuple[str, float]:
    probs = {a: syn.true_conv_prob(p0, a, segment, channel) for a in syn.ARMS}
    best = max(probs, key=probs.get)
    return best, round(probs[best], 4)


# Contextos curados para cobertura (segment, channel, base_propensity, categoria)
_CONTEXTS = [
    # tipicos (canal comum, propensao media) - um por segmento
    ("novo", "app", 0.10, "tipico"),
    ("novo", "web", 0.12, "tipico"),
    ("recorrente", "web", 0.18, "tipico"),
    ("recorrente", "email", 0.20, "tipico"),
    ("reativado", "app", 0.30, "tipico"),
    ("reativado", "web", 0.35, "tipico"),
    # cobertura por segmento x canal
    ("novo", "email", 0.10, "segmento"),
    ("recorrente", "app", 0.18, "segmento"),
    ("reativado", "email", 0.30, "segmento"),
    ("novo", "app", 0.05, "segmento"),
    ("recorrente", "web", 0.25, "segmento"),
    ("reativado", "app", 0.45, "segmento"),
    # bordas (propensao muito baixa / muito alta)
    ("novo", "app", 0.01, "borda"),
    ("novo", "web", 0.45, "borda"),
    ("recorrente", "app", 0.02, "borda"),
    ("reativado", "web", 0.60, "borda"),
    ("recorrente", "email", 0.50, "borda"),
    ("reativado", "app", 0.05, "borda"),
]

# Casos adversariais: a politica NAO deve escolher o braco proibido.
# (oferta direta irrita o cliente novo -> nao deve ser a decisao)
_ADVERSARIAL = [
    ("novo", "app", 0.10, "oferta_deposito"),
    ("novo", "web", 0.40, "oferta_deposito"),
    ("novo", "email", 0.08, "oferta_deposito"),
]


def build_golden_set(path: Path = GOLDEN_PATH) -> list[dict]:
    """Gera os casos do golden set e salva em JSONL."""
    cases: list[dict] = []
    i = 0
    for seg, ch, p0, cat in _CONTEXTS:
        best, p = _best_arm(p0, seg, ch)
        cases.append(
            {
                "case_id": f"gold_{i:03d}",
                "category": cat,
                "context": {"segment": seg, "channel": ch, "base_propensity": p0},
                "expected_action": best,
                "expected_reward": p,
                "rationale": f"Braco otimo p/ {seg}/{ch} no modelo verdadeiro.",
                "pass_criterion": "decisao == expected_action",
            }
        )
        i += 1
    for seg, ch, p0, forbidden in _ADVERSARIAL:
        cases.append(
            {
                "case_id": f"gold_{i:03d}",
                "category": "adversarial",
                "context": {"segment": seg, "channel": ch, "base_propensity": p0},
                "forbidden_action": forbidden,
                "rationale": f"{forbidden} prejudica o cliente {seg}; nao deve ser escolhido.",
                "pass_criterion": "decisao != forbidden_action",
            }
        )
        i += 1

    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for c in cases:
            fh.write(json.dumps(c, ensure_ascii=False) + "\n")
    return cases


def load_golden_set(path: Path = GOLDEN_PATH) -> list[dict]:
    with path.open(encoding="utf-8") as fh:
        return [json.loads(line) for line in fh if line.strip()]


def evaluate_golden(policy, cases: list[dict]) -> tuple[list[dict], float]:
    """Roda a politica em cada caso e marca pass/fail."""
    results = []
    passed = 0
    for c in cases:
        decision = policy.greedy(c["context"])
        if c["category"] == "adversarial":
            ok = decision != c["forbidden_action"]
        else:
            ok = decision == c["expected_action"]
        passed += int(ok)
        results.append({**c, "decision": decision, "passed": ok})
    return results, passed / len(cases)


if __name__ == "__main__":
    built = build_golden_set()
    print(f"Golden set: {len(built)} casos salvos em {GOLDEN_PATH}")
