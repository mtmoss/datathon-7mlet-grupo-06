# Plano LGPD — OfferExp

Plano de proteção de dados alinhado à LGPD (Lei 13.709/2018). O projeto usa
**dados sintéticos**, sem PII real; este plano descreve como o sistema trataria
dados pessoais se operasse em produção.

## Base legal e finalidade

- **Finalidade:** personalizar ofertas e mensagens em canais digitais, melhorando
  a experiência e a conversão.
- **Base legal (em produção):** legítimo interesse ou consentimento, conforme o
  caso; decisões sensíveis com revisão humana.
- **No datathon:** dados sintéticos; não há titular real.

## Minimização de dados

- Usar apenas features necessárias à decisão; nada de identificador direto.
- `subject_key` é sintético (não é CPF nem ID real).
- Features de contexto são agregadas e não identificáveis.

## Atributos protegidos

- A base Bank Marketing contém atributos demográficos (idade, profissão, estado
  civil, escolaridade). **Não são usados para discriminar**; o enunciado proíbe
  usar idade, gênero ou raça com esse fim.
- Monitoramento de fairness verifica exposição entre segmentos.

## Mapeamento de identificadores

| Dado | Classificação | Tratamento |
|---|---|---|
| `subject_key` | pseudônimo sintético | sem ligação a pessoa real |
| segmento, canal, propensão | contexto agregado | não identificável |
| atributos demográficos | sensível em produção | não usar para discriminar |

## Política de logs e telemetria

- Logs de decisão guardam `decision_id`, política, braço e reason codes — **sem PII**.
- O assistente remove PII (e-mail, CPF) da saída (guardrail).
- Telemetria (latência, custo) não contém dado pessoal.

## Ciclo de retenção

- Logs de decisão e eventos: retenção mínima necessária para auditoria e retreino;
  expurgo programado após o período definido.
- Artefatos de modelo versionados; dados brutos não são misturados a dados reais.

## Resposta a incidentes

1. Detecção (alertas de acesso indevido, vazamento, anomalia).
2. Contenção (revogar credenciais via Key Vault, isolar serviço).
3. Avaliação de impacto e notificação conforme a LGPD, se aplicável.
4. Correção e registro de lições aprendidas.

## Segurança (apoio)

- Segredos no **Azure Key Vault**; acesso por **Managed Identity** (sem senha).
- RBAC com menor privilégio; criptografia em repouso e em trânsito.
- Humano no loop para decisões sensíveis.
