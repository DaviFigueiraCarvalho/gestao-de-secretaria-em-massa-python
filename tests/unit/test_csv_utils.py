"""
Testes unitários para o módulo csv_utils.

Validam leitura, parsing e validação de colunas sem necessidade de Playwright.
"""
from __future__ import annotations

import csv
import os
import tempfile
from pathlib import Path

import pytest

from automation.csv_utils import iter_csv, read_csv, validate_columns


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> Path:
    """Auxiliar: escreve um CSV temporário e retorna o caminho."""
    if not rows and fieldnames is None:
        path.write_text("", encoding="utf-8")
        return path

    headers = fieldnames or list(rows[0].keys())

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(rows)

    return path


# ---------------------------------------------------------------------------
# Testes de read_csv
# ---------------------------------------------------------------------------


class TestReadCsv:
    """Testes para a função read_csv."""

    def test_leitura_basica(self, tmp_path):
        """Deve ler um CSV simples e retornar lista de dicts."""
        csv_file = tmp_path / "test.csv"
        _write_csv(
            csv_file,
            [
                {"nome": "Igreja A", "cidade": "São Paulo"},
                {"nome": "Igreja B", "cidade": "Rio de Janeiro"},
            ],
        )

        rows = read_csv(csv_file)

        assert len(rows) == 2
        assert rows[0]["nome"] == "Igreja A"
        assert rows[1]["cidade"] == "Rio de Janeiro"

    def test_ignora_linhas_vazias(self, tmp_path):
        """Deve ignorar linhas completamente em branco."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("nome,cidade\nIgreja A,SP\n\n,\nIgreja B,RJ\n", encoding="utf-8")

        rows = read_csv(csv_file)

        # linhas com algum valor são mantidas; linhas totalmente vazias ignoradas
        nomes = [r["nome"] for r in rows if r["nome"]]
        assert "Igreja A" in nomes
        assert "Igreja B" in nomes

    def test_remove_espacos_nos_valores(self, tmp_path):
        """Deve remover espaços em branco extras dos valores."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text("nome,cidade\n  Igreja A  ,  São Paulo  \n", encoding="utf-8")

        rows = read_csv(csv_file)

        assert rows[0]["nome"] == "Igreja A"
        assert rows[0]["cidade"] == "São Paulo"

    def test_arquivo_nao_encontrado(self, tmp_path):
        """Deve lançar FileNotFoundError para arquivo inexistente."""
        with pytest.raises(FileNotFoundError):
            read_csv(tmp_path / "nao_existe.csv")

    def test_bom_utf8(self, tmp_path):
        """Deve suportar CSV com BOM (encoding utf-8-sig)."""
        csv_file = tmp_path / "bom.csv"
        csv_file.write_bytes(
            b"\xef\xbb\xbfnome,cidade\nIgreja BOM,SP\n"
        )

        rows = read_csv(csv_file)

        assert len(rows) == 1
        assert rows[0]["nome"] == "Igreja BOM"

    def test_csv_vazio_sem_cabecalho(self, tmp_path):
        """Deve lançar ValueError para CSV sem cabeçalho."""
        csv_file = tmp_path / "empty.csv"
        csv_file.write_text("", encoding="utf-8")

        with pytest.raises(ValueError, match="sem cabeçalho"):
            read_csv(csv_file)


# ---------------------------------------------------------------------------
# Testes de iter_csv
# ---------------------------------------------------------------------------


class TestIterCsv:
    """Testes para a função iter_csv."""

    def test_iteracao_basica(self, tmp_path):
        """Deve iterar linha a linha."""
        csv_file = tmp_path / "test.csv"
        _write_csv(
            csv_file,
            [{"nome": "A"}, {"nome": "B"}, {"nome": "C"}],
        )

        resultado = list(iter_csv(csv_file))

        assert len(resultado) == 3
        assert [r["nome"] for r in resultado] == ["A", "B", "C"]


# ---------------------------------------------------------------------------
# Testes de validate_columns
# ---------------------------------------------------------------------------


class TestValidateColumns:
    """Testes para a função validate_columns."""

    def test_sem_colunas_faltando(self):
        """Deve retornar lista vazia quando todas as colunas estão presentes."""
        rows = [{"nome": "A", "cidade": "SP"}]
        missing = validate_columns(rows, ["nome", "cidade"])
        assert missing == []

    def test_com_colunas_faltando(self):
        """Deve retornar as colunas ausentes."""
        rows = [{"nome": "A"}]
        missing = validate_columns(rows, ["nome", "email", "telefone"])
        assert "email" in missing
        assert "telefone" in missing
        assert "nome" not in missing

    def test_rows_vazio(self):
        """Deve retornar lista vazia quando rows está vazio."""
        missing = validate_columns([], ["nome", "cidade"])
        assert missing == []

    def test_colunas_obrigatorias_vazias(self):
        """Deve retornar lista vazia quando não há colunas obrigatórias."""
        rows = [{"nome": "A"}]
        missing = validate_columns(rows, [])
        assert missing == []


# ---------------------------------------------------------------------------
# Teste de integração: exemplos reais do projeto
# ---------------------------------------------------------------------------


class TestExemplosReais:
    """Valida que os CSVs de exemplo do projeto são lidos corretamente."""

    EXAMPLES_DIR = Path(__file__).parent.parent.parent / "examples"

    @pytest.mark.parametrize(
        "filename,coluna_esperada",
        [
            ("igrejas.csv", "nome"),
            ("celulas.csv", "nome"),
            ("membros.csv", "nome"),
            ("comissoes.csv", "nome"),
            ("familias.csv", "nome"),
        ],
    )
    def test_exemplo_csv_legivel(self, filename, coluna_esperada):
        """Cada CSV de exemplo deve ser lido e conter a coluna 'nome'."""
        csv_path = self.EXAMPLES_DIR / filename

        if not csv_path.exists():
            pytest.skip(f"Arquivo de exemplo não encontrado: {csv_path}")

        rows = read_csv(csv_path)

        assert len(rows) > 0, f"{filename} está vazio"
        assert coluna_esperada in rows[0], (
            f"Coluna '{coluna_esperada}' não encontrada em {filename}"
        )
