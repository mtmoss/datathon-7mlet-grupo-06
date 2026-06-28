# Base Kaggle — Bank Marketing

Base factual do projeto. Não é editada; transformações geram `data/processed/`.

## Fonte e versão

- **Base escolhida:** Bank Marketing (arquivo `bank-additional-full.csv`).
- **Link Kaggle:** https://www.kaggle.com/datasets/henriqueyamahata/bank-marketing
- **Origem original (UCI):** http://archive.ics.uci.edu/ml/datasets/Bank+Marketing
- **Versão usada:** `bank-additional-full.csv` — 41.188 registros, ordenados por data (mai/2008 a nov/2010).
- **Citação obrigatória:** Moro, S., Cortez, P., & Rita, P. (2014). *A Data-Driven Approach to Predict the Success of Bank Telemarketing.* Decision Support Systems. doi:10.1016/j.dss.2014.03.001
- **Licença:** disponível publicamente para pesquisa, mediante citação (CC BY 4.0).

## Como baixar (Mac)

Opção A — manual:

1. Abra o link do Kaggle acima e faça login.
2. Clique em **Download** e descompacte o `.zip`.
3. Copie `bank-additional-full.csv` e `bank-additional-names.txt` para esta pasta (`data/kaggle/`).

Opção B — Kaggle CLI:

```bash
pip install kaggle
# coloque seu kaggle.json em ~/.kaggle/ (https://www.kaggle.com/settings -> Create New Token)
kaggle datasets download -d henriqueyamahata/bank-marketing -p data/kaggle --unzip
```

> O CSV **não** é versionado no Git (ver `.gitignore`): a base é grande e a banca pede apenas
> que o download seja documentado, não que o arquivo seja commitado.

## Por que esta base

Campanhas de telemarketing bancário com alvo binário de **conversão** (assinar depósito a
prazo). Encaixa direto no problema de **decisão de oferta**: cada cliente é um contexto, e o
objetivo é prever/otimizar a propensão a converter — base para o baseline e para a política
adaptativa (bandits).

## Alvo

- `y` (original) → tratado como `subscribed` (1 = assinou depósito, 0 = não).

## Colunas usadas

19 variáveis de entrada (dados do cliente, último contato e contexto socioeconômico) + alvo.
Detalhe completo em `docs/data-dictionary.md`.

## Coluna descartada (vazamento temporal)

- **`duration`** (duração da ligação, em segundos): **descartada**.
  - Só é conhecida **depois** do contato. O próprio dataset alerta: se `duration=0` então
    `y="no"`, e a duração só existe após a ligação. Usá-la criaria vazamento (o modelo
    "espiaria o futuro") e geraria um modelo irrealista.
  - O descarte é feito em código (`src/datathon_offerexp/data_loader.py`, `LEAKAGE_COLUMNS`).

## Limitações e vieses conhecidos

- **Desbalanceamento:** só 11,3% de conversão — exige métricas além de acurácia.
- **Valores `unknown`:** várias categóricas têm a classe `unknown` (ver relatório de qualidade);
  tratadas como classe própria, não imputadas.
- **`pdays=999`:** 96,3% dos clientes nunca foram contatados antes — variável quase constante.
- **Período fixo (2008–2010):** contexto macroeconômico específico (crise); limita generalização.
- **Sem identificador de cliente:** não dá para rastrear o mesmo cliente entre registros.
