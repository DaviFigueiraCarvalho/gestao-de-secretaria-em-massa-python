"""
Módulo de gerenciamento de resultados das automações.

Salva o status de cada tentativa de criação em CSV ou JSON.
"""
from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Literal


@dataclass
class AttemptResult:
    """Resultado de uma tentativa de criação de registro."""

    entidade: str                      # ex: "igreja", "celula"
    linha: int                         # número da linha no CSV (base 1)
    status: Literal["sucesso", "erro"] # resultado da tentativa
    identificador: str                 # campo principal para identificação (ex: nome)
    mensagem: str = ""                 # detalhe de erro ou confirmação
    timestamp: str = field(
        default_factory=lambda: datetime.now().isoformat(timespec="seconds")
    )


class ResultsWriter:
    """
    Acumula resultados de tentativas e os salva em arquivo.

    Uso::

        writer = ResultsWriter(output_dir="results", entity="igrejas")
        writer.add(AttemptResult(...))
        writer.save(format="csv")
    """

    def __init__(self, output_dir: str | Path, entity: str) -> None:
        self._dir = Path(output_dir)
        self._entity = entity
        self._results: list[AttemptResult] = []

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------

    def add(self, result: AttemptResult) -> None:
        """Adiciona um resultado à lista."""
        self._results.append(result)

    def add_success(self, linha: int, identificador: str, mensagem: str = "") -> None:
        """Atalho para adicionar resultado de sucesso."""
        self.add(
            AttemptResult(
                entidade=self._entity,
                linha=linha,
                status="sucesso",
                identificador=identificador,
                mensagem=mensagem,
            )
        )

    def add_error(self, linha: int, identificador: str, mensagem: str) -> None:
        """Atalho para adicionar resultado de erro."""
        self.add(
            AttemptResult(
                entidade=self._entity,
                linha=linha,
                status="erro",
                identificador=identificador,
                mensagem=mensagem,
            )
        )

    def save(self, format: str = "csv") -> Path:
        """
        Salva os resultados em arquivo.

        Args:
            format: "csv" ou "json".

        Returns:
            Caminho do arquivo salvo.
        """
        self._dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{self._entity}_{timestamp}.{format}"
        output_path = self._dir / filename

        if format == "json":
            self._save_json(output_path)
        else:
            self._save_csv(output_path)

        return output_path

    @property
    def results(self) -> list[AttemptResult]:
        """Retorna cópia da lista de resultados."""
        return list(self._results)

    @property
    def total(self) -> int:
        """Total de tentativas registradas."""
        return len(self._results)

    @property
    def successes(self) -> int:
        """Total de tentativas com sucesso."""
        return sum(1 for r in self._results if r.status == "sucesso")

    @property
    def errors(self) -> int:
        """Total de tentativas com erro."""
        return sum(1 for r in self._results if r.status == "erro")

    # ------------------------------------------------------------------
    # Métodos privados
    # ------------------------------------------------------------------

    def _save_csv(self, path: Path) -> None:
        """Salva resultados em formato CSV."""
        if not self._results:
            path.write_text("", encoding="utf-8")
            return

        fieldnames = list(asdict(self._results[0]).keys())

        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for result in self._results:
                writer.writerow(asdict(result))

    def _save_json(self, path: Path) -> None:
        """Salva resultados em formato JSON."""
        data = [asdict(r) for r in self._results]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
