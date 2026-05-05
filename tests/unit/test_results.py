"""
Testes unitários para o módulo de resultados.

Valida acumulação, contagem e persistência dos resultados de automação.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from automation.results import AttemptResult, ResultsWriter


class TestAttemptResult:
    """Testes para o dataclass AttemptResult."""

    def test_criacao_basica(self):
        """Deve criar um AttemptResult com os campos corretos."""
        result = AttemptResult(
            entidade="igrejas",
            linha=1,
            status="sucesso",
            identificador="Igreja A",
        )

        assert result.entidade == "igrejas"
        assert result.linha == 1
        assert result.status == "sucesso"
        assert result.identificador == "Igreja A"
        assert result.mensagem == ""
        assert result.timestamp  # não deve ser vazio

    def test_timestamp_preenchido_automaticamente(self):
        """O timestamp deve ser preenchido automaticamente."""
        r = AttemptResult(entidade="e", linha=1, status="sucesso", identificador="x")
        assert "T" in r.timestamp  # formato ISO 8601


class TestResultsWriter:
    """Testes para a classe ResultsWriter."""

    def test_add_e_contagem(self):
        """Deve acumular resultados e contar corretamente."""
        writer = ResultsWriter(output_dir="/tmp/test_results", entity="igrejas")

        writer.add_success(1, "Igreja A")
        writer.add_success(2, "Igreja B")
        writer.add_error(3, "Igreja C", "Timeout")

        assert writer.total == 3
        assert writer.successes == 2
        assert writer.errors == 1

    def test_salvar_csv(self, tmp_path):
        """Deve salvar resultados em CSV com as colunas corretas."""
        writer = ResultsWriter(output_dir=str(tmp_path), entity="igrejas")
        writer.add_success(1, "Igreja A", "OK")
        writer.add_error(2, "Igreja B", "Erro de timeout")

        output = writer.save(format="csv")

        assert output.exists()
        assert output.suffix == ".csv"

        with open(output, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == 2
        assert rows[0]["status"] == "sucesso"
        assert rows[1]["status"] == "erro"
        assert rows[1]["mensagem"] == "Erro de timeout"

    def test_salvar_json(self, tmp_path):
        """Deve salvar resultados em JSON corretamente."""
        writer = ResultsWriter(output_dir=str(tmp_path), entity="membros")
        writer.add_success(1, "João Silva")

        output = writer.save(format="json")

        assert output.exists()
        assert output.suffix == ".json"

        with open(output, encoding="utf-8") as f:
            data = json.load(f)

        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["identificador"] == "João Silva"
        assert data[0]["status"] == "sucesso"

    def test_salvar_csv_vazio(self, tmp_path):
        """Deve criar arquivo vazio quando não há resultados."""
        writer = ResultsWriter(output_dir=str(tmp_path), entity="celulas")
        output = writer.save(format="csv")

        assert output.exists()
        assert output.read_text(encoding="utf-8") == ""

    def test_cria_diretorio_de_saida(self, tmp_path):
        """Deve criar o diretório de saída se não existir."""
        subdir = tmp_path / "novo" / "diretorio"
        writer = ResultsWriter(output_dir=str(subdir), entity="igrejas")
        writer.add_success(1, "Igreja X")
        output = writer.save()

        assert subdir.exists()
        assert output.exists()

    def test_results_retorna_copia(self):
        """A propriedade results deve retornar uma cópia da lista."""
        writer = ResultsWriter(output_dir="/tmp", entity="igrejas")
        writer.add_success(1, "Igreja A")

        lista = writer.results
        lista.clear()  # modificar a cópia não deve afetar o writer

        assert writer.total == 1
