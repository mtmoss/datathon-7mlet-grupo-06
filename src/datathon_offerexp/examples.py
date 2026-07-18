"""Etapa 4 (simplificada): 5 clientes de exemplo com a oferta recomendada.

Mostra, para cada cliente, qual oferta o modelo recomendou e se a decisao faz
sentido. Reproduzivel:  python -m datathon_offerexp.examples
"""

from __future__ import annotations

from datathon_offerexp import policy_store
from datathon_offerexp.synthetic import ARMS

# 5 clientes de exemplo (contexto + descricao)
EXAMPLES = [
    ({"segment": "novo", "channel": "app", "base_propensity": 0.08}, "cliente novo, baixa propensao"),
    ({"segment": "novo", "channel": "email", "base_propensity": 0.12}, "cliente novo, via email"),
    ({"segment": "recorrente", "channel": "web", "base_propensity": 0.20}, "cliente que ja interage"),
    ({"segment": "reativado", "channel": "app", "base_propensity": 0.35}, "cliente que ja converteu"),
    ({"segment": "reativado", "channel": "web", "base_propensity": 0.45}, "reativado, alta propensao"),
]

# Justificativa de "fez sentido?" por oferta
RATIONALE = {
    "educacao_financeira": "sim - cliente novo responde a conteudo educativo",
    "simulador_credito": "sim - quem ja interage engaja com o simulador",
    "oferta_deposito": "sim - quem ja converteu aceita a oferta direta",
    "sem_oferta": "sim - nao vale a pena ofertar a este cliente",
}


def build_cases() -> list[dict]:
    """Roda a politica champion nos 5 clientes e devolve as recomendacoes."""
    policy, version = policy_store.load_policy()
    rows = []
    for i, (ctx, desc) in enumerate(EXAMPLES, 1):
        arm = policy.best_among(ctx, list(ARMS))
        rows.append(
            {
                "n": i,
                "descricao": desc,
                "segmento": ctx["segment"],
                "canal": ctx["channel"],
                "oferta": arm,
                "score": round(policy.estimated_mean(ctx, arm), 3),
                "fez_sentido": RATIONALE.get(arm, "-"),
                "policy_version": version,
            }
        )
    return rows


def main() -> None:
    rows = build_cases()
    print(f"Politica: {rows[0]['policy_version']}\n")
    print(f"{'#':<2} {'segmento':<11} {'canal':<6} {'oferta recomendada':<20} {'score':<6} fez sentido?")
    for r in rows:
        print(
            f"{r['n']:<2} {r['segmento']:<11} {r['canal']:<6} "
            f"{r['oferta']:<20} {r['score']:<6} {r['fez_sentido']}"
        )


if __name__ == "__main__":
    main()
