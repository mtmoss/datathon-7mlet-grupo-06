"""Politicas de decisao: baseline, Thompson Sampling, UCB1 e Thompson contextual.

Cada politica recebe um `context` (dict com segment, channel, base_propensity),
escolhe um braco com `select`, e aprende com `update` quando a recompensa chega.

Conceitos:
- baseline: regra fixa, NAO aprende (controle).
- Thompson Sampling: bandit bayesiano. Mantem uma crenca (distribuicao Beta) sobre
  a taxa de conversao de cada braco e sorteia dela -> explora o incerto.
- UCB1 (familia Nilos-UCB): escolhe por media + bonus de incerteza.
- Thompson contextual: um Thompson separado por segmento -> personaliza.

Cold-start (comeco sem dados):
- Thompson usa prior Beta(1,1) (sem conhecimento -> explora bastante).
- UCB1 joga cada braco uma vez antes de comparar.
"""

from __future__ import annotations

import math
from abc import ABC, abstractmethod

import numpy as np

from datathon_offerexp.synthetic import ARMS


class Policy(ABC):
    """Interface comum a todas as politicas."""

    name: str = "policy"

    @abstractmethod
    def select(self, context: dict) -> str:
        """Escolhe um braco dado o contexto."""

    def update(self, arm: str, reward: float, context: dict) -> None:
        """Aprende com a recompensa observada (0/1). Baseline ignora."""

    def greedy(self, context: dict) -> str:
        """Melhor braco segundo a estimativa atual (usado p/ medir exploracao)."""
        return self.select(context)


class FixedArm(Policy):
    """Baseline deterministico: sempre o mesmo braco. Nao aprende."""

    def __init__(self, arm: str, name: str = "baseline_fixo") -> None:
        self.arm = arm
        self.name = name

    def select(self, context: dict) -> str:
        return self.arm

    def greedy(self, context: dict) -> str:
        return self.arm


class ThompsonSampling(Policy):
    """Bandit Beta-Bernoulli (nao contextual)."""

    def __init__(self, arms: tuple[str, ...] = ARMS, seed: int = 0) -> None:
        self.name = "thompson"
        self.arms = arms
        self.rng = np.random.default_rng(seed)
        # prior Beta(1,1) para cada braco -> cold-start sem vies
        self.alpha = {a: 1.0 for a in arms}
        self.beta = {a: 1.0 for a in arms}

    def select(self, context: dict) -> str:
        samples = {a: self.rng.beta(self.alpha[a], self.beta[a]) for a in self.arms}
        return max(samples, key=samples.get)

    def update(self, arm: str, reward: float, context: dict) -> None:
        self.alpha[arm] += reward
        self.beta[arm] += 1.0 - reward

    def greedy(self, context: dict) -> str:
        means = {a: self.alpha[a] / (self.alpha[a] + self.beta[a]) for a in self.arms}
        return max(means, key=means.get)


class UCB1(Policy):
    """Upper Confidence Bound (referencia da familia Nilos-UCB)."""

    def __init__(self, arms: tuple[str, ...] = ARMS) -> None:
        self.name = "ucb1"
        self.arms = arms
        self.counts = {a: 0 for a in arms}
        self.values = {a: 0.0 for a in arms}  # media de recompensa
        self.total = 0

    def select(self, context: dict) -> str:
        # cold-start: joga cada braco uma vez
        for a in self.arms:
            if self.counts[a] == 0:
                return a
        ucb = {
            a: self.values[a] + math.sqrt(2 * math.log(self.total) / self.counts[a])
            for a in self.arms
        }
        return max(ucb, key=ucb.get)

    def update(self, arm: str, reward: float, context: dict) -> None:
        self.counts[arm] += 1
        self.total += 1
        n = self.counts[arm]
        self.values[arm] += (reward - self.values[arm]) / n

    def greedy(self, context: dict) -> str:
        return max(self.values, key=self.values.get)


class ContextualThompson(Policy):
    """Um Thompson Sampling por segmento -> a decisao depende do contexto."""

    def __init__(
        self,
        arms: tuple[str, ...] = ARMS,
        segments: tuple[str, ...] = ("novo", "recorrente", "reativado"),
        seed: int = 0,
    ) -> None:
        self.name = "thompson_contextual"
        self.models = {
            seg: ThompsonSampling(arms, seed=seed + i) for i, seg in enumerate(segments)
        }

    def _model(self, context: dict) -> ThompsonSampling:
        return self.models[context["segment"]]

    def select(self, context: dict) -> str:
        return self._model(context).select(context)

    def update(self, arm: str, reward: float, context: dict) -> None:
        self._model(context).update(arm, reward, context)

    def greedy(self, context: dict) -> str:
        return self._model(context).greedy(context)
