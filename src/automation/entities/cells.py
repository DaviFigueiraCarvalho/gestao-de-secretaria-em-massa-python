"""
Automação para criação de Células.

Formulário esperado (campos mapeados via data-testid):
  - data-testid="input-nome"       → nome da célula
  - data-testid="input-lider"      → nome do líder responsável
  - data-testid="input-dia-semana" → dia da semana (ex: "Segunda", "Terça")
  - data-testid="input-horario"    → horário (ex: "19:30")
  - data-testid="input-endereco"   → endereço de realização
  - data-testid="input-igreja"     → nome/referência da igreja vinculada

Workaround: campos sem data-testid são localizados por label ou name.
"""
from __future__ import annotations

from playwright.sync_api import Page

from automation.base import BaseAutomation
from automation.config import Config


class CellsAutomation(BaseAutomation):
    """Automação para o formulário de criação de Células."""

    entity_name = "celulas"

    required_columns = ["nome", "lider"]

    def navigate_to_create(self, page: Page) -> None:
        """Navega até o formulário de criação de células."""
        page.goto(f"{self.config.base_url}/celulas/criar")
        page.wait_for_load_state("networkidle")

    def create_one(self, page: Page, row: dict[str, str]) -> None:
        """Preenche e submete o formulário de criação de uma célula."""
        self._fill_field(
            page,
            data_testid="input-nome",
            value=row.get("nome", ""),
            fallback_label="Nome",
            fallback_name="nome",
        )
        self._fill_field(
            page,
            data_testid="input-lider",
            value=row.get("lider", ""),
            fallback_label="Líder",
            fallback_name="lider",
        )
        self._fill_field(
            page,
            data_testid="input-dia-semana",
            value=row.get("dia_semana", ""),
            fallback_label="Dia da Semana",
            fallback_name="dia_semana",
        )
        self._fill_field(
            page,
            data_testid="input-horario",
            value=row.get("horario", ""),
            fallback_label="Horário",
            fallback_name="horario",
        )
        self._fill_field(
            page,
            data_testid="input-endereco",
            value=row.get("endereco", ""),
            fallback_label="Endereço",
            fallback_name="endereco",
        )
        self._fill_field(
            page,
            data_testid="input-igreja",
            value=row.get("igreja", ""),
            fallback_label="Igreja",
            fallback_name="igreja",
        )

        self._submit_form(page)


def create(config: Config, csv_path: str) -> None:
    """
    Ponto de entrada para importação de células via CLI.

    Args:
        config: Configuração carregada.
        csv_path: Caminho para o CSV de células.
    """
    automation = CellsAutomation(config)
    automation.run(csv_path)
