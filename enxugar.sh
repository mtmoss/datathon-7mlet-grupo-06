#!/usr/bin/env bash
# Enxuga o repo para o escopo OFICIAL do Datathon (Fase 5).
# Cria a branch 'slim/escopo-oficial', aplica os cortes e commita.
# Voce revisa e faz merge SO se aprovar. Nada e perdido: a 'main' fica intacta.
#
# Uso:
#   1. abra o Terminal
#   2. cd "/Users/mtmoss/MT Claude/datathon-7mlet-grupo-06"
#   3. bash enxugar.sh
set -euo pipefail

echo ">> Enxugando o repo para o escopo oficial..."

# 0. checagens de seguranca
[ -d .git ] || { echo "ERRO: rode dentro da pasta do repositorio (a que tem a .git)."; exit 1; }
rm -f .git/index.lock 2>/dev/null || true

# 1. base limpa + branch nova (idempotente: pode rodar de novo)
git switch main
git branch -D slim/escopo-oficial 2>/dev/null || true
git switch -c slim/escopo-oficial

# 2. remover pastas e arquivos FORA do escopo oficial
#    docs/ infra/ reports/ inteiras (governanca extra do enunciado antigo)
git rm -rf -q docs infra reports data/synthetic_enrichment/policies
#    arquivo temporario do mlflow que nem devia estar versionado
git rm -f -q mlflow.db-journal 2>/dev/null || true
#    codigo avancado nao pedido: assistente RAG, drift, retreino + seus testes
git rm -f -q \
  src/datathon_offerexp/assistant.py \
  src/datathon_offerexp/drift.py \
  src/datathon_offerexp/lifecycle.py \
  src/tests/test_assistant.py \
  src/tests/test_drift.py \
  src/tests/test_lifecycle.py

# 3. README novo, consolidado e simples
cat > README.md <<'EOF_README'
# Datathon 7-MLET — Experimentação Adaptativa em Ofertas

Plataforma simples que decide, para cada cliente, **qual oferta apresentar** — e
**aprende** com as respostas usando um multi-armed bandit. Datathon da Fase 5
(MLET7 / FIAP). Grupo 06.

## Problema

Uma instituição financeira precisa decidir qual oferta mostrar a cada cliente.
Regra fixa não reage a mudanças. Um **multi-armed bandit** equilibra explorar
(testar o incerto) e explotar (usar o que funciona), aprendendo a cada resposta.

## Base de dados (Etapa 1)

- **Base Kaggle:** Bank Marketing — <https://www.kaggle.com/datasets/henriqueyamahata/bank-marketing>
- **Versão:** `bank-additional-full.csv` (41.188 linhas). Licença CC BY 4.0.
- **Vazamento:** descartamos `duration` (só é conhecida depois da ligação).
- **EDA e tratamento:** `notebooks/eda-e-baseline.ipynb`. Conversão real: 11,3%.

## Preparação da base (Etapa 2)

A base já tem a conversão (`y`). Usamos direto: features do cliente + alvo.
Para o bandit, criamos apenas os **braços de oferta** e a **recompensa simulada**
em `data/synthetic_enrichment/` (com semente fixa, `random_state=42`).

## Baseline vs. bandit (Etapa 3)

Simulação offline. O bandit **supera o baseline**. Registrado no MLflow (Etapa 7).

| Política | Conversão simulada | Regret |
|---|---:|---:|
| Baseline (regra fixa) | 11,9% | 414,7 |
| Thompson Sampling | 15,1% | 183,7 |

Métricas: conversão, recompensa, regret e exploração. Cold-start com prior Beta(1,1).

## Casos de teste (Etapa 4)

5 clientes de exemplo, a oferta recomendada e se fez sentido. Reproduzível com
`make examples`.

| # | Segmento | Canal | Oferta recomendada | Faz sentido? |
|---|---|---|---|---|
| 1 | novo | app | educacao_financeira | Sim — cliente novo responde a conteúdo |
| 2 | novo | email | educacao_financeira | Sim — mesmo perfil, outro canal |
| 3 | recorrente | web | simulador_credito | Sim — quem já interage usa o simulador |
| 4 | reativado | app | oferta_deposito | Sim — quem já converteu aceita a oferta |
| 5 | reativado | web | oferta_deposito | Sim — mesmo perfil, outro canal |

