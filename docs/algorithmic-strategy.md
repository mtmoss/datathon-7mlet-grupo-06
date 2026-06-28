# Estratégia Algorítmica (Etapa 3)

Comparação entre políticas simples (baseline) e multi-armed bandits, com métricas
de recompensa, regret, exploração e conversão. Código: `src/datathon_offerexp/`
(`policies.py`, `evaluation.py`). Resultados rastreados no MLflow.

## Políticas comparadas

| Política | Tipo | Aprende? | Descrição |
|---|---|---|---|
| `baseline_naive` | fixa | não | sempre `oferta_deposito` (regra de negócio ingênua) |
| `baseline_best` | fixa | não | sempre o melhor braço histórico (`educacao_financeira`) |
| `thompson` | bandit | sim | Beta-Bernoulli, não contextual |
| `ucb1` | bandit | sim | Upper Confidence Bound (referência **Nilos-UCB**) |
| `thompson_contextual` | bandit contextual | sim | um Thompson por segmento (**política proposta**) |

## Como o contexto entra na decisão

A política proposta mantém um Thompson Sampling separado **por segmento** (novo,
recorrente, reativado). Assim ela aprende o melhor braço de cada grupo, em vez de
um único braço global. É isso que um baseline fixo não consegue fazer.

## Cold-start (começar sem dados)

- **Thompson**: prior Beta(1,1) por braço. Sem histórico, a crença é uniforme e a
  política explora bastante; vai ficando confiante conforme observa recompensas.
- **UCB1**: joga cada braço uma vez antes de comparar (round-robin inicial).

## Delayed rewards (recompensa com atraso)

A conversão só é confirmada após uma **janela de atribuição de 7 dias**. Na
simulação, a recompensa entra numa fila e só atualiza a política quando "vence".
Logo, decisões iniciais são tomadas com pouca informação — exatamente o desafio
real. Tratamos isso deixando a política aprender de forma incremental conforme as
recompensas chegam.

## Resultados — cenário realista (recompensa com atraso de 7 dias)

8.000 eventos. Conversão = recompensa principal. Regret = quanto se deixou de
ganhar vs. o melhor braço possível em cada contexto (menor é melhor).

| Política | Conversões | Conversão % | Regret | Exploração % |
|---|---:|---:|---:|---:|
| baseline_best | 1.304 | **16,30** | 97,0 | 0 |
| thompson_contextual | 1.258 | 15,73 | 130,7 | 30,5 |
| thompson | 1.210 | 15,12 | 183,7 | 43,8 |
| ucb1 | 1.010 | 12,63 | 359,1 | 76,6 |
| baseline_naive | 952 | 11,90 | 414,7 | 0 |

Leitura:

- Os bandits **superam folgado** o baseline ingênuo (11,9% → 15,7%).
- O baseline forte (`baseline_best`) é difícil de bater **neste horizonte curto
  com atraso**, porque ele já "sabe" o melhor braço global — que coincide com o
  melhor braço do segmento `novo` (87% dos eventos).
- O **UCB1** sofre mais com o atraso: o bônus de confiança o faz explorar demais
  quando o feedback demora. O Thompson lida melhor com incerteza aqui.

## Resultados — efeito do atraso (política proposta)

| Modo | Conversão % | Regret |
|---|---:|---:|
| feedback imediato | **16,43** | 69,2 |
| atraso de 7 dias | 15,73 | 130,7 |

Com feedback imediato, o `thompson_contextual` (16,43%) **supera** o baseline forte
(16,30%) e quase **dobra** a vantagem em regret (69 vs 97). Ou seja: o ganho do
bandit existe e aparece claramente quando a recompensa chega rápido. O atraso é o
principal limitador — o que justifica, na arquitetura, usar sinais intermediários
(clique, jornada) e janelas de atribuição bem desenhadas.

## Justificativa da escolha

**Política proposta: `thompson_contextual`.** Melhor desempenho entre as que
aprendem, menor regret, personaliza por segmento e trata cold-start de forma
natural (priors). O UCB1 fica como referência da família UCB (**Nilos-UCB**), com
trade-off documentado: explora demais sob feedback atrasado.

## Figuras

- `reports/figures/07_cumulative_reward.png` — recompensa acumulada por política.
- `reports/figures/08_cumulative_regret.png` — regret acumulado por política.
- `reports/figures/09_delayed_vs_immediate.png` — efeito do atraso no aprendizado.

## Reproduzir

```bash
python -m datathon_offerexp.synthetic      # garante os dados (Etapa 2)
python -m datathon_offerexp.evaluation     # roda a comparação + MLflow
mlflow ui --backend-store-uri sqlite:///mlflow.db   # ver experimentos
```
