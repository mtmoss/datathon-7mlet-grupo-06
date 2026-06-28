"""Avaliacao offline das politicas por simulacao (Etapa 3/4).

Como funciona a simulacao (replay simulado):
1. Percorremos os eventos em ordem de tempo.
2. Em cada evento, a politica escolhe um braco a partir do contexto.
3. A recompensa e sorteada do modelo "verdadeiro" (synthetic.true_conv_prob).
4. A recompensa so volta para a politica DEPOIS de uma janela de atribuicao
   (delayed rewards) -> a politica aprende com atraso, como na vida real.

Metricas calculadas por politica:
- recompensa total / taxa de conversao;
- regret acumulado (quanto deixou de ganhar vs. o melhor braco possivel);
- taxa de exploracao (quantas vezes nao escolheu o braco que julgava melhor).

Os resultados sao logados no MLflow (rastreabilidade, Nivel 2 de maturidade).
"""

from __future__ import annotations

import heapq
from dataclasses import dataclass, field
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

from datathon_offerexp import synthetic as syn  # noqa: E402
from datathon_offerexp.policies import (  # noqa: E402
    ContextualThompson,
    FixedArm,
    Policy,
    ThompsonSampling,
    UCB1,
)

EVENTS_PATH = syn.EVENTS_PATH
ATTRIBUTION_DELAY_DAYS = 7  # janela ate considerar a recompensa conhecida
FIG_DIR = Path("reports/figures")

# paleta do projeto
CINZA, AZUL, ROSA, AMARELO = "#48494D", "#00ACF1", "#EE008B", "#FFF300"
COLORS = {
    "baseline_naive": CINZA,
    "baseline_best": "#9aa0a6",
    "thompson": AZUL,
    "ucb1": AMARELO,
    "thompson_contextual": ROSA,
}


@dataclass
class SimResult:
    """Resultado agregado de uma simulacao."""

    name: str
    n: int
    total_reward: int
    conversion_rate: float
    cumulative_regret: float
    exploration_rate: float
    reward_curve: list[int] = field(default_factory=list)
    regret_curve: list[float] = field(default_factory=list)


def _context(row: pd.Series) -> dict:
    return {
        "segment": row["segment"],
        "channel": row["channel"],
        "base_propensity": float(row["base_propensity"]),
    }


def _true_probs(row: pd.Series) -> dict[str, float]:
    """Prob. verdadeira de conversao de cada braco no contexto do evento."""
    p0, seg, ch = float(row["base_propensity"]), row["segment"], row["channel"]
    return {a: syn.true_conv_prob(p0, a, seg, ch) for a in syn.ARMS}


def run_simulation(
    policy: Policy,
    events: pd.DataFrame,
    seed: int = 123,
    delayed: bool = True,
) -> SimResult:
    """Roda uma politica sobre o fluxo de eventos e devolve as metricas."""
    rng = np.random.default_rng(seed)
    events = events.sort_values("occurred_at").reset_index(drop=True)
    times = pd.to_datetime(events["occurred_at"])
    delay = pd.Timedelta(days=ATTRIBUTION_DELAY_DAYS)

    queue: list[tuple] = []  # heap (arrival_time, ordem, arm, reward, context)
    counter = 0
    cum_reward = 0
    cum_regret = 0.0
    explore = 0
    reward_curve: list[int] = []
    regret_curve: list[float] = []

    for i, row in events.iterrows():
        now = times[i]
        # 1. entrega recompensas atrasadas que ja venceram
        while queue and queue[0][0] <= now:
            _, _, arm_done, rew_done, ctx_done = heapq.heappop(queue)
            policy.update(arm_done, rew_done, ctx_done)

        ctx = _context(row)
        probs = _true_probs(row)

        # 2. decisao
        arm = policy.select(ctx)
        if arm != policy.greedy(ctx):
            explore += 1

        # 3. recompensa verdadeira e regret
        reward = int(rng.random() < probs[arm])
        cum_reward += reward
        cum_regret += max(probs.values()) - probs[arm]

        # 4. aprendizado (com ou sem atraso)
        if delayed:
            heapq.heappush(queue, (now + delay, counter, arm, reward, ctx))
            counter += 1
        else:
            policy.update(arm, reward, ctx)

        reward_curve.append(cum_reward)
        regret_curve.append(round(cum_regret, 3))

    n = len(events)
    return SimResult(
        name=policy.name,
        n=n,
        total_reward=cum_reward,
        conversion_rate=round(cum_reward / n, 4),
        cumulative_regret=round(cum_regret, 2),
        exploration_rate=round(explore / n, 4),
        reward_curve=reward_curve,
        regret_curve=regret_curve,
    )


def best_logged_arm(events: pd.DataFrame) -> str:
    """Melhor braco historico segundo os dados logados (para o baseline forte)."""
    rewards = pd.read_csv(syn.REWARDS_PATH)
    conv = set(rewards[rewards["reward_type"] == "conversion"]["event_id"])
    ev = events.assign(conv=events["event_id"].isin(conv))
    return str(ev.groupby("chosen_arm")["conv"].mean().idxmax())


