"""
Automação para criação de Igrejas.

Formulário esperado (campos mapeados via data-testid):
  - data-testid="input-nome"          → nome da igreja
  - data-testid="input-endereco"      → endereço completo
  - data-testid="input-cidade"        → cidade
  - data-testid="input-estado"        → estado (UF)
  - data-testid="input-telefone"      → telefone de contato
  - data-testid="input-pastor"        → nome do pastor responsável
  - data-testid="input-data-fundacao" → data de fundação (YYYY-MM-DD)

Workaround: se o front-end não tiver data-testid, os campos são encontrados
por label (ex: "Nome", "Endereço") ou pelo atributo name.
"""
from __future__ import annotations

from playwright.sync_api import Page

from automation.base import BaseAutomation
from automation.config import Config


class ChurchesAutomation(BaseAutomation):
    """Automação para o formulário de criação de Igrejas."""

    entity_name = "igrejas"

    required_columns = ["nome"]  # único campo obrigatório

    def navigate_to_create(self, page: Page) -> None:
        """Navega até o formulário de criação de igrejas."""
        page.goto(f"{self.config.base_url}/igrejas/criar")
        page.wait_for_load_state("networkidle")

    def create_one(self, page: Page, row: dict[str, str]) -> None:
        """Preenche e submete o formulário de criação de uma igreja."""
        self._fill_field(
            page,
            data_testid="input-nome",
            value=row.get("nome", ""),
            fallback_label="Nome",
            fallback_name="nome",
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
            data_testid="input-cidade",
            value=row.get("cidade", ""),
            fallback_label="Cidade",
            fallback_name="cidade",
        )
        self._fill_field(
            page,
            data_testid="input-estado",
            value=row.get("estado", ""),
            fallback_label="Estado",
            fallback_name="estado",
        )
        self._fill_field(
            page,
            data_testid="input-telefone",
            value=row.get("telefone", ""),
            fallback_label="Telefone",
            fallback_name="telefone",
        )
        self._fill_field(
            page,
            data_testid="input-pastor",
            value=row.get("pastor", ""),
            fallback_label="Pastor",
            fallback_name="pastor",
        )
        self._fill_field(
            page,
            data_testid="input-data-fundacao",
            value=row.get("data_fundacao", ""),
            fallback_label="Data de Fundação",
            fallback_name="data_fundacao",
        )

        self._submit_form(page)


def create(config: Config, csv_path: str) -> None:
    """
    Ponto de entrada para importação de igrejas via CLI.

    Args:
        config: Configuração carregada.
        csv_path: Caminho para o CSV de igrejas.
    """
    automation = ChurchesAutomation(config)
    automation.run(csv_path)
