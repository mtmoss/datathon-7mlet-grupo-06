# System Card — Plataforma OfferExp

## Escopo do sistema

Plataforma de experimentação adaptativa que decide qual oferta apresentar a cada
cliente elegível, aprende com as recompensas e mantém auditoria. Inclui um
assistente com LLM (RAG) para explicar decisões. Ambiente **sintético/educacional**,
com humano no loop. Não executa ofertas reais.

## Fluxo de decisão

1. `POST /decide` recebe o contexto (segmento, canal, propensão).
2. A política champion (do registro) escolhe o melhor braço elegível.
3. Resposta com `reason_codes`, versão da política e `decision_id`.
4. Decisão gravada em log auditável (`reports/decision_log.jsonl`).
5. Impressões e recompensas (atrasadas) realimentam o retreino.
6. Assistente (RAG) explica decisões e recupera políticas sintéticas.

## Dependências

- Internas: `policies`, `policy_store`, `lifecycle`, `evaluation`, `assistant`.
- Tracking: MLflow (SQLite local / PostgreSQL no Azure).
- LLM: Claude (Anthropic) no desenvolvimento; Azure AI Foundry no alvo de produção.
- Alvo de nuvem: Azure (ver `docs/architecture-azure.md`).

## Guardrails

| Guardrail | O que faz |
|---|---|
| Suitability | oferta direta não vai para cliente "novo" (golden set adversarial) |
| Elegibilidade | só braços disponíveis no contexto entram na decisão |
| Exploração mínima | mantém aprendizado sem gastar tráfego demais |
| Approval gate | promoção de política exige aprovação humana |
| Assistente — entrada | recusa injeção de prompt e pedidos de conselho financeiro |
| Assistente — saída | remove PII (e-mail, CPF) da resposta |
| Log auditável | toda decisão registra justificativa e versão |

## Cenários de risco

| Risco | Descrição | Mitigação |
|---|---|---|
| **Reward hacking** | otimizar só clique pode ferir conversão/suitability | recompensa principal = conversão; fairness e suitability monitorados |
| **Manipulação do contexto** | entrada adversarial para forçar um braço | validação de contrato (422/400); contexto restrito |
| **Abuso do assistente** | injeção de prompt, extração de dados | guardrail de entrada/saída; só responde sobre políticas sintéticas |
| **Violação de suitability** | oferta inadequada a um segmento | regra de suitability + golden set adversarial + revisão humana |
| **Drift silencioso** | política degrada sem aviso | monitoramento de PSI e recompensa, gatilho de retreino |

## Plano de monitoramento

- Drift (PSI > 0,2) em contexto e recompensa → gatilho de retreino.
- Conversão, regret, exploração e fairness de exposição.
- Latência, disponibilidade e custo (Azure Monitor / App Insights).
- Uso do assistente (tokens, recusas, latência).

## Plano de revisão periódica

- Revisão do System Card a cada mudança relevante de escopo e, no mínimo, mensal.
- Responsável: dono do sistema (a autora). Revisado junto ao Model Card.
