# Relatório de Qualidade — Bank Marketing

Gerado a partir de `bank-additional-full.csv` via `notebooks/01-eda-e-baseline.ipynb`.
Base original: **41.188 linhas × 21 colunas**. Base processada: **41.188 × 20** (sem `duration`).

## Resumo

| Indicador | Valor |
|---|---|
| Registros | 41.188 |
| Valores nulos (NaN) | 0 (ausências vêm como `unknown`) |
| Linhas duplicadas | 12 |
| Taxa de conversão (`subscribed=1`) | **11,27%** (4.640 sim / 36.548 não) |
| Coluna de vazamento removida | `duration` |

## Achados principais

**1. Alvo muito desbalanceado.** Só 11,3% converte. Não dá para confiar em acurácia (um modelo
que sempre diz "não" acerta ~89%). Use AUC, precisão/recall e a recompensa simulada do bandit.
Ver `reports/figures/01_target_balance.png`.

**2. Ausências codificadas como `unknown`** (não são NaN). Contagem por coluna:

| Coluna | `unknown` | % |
|---|---:|---:|
| `default` | 8.597 | 20,9% |
| `education` | 1.731 | 4,2% |
| `housing` | 990 | 2,4% |
| `loan` | 990 | 2,4% |
| `job` | 330 | 0,8% |
| `marital` | 80 | 0,2% |

Decisão: manter `unknown` como categoria própria (não imputar). Em `default`, quase toda a base
é "no"/"unknown" — variável de baixo poder discriminante.

**3. `pdays=999` em 96,3% dos casos** (39.673 registros): a maioria nunca foi contatada antes.
A variável é quase constante; o sinal útil está mais em `poutcome` e `previous`.

**4. 12 linhas duplicadas.** Sem identificador de cliente, não dá para saber se são o mesmo
cliente ou coincidência. Mantidas (impacto desprezível: 0,03% da base). Documentado aqui.

**5. Sinais de conversão (para o baseline e os braços do bandit):**

- **Profissão** (`02_conv_by_job.png`): `student` e `retired` convertem bem acima da média; `blue-collar` e `services` abaixo.
- **Mês** (`03_conv_by_month.png`): mar, dez, set, out têm conversão muito alta; mai a mais baixa.
- **Contato** (`04_conv_by_contact.png`): `cellular` converte bem mais que `telephone`.
- **Campanha anterior** (`05_conv_by_poutcome.png`): `poutcome=success` é o sinal mais forte.
- **Idade** (`06_age_by_outcome.png`): conversão maior nos extremos (jovens e idosos).

## Vazamento — verificação

Única coluna pós-contato é `duration`, **removida** na base processada. As demais (incluindo os
indicadores macroeconômicos) são conhecidas **antes** ou **no momento** da decisão de oferta.
Logo, a base processada não contém vazamento temporal.

## Figuras

Todas em `reports/figures/`:

1. `01_target_balance.png` — balanceamento do alvo
2. `02_conv_by_job.png` — conversão por profissão
3. `03_conv_by_month.png` — conversão por mês
4. `04_conv_by_contact.png` — conversão por tipo de contato
5. `05_conv_by_poutcome.png` — conversão por resultado de campanha anterior
6. `06_age_by_outcome.png` — distribuição de idade por desfecho
