# Roteiro do Vídeo Pitch (até 5 minutos)

O enunciado pede um **vídeo de até 5 min** que explique o problema de negócio, qual
modelo foi usado e **mostre a Etapa 5 rodando** (o modelo gerando uma recomendação).
Não precisa de dezenas de slides — o centro é a **demonstração**.

Prepare antes de gravar:

```bash
cd datathon-7mlet-grupo-06 && source .venv/bin/activate
make pipeline        # garante dados + política treinada
make serve           # deixe a API no ar (um terminal)
```

## Roteiro (5 min)

| Tempo | O que falar | O que mostrar na tela |
|---|---|---|
| 0:00–0:40 | **Problema.** Um banco digital precisa escolher qual oferta mostrar a cada cliente. Regra fixa e teste A/B desperdiçam tráfego e demoram a reagir. | 1 slide simples com o problema |
| 0:40–1:20 | **Abordagem.** Usamos um multi-armed bandit: ele testa ofertas e aprende com a resposta, equilibrando explorar e explotar. Comparamos com um baseline de regra fixa. | 1 slide: baseline vs bandit |
| 1:20–2:00 | **Dados.** Base real Bank Marketing (Kaggle) como contexto; a recompensa é sintética e **calibrada no `y` real**. Descartamos `duration` (vazamento). Somos honestos: não é uplift de produção. | notebook de EDA / tabela de dados |
| 2:00–3:40 | **DEMO (Etapa 5).** Mostrar a API decidindo ao vivo: 3 clientes, 3 recomendações diferentes por segmento, com a justificativa (reason codes) e o log auditável. | terminal: `make decide` + 2 chamadas `curl`; abrir `reports/decision_log.jsonl` |
| 3:40–4:20 | **Resultados + MLflow.** O bandit supera o baseline (11,9% → 15,7%). Experimentos rastreados no MLflow. | `mlflow ui` (opcional) ou a tabela do README |
| 4:20–5:00 | **Governança e fecho.** Guardrails (não oferta direta a cliente novo), humano no loop, nuvem AWS. Impacto: mais conversão, menos desperdício, de forma responsável. | 1 slide de fecho |

## Comandos da demo (para o trecho 2:00–3:40)

```bash
# cliente novo -> educação financeira
curl -s -X POST localhost:8000/decide -H "Content-Type: application/json" \
  -d '{"segment":"novo","channel":"app","base_propensity":0.10}'

# cliente recorrente -> simulador de crédito
curl -s -X POST localhost:8000/decide -H "Content-Type: application/json" \
  -d '{"segment":"recorrente","channel":"web","base_propensity":0.20}'

# cliente reativado -> oferta de depósito
curl -s -X POST localhost:8000/decide -H "Content-Type: application/json" \
  -d '{"segment":"reativado","channel":"app","base_propensity":0.35}'

# mostrar o log auditável gerado
tail -n 3 reports/decision_log.jsonl
```

## Dicas de gravação

- Grave a tela (OBS, QuickTime ou Loom). Fale com calma; 5 min passa rápido.
- **Ensaie a demo antes** e deixe os comandos prontos num arquivo para colar.
- **Plano B:** se a API falhar ao vivo, tenha uma gravação da demo pronta e o
  `decision_log.jsonl` de exemplo já no repositório.
- O peso maior é a **demo funcionando** (70% técnico) — priorize esse trecho.

## Perguntas prováveis (se houver arguição)

- "Por que essa base / esse algoritmo?" → `docs/decisoes-de-design.md`.
- "O bandit sempre vence?" → vence o baseline ingênuo; sem atraso vence o forte.
  Honestidade sobre limites.
- "Como evita discriminar / como escala?" → não usa atributos protegidos; AWS
  App Runner escala sozinho.
- "Como uma nova política entra em produção?" → champion-challenger + aprovação
  humana + rollback (`make retrain`).
