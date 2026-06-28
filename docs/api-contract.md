# Contrato da API de Decisão (Etapa 5)

Serviço FastAPI que recebe um contexto e devolve a oferta escolhida, com
justificativa, versão da política e registro auditável.

Subir o serviço:

```bash
make serve            # ou: uvicorn datathon_offerexp.app:app --reload
```

Documentação interativa automática em `http://localhost:8000/docs`.

## Endpoints

| Método | Rota | Descrição |
|---|---|---|
| GET | `/health` | saúde do serviço |
| GET | `/policy` | versão e braços da política carregada |
| POST | `/decide` | recebe contexto, devolve decisão |

## POST /decide — Entrada

```json
{
  "segment": "novo | recorrente | reativado",
  "channel": "app | web | email",
  "base_propensity": 0.10,
  "available_arms": ["sem_oferta", "educacao_financeira", "simulador_credito", "oferta_deposito"],
  "event_id": "opcional",
  "subject_key": "opcional"
}
```

- `segment`, `channel`: obrigatórios; valor fora da lista → **422**.
- `base_propensity`: float entre 0 e 1; fora do intervalo → **422**.
- `available_arms`: opcional; se omitido, usa todos. Braço inexistente → **400**.

## POST /decide — Saída

```json
{
  "decision_id": "dec_3f9a1c2b7e44",
  "event_id": "evt_8b1d...",
  "selected_arm": "simulador_credito",
  "policy_version": "policy-v1",
  "mode": "adaptive",
  "exploration": false,
  "estimated_conversion": 0.2395,
  "reason_codes": ["elegivel", "segmento:recorrente", "canal:web",
                   "maior_score_estimado", "score=0.2395"],
  "created_at": "2026-06-28T20:00:00+00:00"
}
```

## Exemplo de chamada (Mac)

```bash
curl -X POST localhost:8000/decide \
  -H "Content-Type: application/json" \
  -d '{"segment":"recorrente","channel":"web","base_propensity":0.2}'
```

## Tratamento de erro

| Situação | Código | Resposta |
|---|---|---|
| segmento/canal inválido | 422 | erro de validação do pydantic |
| `base_propensity` fora de [0,1] | 422 | erro de validação |
| braço inexistente em `available_arms` | 400 | `{"detail": "Bracos invalidos: [...]"}` |
| lista de braços vazia | 400 | `{"detail": "Lista de bracos elegiveis vazia."}` |

## Log auditável

Cada decisão é gravada em `reports/decision_log.jsonl` (uma linha por decisão),
com `decision_id`, `event_id`, `policy_version`, `selected_arm`, `mode`,
`exploration`, `reason_codes` e `created_at`. Permite auditar **o que** foi
decidido, **por qual política** e **por quê**.
