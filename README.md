# Datathon 7-MLET — Experimentação Adaptativa em Ofertas Financeiras

Plataforma de **experimentação adaptativa** (multi-armed bandits) que decide, para
cada cliente elegível, qual oferta apresentar — e **aprende** com as respostas.
Datathon da Fase 5 (MLET7 / FIAP). Repositório: **`datathon-7mlet-grupo-06`** (Grupo 06).

## Visão do problema

Uma instituição financeira digital precisa decidir, em cada canal, qual oferta,
mensagem ou próximo passo apresentar a cada cliente. Regras fixas e testes A/B
longos desperdiçam tráfego e demoram a reagir. Um **multi-armed bandit** equilibra
explorar (testar o incerto) e explotar (usar o que funciona), aprendendo a cada
recompensa — sem congelar a decisão em regras estáticas.

## Base de dados (Etapa 1)

- **Base Kaggle:** Bank Marketing — <https://www.kaggle.com/datasets/henriqueyamahata/bank-marketing>
- **Versão:** `bank-additional-full.csv` (41.188 registros, 2008–2010). Licença CC BY 4.0.
- **Vazamento:** descartamos a coluna `duration` (só conhecida após o contato).
- **EDA:** `notebooks/01-eda-e-baseline.ipynb`. Detalhes em `data/kaggle/README.md`
  e `reports/data-quality.md`. Conversão real: 11,3% (base desbalanceada).

## Como rodar (local, Mac/Linux)

```bash
python3.11 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
cp .env.example .env                 # (opcional) preencha ANTHROPIC_API_KEY p/ o assistente

make pipeline    # fluxo ponta a ponta: dados -> bandits -> avaliação -> política
make test        # 41 testes
make serve       # sobe a API em http://localhost:8000  (doc em /docs)
make decide      # exemplo de decisão (outro terminal)
```

| Comando | O que faz |
|---|---|
| `make pipeline` | roda o fluxo completo (1 comando) |
| `make retrain` | ciclo MLOps: champion-challenger, aprovação, rollback |
| `make serve` / `make decide` | sobe a API / faz uma chamada de exemplo |
| `make assistant` | assistente explica uma decisão |
| `make test` / `make lint` | testes / estilo |

## Baseline vs. política adaptativa (Etapa 3)

Comparação na simulação offline (8.000 eventos, recompensa com atraso de 7 dias). O
bandit **supera o baseline** — evidência registrada no MLflow (Etapa 7).

| Política | Conversão simulada | Regret |
|---|---:|---:|
| Baseline (regra fixa) | 11,9% | 414,7 |
| Thompson (global) | 15,1% | 183,7 |
| UCB1 (família Nilos-UCB) | 12,6% | 359,1 |
| **Thompson contextual (proposta)** | **15,7%** | 130,7 |

Sem atraso, a política contextual chega a **16,4%**. Métricas: recompensa, regret,
exploração e conversão; cold-start (prior Beta(1,1)) e delayed rewards tratados.
Detalhe em `docs/algorithmic-strategy.md`.

> A recompensa é **sintética e calibrada** pelo `y` real da base (via regressão
> logística) — não é uplift de produção. Declarado honestamente.

## Casos de teste — recomendações (Etapa 4)

A política treinada, para 5 clientes de exemplo:

| # | Segmento | Canal | Oferta recomendada | Score | Faz sentido? |
|---|---|---|---|---:|---|
| 1 | novo | app | educacao_financeira | 0,14 | Sim — cliente novo responde a conteúdo educativo |
| 2 | novo | email | educacao_financeira | 0,14 | Sim — mesmo perfil, canal diferente |
| 3 | recorrente | web | simulador_credito | 0,23 | Sim — quem já interage responde ao simulador |
| 4 | recorrente | app | simulador_credito | 0,23 | Sim — consistente por segmento |
| 5 | reativado | app | oferta_deposito | 0,92 | Sim — quem já converteu aceita a oferta direta |

Golden set completo (21 casos, com pass/fail) em `data/golden_set/evaluation_cases.jsonl`
e `reports/offline-evaluation.md`.

## Serviço de decisão (Etapa 5)

`POST /decide` recebe o contexto e devolve a oferta escolhida, com `reason_codes`
(justificativa), `policy_version` e um `decision_id`. Cada decisão vira uma linha no
log auditável (`reports/decision_log.jsonl`). Contrato completo em
`docs/api-contract.md`.

```bash
curl -X POST localhost:8000/decide -H "Content-Type: application/json" \
  -d '{"segment":"recorrente","channel":"web","base_propensity":0.2}'
```

## Arquitetura em nuvem (Etapa 6)

Alvo em **Amazon Web Services (AWS)**. A API roda em **AWS App Runner** (autoscaling,
barato ocioso); os dados, artefatos e logs ficam no **Amazon S3**; o **MLflow** usa
**Amazon RDS for PostgreSQL**; eventos entram por **Amazon Kinesis**; o assistente usa
**Amazon OpenSearch** (busca vetorial) + **Amazon Bedrock** (que roda o **mesmo Claude**
do desenvolvimento, sem troca de modelo); observabilidade no **Amazon CloudWatch + X-Ray**.

Segurança sem senha no código: segredos no **AWS Secrets Manager**, acessados por
**IAM Role**, com permissões de menor privilégio (least privilege). Diagrama e plano de
deploy (opcionais) em `docs/architecture-aws.md` e `infra/aws/`.

## Ciclo MLOps (Etapa 7)

Experimentos rastreados no **MLflow** (params + métricas da Etapa 3). Vai além do
mínimo: champion-challenger com critério de promoção, **aprovação humana**,
versionamento e rollback, mais monitoramento de drift (PSI). Detalhe em
`reports/retraining-approval-plan.md`.

## Estrutura e documentação

```text
data/       base Kaggle, base processada, enriquecimento sintético, golden set, políticas
notebooks/  EDA e baseline
src/datathon_offerexp/  contratos, políticas, avaliação, serviço, ciclo de vida, assistente
reports/    qualidade, geração, avaliação, fairness, retreino, observabilidade
docs/       cards, arquitetura, estratégia, contrato da API, pitch, decisões de design
infra/aws/  arquitetura e plano de deploy
```

Documentos de diferencial: `docs/model-card.md`, `docs/system-card.md`,
`docs/lgpd-plan.md`, `docs/technical-report.md`, `docs/decisoes-de-design.md`.

## Limitações

- Dados de decisão e recompensa são **sintéticos** (calibrados no `y` real); validam
  o método, não um banco real. Sem deploy em produção.
- A política agrupa por segmento; contexto mais fino superajusta segmentos pequenos.
- Recompensa atrasada reduz o ganho sobre o baseline.
- O assistente apoia a análise humana; não dá conselho financeiro (guardrails).

## Checklist (entregáveis)

- [x] Repo público + `pyproject.toml` + instruções de execução
- [x] Notebook de EDA com a base Kaggle limpa e referenciada
- [x] Baseline e política adaptativa implementados e comparados
- [x] Casos de teste com recomendações (5 no README + golden set de 21)
- [x] Código executável que retorna a recomendação (API FastAPI)
- [x] README com link da base, parágrafo de nuvem e execução local
- [x] Tracking de experimentos no MLflow
- [ ] Vídeo de até 5 min (roteiro em `docs/demo-day-pitch.md`)
