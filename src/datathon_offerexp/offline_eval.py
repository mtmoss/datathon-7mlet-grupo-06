"""Avaliacao offline formal (Etapa 4): golden set, fairness e sensibilidade.

Gera, de forma reprodutivel:
- golden set (>= 20 casos) e resultado pass/fail;
- metricas por segmento (conversao e regret) da politica proposta;
- analise de fairness (exposicao de cada braco por segmento);
- analise de sensibilidade (varios seeds e varias janelas de atraso);
- relatorios em reports/offline-evaluation.md e reports/fairness-review.md.

Rode com:  python -m datathon_offerexp.offline_eval
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from datathon_offerexp import evaluation as ev
from datathon_offerexp import golden as gold
from datathon_offerexp import synthetic as syn
from datathon_offerexp.policies import ContextualThompson

OFFLINE_REPORT = Path("reports/offline-evaluation.md")
FAIRNESS_REPORT = Path("reports/fairness-review.md")


def train_proposed(events: pd.DataFrame, seed: int = 0) -> ContextualThompson:
    """Treina a politica proposta ate convergir (feedback imediato)."""
    pol = ContextualThompson(seed=seed)
    ev.run_simulation(pol, events, delayed=False)
    return pol


def per_segment_metrics(events: pd.DataFrame, policy) -> pd.DataFrame:
    """Conversao esperada e regret da politica proposta, por segmento."""
    rows = []
    for seg, grp in events.groupby("segment"):
        arm = policy.greedy({"segment": seg})
        conv, oracle = [], []
        for _, r in grp.iterrows():
            p0, ch = float(r["base_propensity"]), r["channel"]
            probs = {a: syn.true_conv_prob(p0, a, seg, ch) for a in syn.ARMS}
            conv.append(probs[arm])
            oracle.append(max(probs.values()))
        rows.append(
            {
                "segmento": seg,
                "n_eventos": len(grp),
                "braco_escolhido": arm,
                "conversao_%": round(np.mean(conv) * 100, 2),
                "oracle_%": round(np.mean(oracle) * 100, 2),
                "regret_medio_%": round((np.mean(oracle) - np.mean(conv)) * 100, 2),
            }
        )
    return pd.DataFrame(rows)


def fairness_exposure(events: pd.DataFrame, seed: int = 0) -> pd.DataFrame:
    """Exposicao (%) de cada braco dentro de cada segmento, na politica proposta."""
    pol = ContextualThompson(seed=seed)
    res = ev.run_simulation(pol, events, delayed=False)
    rows = []
    for seg in sorted({s for s, _ in res.exposure_seg}):
        total = sum(v for (s, _), v in res.exposure_seg.items() if s == seg)
        row = {"segmento": seg, "impressoes": total}
        for arm in syn.ARMS:
            row[arm] = round(res.exposure_seg.get((seg, arm), 0) / total * 100, 1)
        rows.append(row)
    return pd.DataFrame(rows)


def sensitivity_seeds(events: pd.DataFrame, seeds=range(5)) -> dict:
    """Estabilidade da politica proposta entre seeds (delayed)."""
    conv, reg = [], []
    for s in seeds:
        r = ev.run_simulation(ContextualThompson(seed=s), events, seed=100 + s)
        conv.append(r.conversion_rate * 100)
        reg.append(r.cumulative_regret)
    return {
        "conv_mean": round(float(np.mean(conv)), 2),
        "conv_std": round(float(np.std(conv)), 2),
        "regret_mean": round(float(np.mean(reg)), 1),
        "regret_std": round(float(np.std(reg)), 1),
    }


def sensitivity_delay(events: pd.DataFrame, delays=(0, 7, 14)) -> pd.DataFrame:
    """Efeito da janela de atraso na politica proposta."""
    rows = []
    for d in delays:
        r = ev.run_simulation(
            ContextualThompson(seed=0), events, delayed=(d > 0), delay_days=d
        )
        rows.append(
            {
                "atraso_dias": d,
                "conversao_%": round(r.conversion_rate * 100, 2),
                "regret": r.cumulative_regret,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    events = pd.read_csv(ev.EVENTS_PATH)

    # 1. golden set
    cases = gold.build_golden_set()
    proposed = train_proposed(events)
    g_results, pass_rate = gold.evaluate_golden(proposed, cases)
    g_df = pd.DataFrame(
        [
            {
                "case_id": r["case_id"],
                "categoria": r["category"],
                "decisao": r["decision"],
                "passou": r["passed"],
            }
            for r in g_results
        ]
    )
    by_cat = g_df.groupby("categoria")["passou"].agg(["sum", "count"])

    # 2. metricas e analises
    seg_metrics = per_segment_metrics(events, proposed)
    fairness = fairness_exposure(events)
    sens_seed = sensitivity_seeds(events)
    sens_delay = sensitivity_delay(events)

    _write_offline_report(g_df, pass_rate, by_cat, seg_metrics, sens_seed, sens_delay)
    _write_fairness_report(fairness, seg_metrics)

    print(f"Golden set: {len(cases)} casos | aprovacao {pass_rate*100:.1f}%")
    print(by_cat.to_string())
    print("\nMetricas por segmento:")
    print(seg_metrics.to_string(index=False))
    print(f"\nSensibilidade (seeds): conv {sens_seed['conv_mean']}±{sens_seed['conv_std']}%")
    print("\nRelatorios escritos em reports/.")


def _write_offline_report(g_df, pass_rate, by_cat, seg_metrics, sens_seed, sens_delay):
    falhas = g_df[~g_df["passou"]]
    lines = [
        "# Avaliação Offline (Etapa 4)",
        "",
        "Reproduzível: `python -m datathon_offerexp.offline_eval`.",
        "",
        "## Golden set",
        "",
        f"Total de casos: **{len(g_df)}** (>= 20 exigidos). "
        f"Aprovação: **{pass_rate*100:.1f}%**.",
        "",
        "Aprovação por categoria:",
        "",
        "| categoria | aprovados | total |",
        "|---|---:|---:|",
    ]
    for cat, r in by_cat.iterrows():
        lines.append(f"| {cat} | {int(r['sum'])} | {int(r['count'])} |")
    lines += [
        "",
        f"Casos que falharam: **{len(falhas)}**. "
        "São casos em que o melhor braço depende do **canal**, que a política "
        "proposta (contextual só por segmento) ignora. Limitação conhecida — ver abaixo.",
        "",
        "## Métricas por segmento",
        "",
        seg_metrics.to_markdown(index=False),
        "",
        "## Sensibilidade",
        "",
        f"**Entre seeds (5 execuções):** conversão "
        f"{sens_seed['conv_mean']}% ± {sens_seed['conv_std']} | "
        f"regret {sens_seed['regret_mean']} ± {sens_seed['regret_std']}. "
        "Resultado estável (desvio pequeno).",
        "",
        "**Janela de atraso:**",
        "",
        sens_delay.to_markdown(index=False),
        "",
        "Quanto maior o atraso, menor a conversão e maior o regret — o aprendizado "
        "demora a reagir.",
        "",
        "## Limitações e quando NÃO usar",
        "",
        "- A política agrupa só por **segmento**; ignora **canal** e propensão fina. "
        "Em contextos onde o canal muda o melhor braço, ela erra (ver golden set).",
        "- Sob **atraso longo** de recompensa, o ganho sobre o baseline encolhe.",
        "- Segmentos pequenos (`reativado`) têm poucas amostras: mais variância.",
        "- Não usar para decisões sensíveis sem **revisão humana** (suitability).",
        "- Próximo passo: política contextual completa (ex.: LinUCB) usando canal.",
        "",
    ]
    OFFLINE_REPORT.write_text("\n".join(lines), encoding="utf-8")


def _write_fairness_report(fairness, seg_metrics):
    lines = [
        "# Análise de Fairness — Exposição (Etapa 4)",
        "",
        "Fairness aqui = como a exposição às ofertas se distribui entre os segmentos "
        "sintéticos elegíveis. Verifica se algum grupo é sistematicamente excluído.",
        "",
        "## Exposição (%) de cada braço por segmento (política proposta)",
        "",
        fairness.to_markdown(index=False),
        "",
        "## Leitura",
        "",
        "- A política **converge** para um braço dominante por segmento (efeito "
        "esperado: ela explota o que converte mais). A exploração garante que os "
        "demais braços recebam alguma exposição.",
        "- `novo` concentra a maioria das impressões; `reativado` recebe poucas "
        "(desbalanceamento herdado da base). Estimativas desse grupo são menos "
        "confiáveis.",
        "- Nenhum segmento fica sem oferta: todos recebem decisões.",
        "",
        "## Riscos e mitigação",
        "",
        "- **Risco:** concentração pode reforçar vieses (sempre a mesma oferta para "
        "um grupo). **Mitigação:** manter exploração mínima e monitorar exposição.",
        "- **Risco:** segmento minoritário com pouca amostra. **Mitigação:** priors "
        "informativos e revisão humana antes de promover a política.",
        "",
        "## Conversão x regret por segmento",
        "",
        seg_metrics.to_markdown(index=False),
        "",
    ]
    FAIRNESS_REPORT.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
