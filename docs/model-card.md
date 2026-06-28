# Model Card — Política de Experimentação Adaptativa

## Identificação

- **Nome:** OfferExp — política adaptativa de ofertas (multi-armed bandit).
- **Tipo:** Thompson Sampling contextual (Beta-Bernoulli, um modelo por segmento).
- **Versão champion:** `policy-v2` (registro em `models/registry.json`).
- **Repositório:** `datathon-7mlet-grupo-06`.

## Dados

- **Base factual:** Bank Marketing (Kaggle / UCI), 41.188 registros, mai/2008–nov/2010.
  Coluna `duration` descartada (vazamento). Detalhe em `data/kaggle/README.md`.
- **Camada de experimentação (sintética):** 8.000 eventos, 4 braços, 3 segmentos,
  3 canais, recompensas com atraso. Detalhe em `reports/data-generation.md`.
- **Avaliação:** simulação offline + golden set (21 casos).

## Métricas (avaliação offline)

| Política | Conversão (atraso 7d) | Regret |
|---|---:|---:|
| baseline_naive (oferta fixa) | 11,9% | 414,7 |
| baseline_best (melhor braço fixo) | 16,3% | 97,0 |
| thompson (global) | 15,1% | 183,7 |
| **thompson_contextual (proposta)** | **15,7%** (16,4% sem atraso) | 130,7 |

- Golden set: **90,5%** de aprovação (falhas = casos onde o canal muda o ótimo).
- Champion-challenger: `policy-v2` promovido com **+1,8 pp** de conversão.

## Uso pretendido (intended use)

- Experimentação adaptativa de ofertas/mensagens/canais em ambiente **sintético e
  educacional**, com humano no loop.
- Apoiar a decisão de qual oferta apresentar, registrando justificativa auditável.

## Uso fora de escopo (out-of-scope)

- Aconselhamento financeiro individualizado.
- Execução real de ofertas ou integração com sistemas de produção reais.
- Uso com dados reais de clientes ou atributos protegidos para discriminar.

## Análise de fairness

- Exposição medida por segmento (`reports/fairness-review.md`). A política
  converge para um braço dominante por segmento; a exploração garante exposição
  mínima aos demais.
- `reativado` tem poucas amostras (255): estimativas menos confiáveis.

## Vieses conhecidos

- Base de 2008–2010 (contexto macroeconômico específico).
- Alvo desbalanceado (11,3% de conversão).
- Política agrupa só por segmento: ignora canal e propensão fina.

## Limitações técnicas

- Recompensa atrasada (7 dias) reduz o ganho sobre o baseline.
- Contexto mais fino (segmento+canal) superajusta segmentos pequenos.
- Dados de decisão 100% sintéticos: validam o método, não um banco real.

## Plano de revisão periódica

- **Cadência:** a cada retreino e, no mínimo, mensalmente.
- **Responsável:** dono da política (no datathon, a autora).
- **Gatilhos extra:** drift (PSI > 0,2), queda de conversão, mudança de catálogo.
- Revisão conjunta com o System Card.
