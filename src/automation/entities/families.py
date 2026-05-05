"""
Automação para criação de Famílias.

Formulário esperado (campos mapeados via data-testid):
  - data-testid="input-nome"         → sobrenome/nome da família
  - data-testid="input-responsavel"  → membro responsável (chefe de família)
  - data-testid="input-endereco"     → endereço residencial
  - data-testid="input-telefone"     → telefone de contato
  - data-testid="input-observacoes"  → observações gerais

Workaround: campos sem data-testid são localizados por label ou name.
"""
from __future__ import annotations

from playwright.sync_api import Page

from automation.base import BaseAutomation
from automation.config import Config


class FamiliesAutomation(BaseAutomation):
    """Automação para o formulário de criação de Famílias."""

    entity_name = "familias"

    required_columns = ["nome"]

    def navigate_to_create(self, page: Page) -> None:
        """Navega até o formulário de criação de famílias."""
        page.goto(f"{self.config.base_url}/familias/criar")
        page.wait_for_load_state("networkidle")

    def create_one(self, page: Page, row: dict[str, str]) -> None:
        """Preenche e submete o formulário de criação de uma família."""
        self._fill_field(
            page,
            data_testid="input-nome",
            value=row.get("nome", ""),
            fallback_label="Nome",
            fallback_name="nome",
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
            data_testid="input-endereco",
            value=row.get("endereco", ""),
            fallback_label="Endereço",
            fallback_name="endereco",
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
            data_testid="input-observacoes",
            value=row.get("observacoes", ""),
            fallback_label="Observações",
            fallback_name="observacoes",
        )

        self._submit_form(page)


def create(config: Config, csv_path: str) -> None:
    """
    Ponto de entrada para importação de famílias via CLI.

    Args:
        config: Configuração carregada.
        csv_path: Caminho para o CSV de famílias.
    """
    automation = FamiliesAutomation(config)
    automation.run(csv_path)