## Serviço de decisão (Etapa 5)

`POST /decide` recebe o contexto do cliente e devolve a oferta escolhida, com a
justificativa (`reason_codes`) e um `decision_id`. Sobe com `make serve`.

```bash
curl -X POST localhost:8000/decide -H "Content-Type: application/json" \
  -d '{"segment":"recorrente","channel":"web","base_propensity":0.2}'
```

## Arquitetura em nuvem (Etapa 6)

Para colocar em produção, usaríamos a **AWS**: a API em **AWS App Runner**
(escala sozinha, barato quando ocioso), os dados e artefatos no **Amazon S3**, e o
tracking do **MLflow** apoiado por um banco gerenciado (**Amazon RDS**). Segredos
ficariam no **AWS Secrets Manager**, sem senha no código.

## Ciclo MLOps (Etapa 7)

Experimentos rastreados no **MLflow local**: parâmetros e métricas da Etapa 3
(conversão e regret de cada política).

## Como rodar (local)

```bash
python3.11 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\activate
pip install -e ".[dev]"

make pipeline    # dados -> bandit -> avaliação
make examples    # os 5 casos de teste
make serve       # sobe a API em http://localhost:8000
make test        # testes
```

## Estrutura

```text
data/       base Kaggle, base processada, braços/recompensa, golden set
notebooks/  EDA e baseline
src/datathon_offerexp/  base, políticas, avaliação, API, log de decisão
```

## Limitações

- A recompensa é **simulada** (calibrada no `y` real da base). Valida o método,
  não um banco real. Sem deploy em produção.
- A política agrupa por segmento; contexto muito fino superajusta grupos pequenos.

## Checklist (entregáveis)

- [x] Repo público + `pyproject.toml` + instruções
- [x] Notebook de EDA com a base limpa e referenciada
- [x] Baseline e bandit implementados e comparados
- [x] 5 casos de teste com recomendações
- [x] API que retorna a recomendação
- [x] README com base, parágrafo de nuvem e execução local
- [x] Tracking no MLflow
- [ ] Vídeo de até 5 min
EOF_README

# 4. pyproject.toml sem a dependencia 'anthropic' (era so do assistente)
grep -v 'anthropic' pyproject.toml > pyproject.tmp && mv pyproject.tmp pyproject.toml

# 5. Makefile sem os alvos 'retrain' e 'assistant'
awk 'BEGIN{skip=0}
  /^retrain:/{skip=1}
  /^assistant:/{skip=1}
  skip==1 && /^$/{skip=0; next}
  skip==1{next}
  {print}' Makefile > Makefile.tmp && mv Makefile.tmp Makefile
sed 's/ retrain//; s/ assistant//' Makefile > Makefile.tmp && mv Makefile.tmp Makefile

# 6. ignorar saidas geradas em runtime (nao voltam pro repo)
grep -qxF 'reports/' .gitignore 2>/dev/null || echo 'reports/' >> .gitignore
grep -qxF 'models/'  .gitignore 2>/dev/null || echo 'models/'  >> .gitignore

# 7. commit na branch
git add -A
git commit -q -m "chore: enxuga repo para o escopo oficial do datathon

Remove governanca extra (docs/, infra/, reports/), o assistente RAG,
drift e retreino (lifecycle). Consolida a doc no README. Mantem EDA,
baseline, bandit, API, golden set, testes e MLflow."

echo ""
echo ">> PRONTO. Branch 'slim/escopo-oficial' criada e commitada."
echo ""
echo "   Revisar o que mudou:   git diff main..slim/escopo-oficial --stat"
echo "   Testar (recomendado):  pip install -e '.[dev]' && make test && make pipeline"
echo ""
echo "   Se APROVAR:  git switch main && git merge slim/escopo-oficial && git push"
echo "   Se NAO:      git switch main && git branch -D slim/escopo-oficial   (nada perdido)"
