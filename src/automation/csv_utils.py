"""
Utilitários para leitura e validação de arquivos CSV.

Centraliza a lógica de parsing para ser testada independentemente do Playwright.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Iterator


def read_csv(path: str | Path) -> list[dict[str, str]]:
    """
    Lê um arquivo CSV e retorna uma lista de dicionários.

    Cada dicionário mapeia cabeçalho → valor da linha.
    Linhas completamente vazias são ignoradas.

    Args:
        path: Caminho para o arquivo CSV.

    Returns:
        Lista de dicionários com os dados do CSV.

    Raises:
        FileNotFoundError: Se o arquivo não existir.
        ValueError: Se o CSV não tiver cabeçalho.
    """
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"Arquivo CSV não encontrado: {path}")

    rows: list[dict[str, str]] = []

    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)

        if reader.fieldnames is None:
            raise ValueError(f"CSV sem cabeçalho: {path}")

        for row in reader:
            # ignora linhas onde todos os valores são vazios
            if any(v.strip() for v in row.values()):
                # remove espaços em branco extras nos valores
                clean = {k.strip(): v.strip() for k, v in row.items() if k}
                rows.append(clean)

    return rows


def iter_csv(path: str | Path) -> Iterator[dict[str, str]]:
    """
    Versão geradora de :func:`read_csv` para arquivos grandes.

    Args:
        path: Caminho para o arquivo CSV.

    Yields:
        Dicionário com os dados de cada linha.
    """
    for row in read_csv(path):
        yield row


def validate_columns(
    rows: list[dict[str, str]],
    required_columns: list[str],
) -> list[str]:
    """
    Verifica se as colunas obrigatórias estão presentes no CSV.

    Args:
        rows: Lista de dicionários lidos do CSV.
        required_columns: Colunas que devem existir.

    Returns:
        Lista de colunas ausentes (vazia se tudo OK).
    """
    if not rows:
        return []

    available = set(rows[0].keys())
    missing = [col for col in required_columns if col not in available]
    return missing
