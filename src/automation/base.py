"""
Classe base para todas as automações de entidades.

Define o contrato comum: login, iteração por CSV e registro de resultados.
Cada módulo de entidade deve estender :class:`BaseAutomation` e implementar
:meth:`create_one`.
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from playwright.sync_api import Page

from automation.browser import browser_context
from automation.config import Config
from automation.csv_utils import read_csv, validate_columns
from automation.logger import setup_logger
from automation.results import ResultsWriter


class BaseAutomation(ABC):
    """
    Classe base abstrata para automação de formulários web.

    Subclasses devem definir:
    - :attr:`entity_name`: identificador da entidade (ex: ``"igrejas"``).
    - :attr:`required_columns`: colunas obrigatórias no CSV.
    - :meth:`create_one`: lógica de preenchimento do formulário para uma linha.
    - :meth:`navigate_to_create`: navegar até o formulário de criação.
    """

    # ------------------------------------------------------------------
    # Atributos que subclasses devem sobrescrever
    # ------------------------------------------------------------------

    #: Nome da entidade (usado em logs e nomes de arquivo de resultado).
    entity_name: str = "entidade"

    #: Colunas que o CSV deve ter para esta entidade.
    required_columns: list[str] = []

    # ------------------------------------------------------------------
    # Inicialização
    # ------------------------------------------------------------------

    def __init__(self, config: Config) -> None:
        self.config = config
        self.logger: logging.Logger = setup_logger(
            f"automation.{self.entity_name}"
        )

    # ------------------------------------------------------------------
    # Métodos abstratos — subclasses obrigatoriamente implementam
    # ------------------------------------------------------------------

    @abstractmethod
    def navigate_to_create(self, page: Page) -> None:
        """Navega até o formulário de criação da entidade."""

    @abstractmethod
    def create_one(self, page: Page, row: dict[str, str]) -> None:
        """
        Preenche e submete o formulário de criação para uma linha do CSV.

        Args:
            page: Página Playwright já autenticada.
            row: Dicionário com os dados da linha do CSV.

        Raises:
            Exception: Qualquer exceção indica falha na criação.
        """

    # ------------------------------------------------------------------
    # Método principal — não sobrescrever normalmente
    # ------------------------------------------------------------------

    def run(self, csv_path: str | Path) -> ResultsWriter:
        """
        Executa a importação completa: login → CSV → criar cada linha.

        Args:
            csv_path: Caminho para o arquivo CSV.

        Returns:
            :class:`ResultsWriter` com o resultado de cada tentativa.
        """
        csv_path = Path(csv_path)
        writer = ResultsWriter(
            output_dir=self.config.output.dir,
            entity=self.entity_name,
        )

        # lê e valida o CSV antes de abrir o browser
        rows = read_csv(csv_path)
        missing = validate_columns(rows, self.required_columns)
        if missing:
            raise ValueError(
                f"CSV '{csv_path}' está faltando as colunas: {', '.join(missing)}"
            )

        self.logger.info(
            "Iniciando importação de %d linha(s) para '%s'",
            len(rows),
            self.entity_name,
        )

        with browser_context(self.config.browser) as (_, _, page):
            self._login(page)

            for idx, row in enumerate(rows, start=1):
                identificador = self._get_identifier(row)
                self.logger.info(
                    "Linha %d/%d — %s", idx, len(rows), identificador
                )
                try:
                    self.navigate_to_create(page)
                    self.create_one(page, row)
                    writer.add_success(
                        linha=idx,
                        identificador=identificador,
                        mensagem="Criado com sucesso",
                    )
                    self.logger.info("  ✓ Sucesso: %s", identificador)
                except Exception as exc:  # noqa: BLE001
                    # captura qualquer erro (timeout, elemento não encontrado, etc.)
                    # para registrar o resultado e continuar com as próximas linhas
                    mensagem = str(exc)
                    writer.add_error(
                        linha=idx,
                        identificador=identificador,
                        mensagem=mensagem,
                    )
                    self.logger.error("  ✗ Erro na linha %d: %s", idx, mensagem)

        # salva resultados e exibe resumo
        output_file = writer.save(format=self.config.output.format)
        self.logger.info(
            "Importação concluída: %d sucesso(s), %d erro(s). Resultado: %s",
            writer.successes,
            writer.errors,
            output_file,
        )

        return writer

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------

    def _login(self, page: Page) -> None:
        """Realiza o login na aplicação usando as credenciais configuradas."""
        self.logger.info("Fazendo login em %s", self.config.base_url)

        page.goto(f"{self.config.base_url}/login")
        page.wait_for_load_state("networkidle")

        # tenta localizar campo de usuário via data-testid, depois fallback
        username_field = self._find_field(
            page,
            data_testid="input-username",
            fallback_label="Usuário",
            fallback_name="username",
        )
        password_field = self._find_field(
            page,
            data_testid="input-password",
            fallback_label="Senha",
            fallback_name="password",
        )

        username_field.fill(self.config.credentials.username)
        password_field.fill(self.config.credentials.password)

        # botão de submit via data-testid ou tipo submit
        submit = page.locator(
            '[data-testid="btn-login"], [type="submit"]'
        ).first
        submit.click()

        # aguarda redirecionar para fora da tela de login
        page.wait_for_url(
            lambda url: "/login" not in url,
            timeout=self.config.browser.timeout,
        )
        self.logger.info("Login realizado com sucesso")

    def _find_field(
        self,
        page: Page,
        data_testid: str,
        fallback_label: str,
        fallback_name: str,
    ) -> Any:
        """
        Tenta localizar um campo de formulário por data-testid; se não encontrar,
        usa label ou name como fallback.

        Workaround documentado: se o front-end não tiver ``data-testid``,
        usa ``page.get_by_label()`` ou ``page.locator('[name=...]')``.
        """
        locator = page.locator(f'[data-testid="{data_testid}"]')
        if locator.count() > 0:
            return locator.first

        # fallback 1: por label
        try:
            return page.get_by_label(fallback_label, exact=False)
        except Exception:  # noqa: BLE001
            # get_by_label pode lançar se o label não existir; tenta fallback por name
            self.logger.debug(
                "Campo '%s' não encontrado por label '%s', tentando name='%s'",
                data_testid,
                fallback_label,
                fallback_name,
            )

        # fallback 2: por name
        return page.locator(f'[name="{fallback_name}"]').first

    def _get_identifier(self, row: dict[str, str]) -> str:
        """Retorna o valor do campo 'nome' ou primeiro campo disponível."""
        return row.get("nome", next(iter(row.values()), "—"))

    def _fill_field(
        self,
        page: Page,
        data_testid: str,
        value: str,
        fallback_label: str = "",
        fallback_name: str = "",
    ) -> None:
        """
        Preenche um campo de formulário pelo data-testid ou fallback.

        Se o valor estiver vazio, não faz nada.
        """
        if not value:
            return

        field = self._find_field(
            page,
            data_testid=data_testid,
            fallback_label=fallback_label,
            fallback_name=fallback_name,
        )
        field.fill(value)

    def _submit_form(self, page: Page, data_testid: str = "btn-submit") -> None:
        """
        Clica no botão de submit e aguarda a resposta da rede.

        Tenta primeiro por data-testid; se não encontrar, usa o tipo submit.
        """
        btn = page.locator(f'[data-testid="{data_testid}"], [type="submit"]').first
        with page.expect_response(lambda r: r.status in (200, 201, 204, 302)):
            btn.click()