def build_policies(events: pd.DataFrame, seed: int = 0) -> list[Policy]:
    """Monta a lista de politicas comparadas."""
    best = best_logged_arm(events)
    return [
        FixedArm("oferta_deposito", name="baseline_naive"),
        FixedArm(best, name="baseline_best"),
        ThompsonSampling(seed=seed),
        UCB1(),
        ContextualThompson(seed=seed),
    ]


def _plot(results: list[SimResult]) -> None:
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update(
        {"font.family": "monospace", "figure.facecolor": "white", "axes.facecolor": "white"}
    )
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    for r in results:
        ax.plot(r.reward_curve, label=r.name, color=COLORS.get(r.name, CINZA), lw=1.6)
    ax.set_title("Recompensa acumulada (conversoes)")
    ax.set_xlabel("eventos")
    ax.set_ylabel("conversoes")
    ax.legend(fontsize=7)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "07_cumulative_reward.png", bbox_inches="tight")
    plt.close()

    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    for r in results:
        ax.plot(r.regret_curve, label=r.name, color=COLORS.get(r.name, CINZA), lw=1.6)
    ax.set_title("Regret acumulado (menor = melhor)")
    ax.set_xlabel("eventos")
    ax.set_ylabel("regret")
    ax.legend(fontsize=7)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "08_cumulative_regret.png", bbox_inches="tight")
    plt.close()


def _plot_delay(delayed: SimResult, immediate: SimResult) -> None:
    """Compara aprendizado com e sem atraso (demonstra delayed rewards)."""
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    ax.plot(immediate.regret_curve, label="imediato", color=AZUL, lw=1.8)
    ax.plot(delayed.regret_curve, label="atraso 7 dias", color=ROSA, lw=1.8)
    ax.set_title("Efeito do atraso no aprendizado (thompson_contextual)")
    ax.set_xlabel("eventos")
    ax.set_ylabel("regret acumulado")
    ax.legend(fontsize=8)
    plt.tight_layout()
    plt.savefig(FIG_DIR / "09_delayed_vs_immediate.png", bbox_inches="tight")
    plt.close()


def _log_mlflow(results: list[tuple[SimResult, str]]) -> None:
    import os

    try:
        import mlflow
    except ImportError:
        print("(MLflow nao instalado - pulando tracking)")
        return
    # SQLite e o backend recomendado (o backend de arquivos foi descontinuado)
    mlflow.set_tracking_uri(os.environ.get("MLFLOW_TRACKING_URI", "sqlite:///mlflow.db"))
    mlflow.set_experiment("etapa3-bandits")
    for r, mode in results:
        with mlflow.start_run(run_name=f"{r.name}__{mode}"):
            mlflow.log_params({"policy": r.name, "mode": mode, "n_events": r.n})
            mlflow.log_metrics(
                {
                    "total_reward": r.total_reward,
                    "conversion_rate": r.conversion_rate,
                    "cumulative_regret": r.cumulative_regret,
                    "exploration_rate": r.exploration_rate,
                }
            )


def _table(results: list[SimResult]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "politica": r.name,
                "conversoes": r.total_reward,
                "conversao_%": round(r.conversion_rate * 100, 2),
                "regret": r.cumulative_regret,
                "exploracao_%": round(r.exploration_rate * 100, 2),
            }
            for r in results
        ]
    ).sort_values("conversao_%", ascending=False)


def main() -> None:
    """Roda a comparacao completa: simula todas as politicas e reporta."""
    events = pd.read_csv(EVENTS_PATH)

    # 1. comparacao principal (cenario realista: recompensa com atraso)
    results = [run_simulation(p, events, delayed=True) for p in build_policies(events)]
    print("== Comparacao de politicas (recompensa com atraso de 7 dias) ==")
    print(_table(results).to_string(index=False))
    _plot(results)

    # 2. demonstracao do efeito de delayed rewards na politica proposta
    ctx_delayed = run_simulation(ContextualThompson(seed=0), events, delayed=True)
    ctx_immediate = run_simulation(ContextualThompson(seed=0), events, delayed=False)
    _plot_delay(ctx_delayed, ctx_immediate)
    print("\n== Efeito do atraso (thompson_contextual) ==")
    print(f"  imediato : conversao {ctx_immediate.conversion_rate*100:.2f}% | "
          f"regret {ctx_immediate.cumulative_regret}")
    print(f"  atraso 7d: conversao {ctx_delayed.conversion_rate*100:.2f}% | "
          f"regret {ctx_delayed.cumulative_regret}")

    # 3. tracking
    tagged = [(r, "delayed") for r in results]
    tagged += [(ctx_immediate, "immediate")]
    _log_mlflow(tagged)
    print("\nFiguras salvas em reports/figures/ (07, 08, 09).")


if __name__ == "__main__":
    main()
