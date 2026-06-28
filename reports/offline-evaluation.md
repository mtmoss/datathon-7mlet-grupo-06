# Avaliação Offline (Etapa 4)

Reproduzível: `python -m datathon_offerexp.offline_eval`.

## Golden set

Total de casos: **21** (>= 20 exigidos). Aprovação: **90.5%**.

Aprovação por categoria:

| categoria | aprovados | total |
|---|---:|---:|
| adversarial | 3 | 3 |
| borda | 5 | 6 |
| segmento | 5 | 6 |
| tipico | 6 | 6 |

Casos que falharam: **2**. São casos em que o melhor braço depende do **canal**, que a política proposta (contextual só por segmento) ignora. Limitação conhecida — ver abaixo.

## Métricas por segmento

| segmento   |   n_eventos | braco_escolhido     |   conversao_% |   oracle_% |   regret_medio_% |
|:-----------|------------:|:--------------------|--------------:|-----------:|-----------------:|
| novo       |        6939 | educacao_financeira |         13.31 |      13.31 |             0    |
| reativado  |         255 | oferta_deposito     |         89.48 |      89.48 |             0    |
| recorrente |         806 | simulador_credito   |         23.95 |      24.48 |             0.53 |

## Sensibilidade

**Entre seeds (5 execuções):** conversão 15.17% ± 0.17 | regret 136.6 ± 12.3. Resultado estável (desvio pequeno).

**Janela de atraso:**

|   atraso_dias |   conversao_% |   regret |
|--------------:|--------------:|---------:|
|             0 |         16.43 |    69.2  |
|             7 |         15.73 |   130.74 |
|            14 |         14.76 |   213.36 |

Quanto maior o atraso, menor a conversão e maior o regret — o aprendizado demora a reagir.

## Limitações e quando NÃO usar

- A política agrupa só por **segmento**; ignora **canal** e propensão fina. Em contextos onde o canal muda o melhor braço, ela erra (ver golden set).
- Sob **atraso longo** de recompensa, o ganho sobre o baseline encolhe.
- Segmentos pequenos (`reativado`) têm poucas amostras: mais variância.
- Não usar para decisões sensíveis sem **revisão humana** (suitability).
- Próximo passo: política contextual completa (ex.: LinUCB) usando canal.
