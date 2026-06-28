# Pitch Demo Day — OfferExp (até 10 min + 5 de perguntas)

Roteiro slide a slide, com tempo e fala-chave. Os slides devem ser versionados no
repositório em PDF ou formato aberto. Distribuição de papéis: solo (autora).

## Estrutura e tempo (10 min)

| # | Slide | Tempo | Mensagem-chave |
|---|---|---:|---|
| 1 | Capa | 0:30 | Plataforma que aprende sozinha qual oferta mostrar |
| 2 | Problema | 1:00 | Regra fixa e A/B desperdiçam tráfego e demoram a reagir |
| 3 | Abordagem | 1:00 | Multi-armed bandit: decide e aprende a cada recompensa |
| 4 | Dados | 1:00 | Base Kaggle real + camada sintética; sem vazamento |
| 5 | Resultados | 1:30 | Bandit vence baseline ingênuo; honesto sobre limites |
| 6 | Demo ao vivo | 2:00 | API decide + log + assistente explica |
| 7 | Ciclo MLOps | 1:00 | Champion-challenger, aprovação humana, rollback |
| 8 | Arquitetura Azure + FinOps | 1:00 | Só Azure; custo e escala |
| 9 | Riscos e governança | 0:30 | Cards, LGPD, guardrails |
| 10 | Impacto e fecho | 0:30 | ROI da personalização responsável |

## Falas por slide

**1. Capa.** "OfferExp: uma plataforma que decide, sozinha, qual oferta apresentar
a cada cliente — e aprende a cada resposta."

**2. Problema.** Regras fixas não personalizam; testes A/B longos desperdiçam
tráfego e demoram a reagir. Exemplo: cliente começa a usar cartão em farmácia — não
é doença, é um filho recém-nascido. O sistema precisa testar hipóteses, não chutar.

**3. Abordagem.** Multi-armed bandit equilibra explorar (testar o incerto) e
explotar (usar o que funciona). Implementamos Thompson Sampling contextual e UCB1
(Nilos-UCB), comparados a baselines.

**4. Dados.** Base Bank Marketing (real) como contexto; camada sintética de ofertas,
eventos e recompensas com atraso. Descartamos `duration` (vazamento). Tudo
versionado e documentado.

**5. Resultados.** Bandit vence o baseline ingênuo (11,9% → 15,7%). Sem atraso,
supera até o baseline forte (16,4% vs 16,3%). Somos honestos: o atraso de 7 dias é
o limitador, e mostramos isso com números.

**6. Demo ao vivo.** `make serve` + 3 chamadas: novo→educação, recorrente→simulador,
reativado→oferta. Mostrar o log auditável e o assistente explicando a decisão.
*Plano de contingência: gravação da demo + `decision_log.jsonl` de exemplo no repo.*

**7. Ciclo MLOps.** `make retrain`: challenger v2 promovido (+1,8 pp) com aprovação
humana; v3 rejeitado pelo gate (superajuste). Rollback testado. O gate protege a
produção.

**8. Arquitetura + FinOps.** Só Azure: Container Apps (escala a zero), Blob,
PostgreSQL, Event Hubs, AI Search + AI Foundry, Key Vault. Custo: Container Apps
quase zero ocioso; AI Search e PostgreSQL cobram parados; AI Foundry por token.
Escala: Container Apps e Event Hubs sobem sozinhos. ROI: ganho da personalização
sobre campanha estática supera o custo incremental.

**9. Riscos e governança.** Model Card, System Card, LGPD. Guardrails: suitability,
approval gate, e o assistente recusa injeção e remove PII. Riscos mapeados:
reward hacking, manipulação de contexto, abuso do assistente.

**10. Impacto.** Mais conversão com menos desperdício, de forma responsável e
auditável — humanos como revisores, não juízes de cada experimento.

## Cobertura dos critérios de apresentação

- **FinOps (ROI, custo, TCO):** slide 8 — custo qualitativo por serviço, o que
  cobra ocioso, ROI vs campanha estática, TCO (dev + operação + observabilidade +
  retreino + governança).
- **Arquitetura técnica:** slides 6–8 — diagrama, fronteiras de componentes,
  alternativas descartadas (AKS, Cosmos, Azure ML).
- **Escala e redução:** slide 8 — o que escala sozinho, o que é manual, o que cobra
  ocioso, sob baixa e alta carga.

## Perguntas prováveis (5 min)

- "Por que o bandit não vence o baseline forte com atraso?" → contexto dominado por
  um segmento + atraso; sem atraso ele vence. Honestidade > marketing.
- "Como evita discriminar?" → não usa atributos protegidos; monitora fairness.
- "Como uma nova política entra em produção?" → champion-challenger + aprovação
  humana + rollback (Etapa 7).
