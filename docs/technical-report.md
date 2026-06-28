# Relatório Técnico — OfferExp

Plataforma de Experimentação Adaptativa em Ofertas Financeiras — Datathon Fase 5,
MLET7 (Grupo 06). Documento de até ~10 páginas; pode ser exportado para PDF.

## 1. Problema

Uma instituição financeira digital precisa decidir, em cada canal, qual oferta,
mensagem ou próximo passo apresentar a cada cliente elegível. Regras fixas e testes
A/B longos desperdiçam tráfego e demoram a reagir. O objetivo é uma plataforma que
**aprende sozinha** qual a melhor decisão, equilibrando exploração e explotação,
com governança, auditoria e segurança.

A diferença estrutural: num teste A/B, um humano decide o vencedor no fim; num
**multi-armed bandit**, o próprio sistema ajusta a decisão a cada recompensa.

## 2. Base de dados

Base factual: **Bank Marketing** (Kaggle/UCI), 41.188 registros (2008–2010), alvo
binário de conversão (assinar depósito). Descartamos `duration` (vazamento
temporal: só é conhecida após o contato). Mantivemos `unknown` como categoria.
Conversão real: 11,3% (base desbalanceada). Detalhe em `data/kaggle/README.md`,
`docs/data-dictionary.md` e `reports/data-quality.md`.

## 3. Enriquecimento sintético

Sobre a base, criamos a camada de experimentação (semente fixa, 8.000 eventos,
30 dias):

- **4 braços:** sem_oferta, educacao_financeira, simulador_credito, oferta_deposito.
- **Contexto:** segmento (novo/recorrente/reativado, derivado do histórico), canal
  (app/web/email) e propensão base (regressão logística sobre os dados reais).
- **Recompensa:** probabilidade de conversão por braço, ajustada por
  segmento e canal — de modo que **o melhor braço depende do contexto**.
- **Funil com atraso:** clique (~1,5h) → jornada (~12h) → conversão (~7,5 dias).

O melhor braço por segmento: novo→educação, recorrente→simulador, reativado→oferta
direta. Detalhe em `reports/data-generation.md`.

## 4. Modelagem como multi-armed bandit

Implementamos (em `src/datathon_offerexp/policies.py`):

- **Baselines** (controle, não aprendem): braço fixo ingênuo e melhor braço histórico.
- **Thompson Sampling** (Beta-Bernoulli): bandit bayesiano.
- **UCB1**: referência da família **Nilos-UCB**.
- **Thompson contextual** (proposta): um Thompson por segmento.

Cold-start tratado com prior Beta(1,1) (Thompson) e round-robin inicial (UCB1).
Delayed rewards tratados com janela de atribuição de 7 dias na simulação.

## 5. Comparação quantitativa

Avaliação offline (8.000 eventos, recompensa com atraso de 7 dias):

| Política | Conversão | Regret | Exploração |
|---|---:|---:|---:|
| baseline_naive | 11,9% | 414,7 | 0% |
| baseline_best | 16,3% | 97,0 | 0% |
| thompson | 15,1% | 183,7 | 43,8% |
| ucb1 | 12,6% | 359,1 | 76,6% |
| **thompson_contextual** | **15,7%** | 130,7 | 30,5% |

Sem atraso, a política contextual sobe para **16,4%** e supera o baseline forte
(16,3%), com regret menor (69 vs 97). O atraso é o principal limitador. Golden set:
**90,5%** de aprovação (21 casos); as falhas são casos onde o canal muda o ótimo —
limitação documentada. Sensibilidade entre 5 sementes: 15,2% ± 0,2 (estável).
Detalhe em `docs/algorithmic-strategy.md` e `reports/offline-evaluation.md`.

## 6. Serviço e auditoria

API FastAPI (`/decide`) recebe o contexto e devolve a oferta, com `reason_codes`,
versão da política e `decision_id`. Toda decisão é gravada em log auditável.
Contrato e tratamento de erro em `docs/api-contract.md`. A política é carregada de
um artefato versionado (`models/policy-vN.json`), treinado fora do serviço.

## 7. Arquitetura-alvo Azure

Exclusivamente Azure (ver `docs/architecture-azure.md`): Container Apps (API e
jobs), Blob/Data Lake (dados/artefatos/logs), PostgreSQL (MLflow), Event Hubs
(eventos), Azure AI Search + AI Foundry (assistente RAG), Azure Monitor/App
Insights (observabilidade), Entra ID + Managed Identity + Key Vault + RBAC
(segurança). Escolha guiada por simplicidade e custo baixo ocioso.

## 8. Ciclo MLOps

Champion-challenger com critério objetivo (lift ≥ 0,3 pp), **aprovação humana**
obrigatória, versionamento (registro) e rollback. Demonstração executada:
`policy-v2` (retreino com dados completos) promovido com **+1,8 pp**; `policy-v3`
(segmento+canal) **rejeitado** pelo gate por superajuste. Monitoramento de drift
via PSI (> 0,2 dispara retreino). Rastreio no MLflow. Detalhe em
`reports/retraining-approval-plan.md` e `reports/observability-plan.md`.

## 9. Assistente (RAG)

Assistente com Claude (Anthropic) que explica decisões e recupera políticas
sintéticas por busca TF-IDF, com guardrails de entrada (injeção/conselho
financeiro) e saída (PII). Em produção, o modelo seria o Azure AI Foundry.

## 10. Governança

Model Card, System Card e Plano LGPD completos (`docs/`). Riscos mapeados (reward
hacking, manipulação de contexto, abuso do assistente, violação de suitability),
com mitigação e plano de revisão periódica dos cards.

## 11. Limitações, riscos e hipóteses

- Dados de decisão 100% sintéticos: validam o método, não um banco real.
- Política contextual ignora canal e propensão fina; contexto mais fino
  superajusta segmentos pequenos.
- Recompensa atrasada reduz o ganho.
- Hipóteses de recompensa são sintéticas (multiplicadores definidos pelo grupo).

## 12. Trabalhos futuros

- Política contextual completa (LinUCB) usando canal e propensão.
- Off-policy evaluation (IPS/DR) além do replay simulado.
- RAG com busca vetorial (Azure AI Search) e avaliação (RAGAS).
- Deploy real em Azure com CI/CD de promoção.

## 13. Referências

- Moro, Cortez & Rita (2014). *A Data-Driven Approach to Predict the Success of
  Bank Telemarketing.* Decision Support Systems.
- Microsoft. *MLOps Maturity Model.*
- Thompson (1933); Auer et al. (2002, UCB).
- Lei 13.709/2018 (LGPD).
