"""
Automação para criação de Comissões.

Formulário esperado (campos mapeados via data-testid):
  - data-testid="input-nome"         → nome da comissão
  - data-testid="input-descricao"    → descrição/propósito
  - data-testid="input-responsavel"  → membro responsável pela comissão
  - data-testid="input-data-inicio"  → data de início (YYYY-MM-DD)

Workaround: campos sem data-testid são localizados por label ou name.
"""
from __future__ import annotations

from playwright.sync_api import Page

from automation.base import BaseAutomation
from automation.config import Config


class CommissionsAutomation(BaseAutomation):
    """Automação para o formulário de criação de Comissões."""

    entity_name = "comissoes"

    required_columns = ["nome"]

    def navigate_to_create(self, page: Page) -> None:
        """Navega até o formulário de criação de comissões."""
        page.goto(f"{self.config.base_url}/comissoes/criar")
        page.wait_for_load_state("networkidle")

    def create_one(self, page: Page, row: dict[str, str]) -> None:
        """Preenche e submete o formulário de criação de uma comissão."""
        self._fill_field(
            page,
            data_testid="input-nome",
            value=row.get("nome", ""),
            fallback_label="Nome",
            fallback_name="nome",
        )
        self._fill_field(
            page,
            data_testid="input-descricao",
            value=row.get("descricao", ""),
            fallback_label="Descrição",
            fallback_name="descricao",
        )
        self._fill_field(
            page,
            data_testid="input-responsavel",
            value=row.get("responsavel", ""),
            fallback_label="Responsável",
            fallback_name="responsavel",
        )
        self._fill_field(
            page,
            data_testid="input-data-inicio",
            value=row.get("data_inicio", ""),
            fallback_label="Data de Início",
            fallback_name="data_inicio",
        )

        self._submit_form(page)


def create(config: Config, csv_path: str) -> None:
    """
    Ponto de entrada para importação de comissões via CLI.

    Args:
        config: Configuração carregada.
        csv_path: Caminho para o CSV de comissões.
    """
    automation = CommissionsAutomation(config)
    automation.run(csv_path)
