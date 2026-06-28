# Análise de Fairness — Exposição (Etapa 4)

Fairness aqui = como a exposição às ofertas se distribui entre os segmentos sintéticos elegíveis. Verifica se algum grupo é sistematicamente excluído.

## Exposição (%) de cada braço por segmento (política proposta)

| segmento   |   impressoes |   sem_oferta |   educacao_financeira |   simulador_credito |   oferta_deposito |
|:-----------|-------------:|-------------:|----------------------:|--------------------:|------------------:|
| novo       |         6939 |          2   |                  77.2 |                18.7 |               2.1 |
| reativado  |          255 |          2   |                   6.7 |                 0.4 |              91   |
| recorrente |          806 |          5.1 |                   9.1 |                48.5 |              37.3 |

## Leitura

- A política **converge** para um braço dominante por segmento (efeito esperado: ela explota o que converte mais). A exploração garante que os demais braços recebam alguma exposição.
- `novo` concentra a maioria das impressões; `reativado` recebe poucas (desbalanceamento herdado da base). Estimativas desse grupo são menos confiáveis.
- Nenhum segmento fica sem oferta: todos recebem decisões.

## Riscos e mitigação

- **Risco:** concentração pode reforçar vieses (sempre a mesma oferta para um grupo). **Mitigação:** manter exploração mínima e monitorar exposição.
- **Risco:** segmento minoritário com pouca amostra. **Mitigação:** priors informativos e revisão humana antes de promover a política.

## Conversão x regret por segmento

| segmento   |   n_eventos | braco_escolhido     |   conversao_% |   oracle_% |   regret_medio_% |
|:-----------|------------:|:--------------------|--------------:|-----------:|-----------------:|
| novo       |        6939 | educacao_financeira |         13.31 |      13.31 |             0    |
| reativado  |         255 | oferta_deposito     |         89.48 |      89.48 |             0    |
| recorrente |         806 | simulador_credito   |         23.95 |      24.48 |             0.53 |
