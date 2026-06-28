# Dicionário de Dados — Bank Marketing

Base: `bank-additional-full.csv` (41.188 linhas, separador `;`). 20 variáveis de entrada +
1 alvo. A coluna `duration` aparece no arquivo original, mas é **descartada** na base
processada por vazamento temporal.

## Dados do cliente

| # | Coluna | Tipo | Descrição | Valores |
|---|---|---|---|---|
| 1 | `age` | numérica | Idade do cliente | inteiro |
| 2 | `job` | categórica | Profissão | admin., blue-collar, entrepreneur, housemaid, management, retired, self-employed, services, student, technician, unemployed, unknown |
| 3 | `marital` | categórica | Estado civil | divorced, married, single, unknown |
| 4 | `education` | categórica | Escolaridade | basic.4y, basic.6y, basic.9y, high.school, illiterate, professional.course, university.degree, unknown |
| 5 | `default` | categórica | Tem crédito em inadimplência? | no, yes, unknown |
| 6 | `housing` | categórica | Tem financiamento imobiliário? | no, yes, unknown |
| 7 | `loan` | categórica | Tem empréstimo pessoal? | no, yes, unknown |

## Último contato da campanha atual

| # | Coluna | Tipo | Descrição | Valores |
|---|---|---|---|---|
| 8 | `contact` | categórica | Tipo de contato | cellular, telephone |
| 9 | `month` | categórica | Mês do último contato | jan … dec |
| 10 | `day_of_week` | categórica | Dia da semana do contato | mon, tue, wed, thu, fri |
| 11 | `duration` | numérica | **Duração da ligação (s) — DESCARTADA (vazamento)** | inteiro |

## Outros atributos da campanha

| # | Coluna | Tipo | Descrição | Observação |
|---|---|---|---|---|
| 12 | `campaign` | numérica | Nº de contatos nesta campanha (inclui o último) | — |
| 13 | `pdays` | numérica | Dias desde o último contato de campanha anterior | 999 = nunca contatado (96,3% dos casos) |
| 14 | `previous` | numérica | Nº de contatos antes desta campanha | — |
| 15 | `poutcome` | categórica | Resultado da campanha anterior | failure, nonexistent, success |

## Contexto socioeconômico (indicadores nacionais)

| # | Coluna | Tipo | Descrição |
|---|---|---|---|
| 16 | `emp.var.rate` | numérica | Taxa de variação do emprego (trimestral) |
| 17 | `cons.price.idx` | numérica | Índice de preços ao consumidor (mensal) |
| 18 | `cons.conf.idx` | numérica | Índice de confiança do consumidor (mensal) |
| 19 | `euribor3m` | numérica | Taxa Euribor 3 meses (diária) |
| 20 | `nr.employed` | numérica | Número de empregados (trimestral) |

## Alvo

| # | Coluna | Tipo | Descrição |
|---|---|---|---|
| 21 | `y` → `subscribed` | binária | Cliente assinou depósito a prazo? `yes`/`no` → `1`/`0` |

## Transformações na base processada (`data/processed/modeling_table.parquet`)

1. Remoção de `duration` (vazamento temporal).
2. `y` (texto) → `subscribed` (inteiro 0/1).
3. `unknown` mantido como categoria própria (sem imputação).
