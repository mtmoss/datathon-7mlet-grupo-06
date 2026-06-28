"""Testes da camada de dados (Etapa 1)."""

import pandas as pd

from datathon_offerexp import data_loader as dl


def _mini_raw() -> pd.DataFrame:
    """Mini base com o mesmo formato da original (sem precisar do CSV real)."""
    return pd.DataFrame(
        {
            "age": [30, 45],
            "job": ["admin.", "blue-collar"],
            "duration": [120, 0],  # coluna de vazamento
            "y": ["yes", "no"],
        }
    )


def test_remove_coluna_de_vazamento() -> None:
    df = dl.build_modeling_table(_mini_raw())
    assert "duration" not in df.columns


def test_cria_alvo_inteiro() -> None:
    df = dl.build_modeling_table(_mini_raw())
    assert "subscribed" in df.columns
    assert "y" not in df.columns
    assert df["subscribed"].tolist() == [1, 0]


def test_nao_altera_base_original() -> None:
    raw = _mini_raw()
    _ = dl.build_modeling_table(raw)
    assert "duration" in raw.columns  # a copia preserva a original
