"""
Automação para criação de Membros.

Formulário esperado (campos mapeados via data-testid):
  - data-testid="input-nome"            → nome completo
  - data-testid="input-email"           → e-mail
  - data-testid="input-telefone"        → telefone de contato
  - data-testid="input-data-nascimento" → data de nascimento (YYYY-MM-DD)
  - data-testid="input-endereco"        → endereço residencial
  - data-testid="input-celula"          → nome/referência da célula
  - data-testid="input-cargo"           → cargo/função na igreja
  - data-testid="input-data-batismo"    → data de batismo (YYYY-MM-DD)
  - data-testid="input-estado-civil"    → estado civil (ex: "Solteiro", "Casado")

Workaround: campos sem data-testid são localizados por label ou name.
"""
from __future__ import annotations

from playwright.sync_api import Page

from automation.base import BaseAutomation
from automation.config import Config


class MembersAutomation(BaseAutomation):
    """Automação para o formulário de criação de Membros."""

    entity_name = "membros"

    required_columns = ["nome"]

    def navigate_to_create(self, page: Page) -> None:
        """Navega até o formulário de criação de membros."""
        page.goto(f"{self.config.base_url}/membros/criar")
        page.wait_for_load_state("networkidle")

    def create_one(self, page: Page, row: dict[str, str]) -> None:
        """Preenche e submete o formulário de criação de um membro."""
        self._fill_field(
            page,
            data_testid="input-nome",
            value=row.get("nome", ""),
            fallback_label="Nome",
            fallback_name="nome",
        )
        self._fill_field(
            page,
            data_testid="input-email",
            value=row.get("email", ""),
            fallback_label="E-mail",
            fallback_name="email",
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
            data_testid="input-data-nascimento",
            value=row.get("data_nascimento", ""),
            fallback_label="Data de Nascimento",
            fallback_name="data_nascimento",
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
            data_testid="input-celula",
            value=row.get("celula", ""),
            fallback_label="Célula",
            fallback_name="celula",
        )
        self._fill_field(
            page,
            data_testid="input-cargo",
            value=row.get("cargo", ""),
            fallback_label="Cargo",
            fallback_name="cargo",
        )
        self._fill_field(
            page,
            data_testid="input-data-batismo",
            value=row.get("data_batismo", ""),
            fallback_label="Data de Batismo",
            fallback_name="data_batismo",
        )
        self._fill_field(
            page,
            data_testid="input-estado-civil",
            value=row.get("estado_civil", ""),
            fallback_label="Estado Civil",
            fallback_name="estado_civil",
        )

        self._submit_form(page)


def create(config: Config, csv_path: str) -> None:
    """
    Ponto de entrada para importação de membros via CLI.

    Args:
        config: Configuração carregada.
        csv_path: Caminho para o CSV de membros.
    """
    automation = MembersAutomation(config)
    automation.run(csv_path)
