"""Camada de dados: carrega a base Kaggle, registra metadados e gera a base processada.

Responsabilidades (Etapa 1):
- carregar `bank-additional-full.csv` (separador ';');
- registrar fonte, versao e licenca da base;
- descartar a coluna de vazamento temporal (`duration`);
- mapear o alvo `y` (yes/no) para inteiro (1/0);
- salvar a base tratada em `data/processed/modeling_table.parquet`.

Por que descartar `duration`: a duracao da ligacao so e conhecida DEPOIS do
contato. Usa-la criaria vazamento (o modelo "espiaria o futuro"). O proprio
dataset recomenda descarta-la para um modelo realista (Moro et al., 2014).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import pandas as pd

# Caminhos padrao (relativos a raiz do repositorio)
RAW_PATH = Path("data/kaggle/bank-additional-full.csv")
PROCESSED_PATH = Path("data/processed/modeling_table.parquet")
METADATA_PATH = Path("data/processed/dataset_metadata.json")

# Coluna(s) que geram vazamento temporal / pos-decisao. NAO usar na modelagem.
LEAKAGE_COLUMNS: tuple[str, ...] = ("duration",)

# Nome do alvo no arquivo original.
RAW_TARGET = "y"
TARGET = "subscribed"  # alvo tratado (1 = assinou deposito, 0 = nao)


@dataclass(frozen=True)
class DatasetMetadata:
    """Procedencia da base, para rastreabilidade (exigido pela banca)."""

    name: str = "Bank Marketing (bank-additional-full)"
    source_kaggle: str = "https://www.kaggle.com/datasets/henriqueyamahata/bank-marketing"
    source_original: str = "http://archive.ics.uci.edu/ml/datasets/Bank+Marketing"
    citation: str = "Moro, Cortez & Rita (2014), Decision Support Systems"
    license: str = "CC BY 4.0 (uso para pesquisa, com citacao)"
    version: str = "bank-additional-full.csv (41188 registros, mai/2008-nov/2010)"
    separator: str = ";"
    leakage_columns_dropped: tuple[str, ...] = LEAKAGE_COLUMNS


def load_raw(path: Path = RAW_PATH) -> pd.DataFrame:
    """Carrega a base original sem alteracoes (separador ';')."""
    if not path.exists():
        raise FileNotFoundError(
            f"Base nao encontrada em {path}. "
            "Baixe do Kaggle (ver data/kaggle/README.md) e salve nessa pasta."
        )
    return pd.read_csv(path, sep=";")


def build_modeling_table(df_raw: pd.DataFrame) -> pd.DataFrame:
    """Gera a base tratada: remove vazamento e cria o alvo inteiro.

    Transformacoes (todas explicadas):
    1. remove `duration` (vazamento temporal);
    2. cria `subscribed` = 1 se y == 'yes', senao 0;
    3. remove o `y` textual original.

    Mantemos a categoria 'unknown' como classe propria (nao imputamos) e
    preservamos as demais colunas para a engenharia de features (Etapa 2).
    """
    df = df_raw.copy()

    # 1. vazamento
    for col in LEAKAGE_COLUMNS:
        if col in df.columns:
            df = df.drop(columns=col)

    # 2. alvo inteiro
    if RAW_TARGET in df.columns:
        df[TARGET] = (df[RAW_TARGET].str.strip().str.lower() == "yes").astype(int)
        df = df.drop(columns=RAW_TARGET)

    return df


def save_processed(
    df: pd.DataFrame,
    path: Path = PROCESSED_PATH,
    metadata: DatasetMetadata | None = None,
) -> None:
    """Salva a base tratada em Parquet e grava os metadados em JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)

    meta = metadata or DatasetMetadata()
    meta_dict = asdict(meta)
    meta_dict["n_rows"] = int(len(df))
    meta_dict["n_cols"] = int(df.shape[1])
    METADATA_PATH.write_text(json.dumps(meta_dict, ensure_ascii=False, indent=2))


def main() -> None:
    """Roda a pipeline de dados ponta a ponta e imprime um resumo."""
    df_raw = load_raw()
    df = build_modeling_table(df_raw)
    save_processed(df)

    taxa = df[TARGET].mean() * 100
    print(f"Base original : {df_raw.shape[0]} linhas x {df_raw.shape[1]} colunas")
    print(f"Base tratada  : {df.shape[0]} linhas x {df.shape[1]} colunas")
    print(f"Vazamento removido: {', '.join(LEAKAGE_COLUMNS)}")
    print(f"Taxa de conversao (subscribed=1): {taxa:.2f}%")
    print(f"Salvo em: {PROCESSED_PATH}")


if __name__ == "__main__":
    main()
