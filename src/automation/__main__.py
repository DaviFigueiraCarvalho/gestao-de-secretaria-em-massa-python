"""
CLI da ferramenta de automação de formulários.

Uso::

    # atalho de ambiente (dev = localhost:3000 | prod = app.icravivalista)
    python -m automation churches import --env dev --csv examples/igrejas.csv
    python -m automation churches import --env prod --csv examples/igrejas.csv

    # ou passando a URL manualmente
    python -m automation churches import --url http://localhost:3000 --csv examples/igrejas.csv
    python -m automation login-test --env prod
"""
from __future__ import annotations

import sys

import click

from automation.config import apply_overrides, load_config


# ---------------------------------------------------------------------------
# Presets de ambiente
# ---------------------------------------------------------------------------

#: URLs pré-configuradas para cada ambiente
ENV_URLS: dict[str, str] = {
    "dev": "http://localhost:3000",
    "prod": "https://app.icravivalista",
}


# ---------------------------------------------------------------------------
# Opções globais compartilhadas por todos os sub-comandos
# ---------------------------------------------------------------------------

GLOBAL_OPTIONS = [
    click.option("--config", "-c", default=None, help="Caminho para config.yaml/.json"),
    click.option(
        "--env",
        type=click.Choice(["dev", "prod"]),
        default=None,
        help="Ambiente alvo: dev (localhost:3000) ou prod (app.icravivalista)",
    ),
    click.option("--url", default=None, help="URL base da aplicação (sobrescreve --env)"),
    click.option("--username", "-u", default=None, help="Usuário para login"),
    click.option("--password", "-p", default=None, help="Senha para login"),
    click.option(
        "--headless/--no-headless",
        default=None,
        help="Rodar em modo headless (padrão: headless)",
    ),
    click.option("--timeout", default=None, type=int, help="Timeout em ms"),
    click.option("--output-dir", default=None, help="Pasta de saída dos resultados"),
    click.option(
        "--output-format",
        default=None,
        type=click.Choice(["csv", "json"]),
        help="Formato de saída (csv ou json)",
    ),
]


def global_options(func):
    """Decorador que aplica todas as opções globais a um comando."""
    for option in reversed(GLOBAL_OPTIONS):
        func = option(func)
    return func


def _build_config(
    config: str | None,
    env: str | None,
    url: str | None,
    username: str | None,
    password: str | None,
    headless: bool | None,
    timeout: int | None,
    output_dir: str | None,
    output_format: str | None,
):
    """Carrega e aplica sobrescritas na configuração.

    Prioridade da URL: --url > --env > config.yaml > padrão (localhost:3000).
    """
    cfg = load_config(config)

    # resolve URL: --url tem prioridade; se não informado, usa preset do --env
    resolved_url = url or (ENV_URLS[env] if env else None)

    apply_overrides(
        cfg,
        base_url=resolved_url,
        username=username,
        password=password,
        headless=headless,
        timeout=timeout,
        output_dir=output_dir,
        output_format=output_format,
    )
    return cfg


# ---------------------------------------------------------------------------
# Grupo raiz
# ---------------------------------------------------------------------------


@click.group()
def cli() -> None:
    """Automação de preenchimento em massa de formulários web via CSV."""


# ---------------------------------------------------------------------------
# Comando: login-test
# ---------------------------------------------------------------------------


@cli.command("login-test")
@global_options
def login_test(
    config, env, url, username, password, headless, timeout, output_dir, output_format
) -> None:
    """Testa o login na aplicação e imprime resultado."""
    from automation.browser import browser_context
    from automation.config import Config
    from automation.logger import logger

    cfg = _build_config(
        config, env, url, username, password, headless, timeout, output_dir, output_format
    )

    logger.info("Testando login em %s ...", cfg.base_url)

    try:
        with browser_context(cfg.browser) as (_, _, page):
            page.goto(f"{cfg.base_url}/login")
            page.wait_for_load_state("networkidle")

            page.locator(
                '[data-testid="input-username"], [name="username"]'
            ).first.fill(cfg.credentials.username)
            page.locator(
                '[data-testid="input-password"], [name="password"]'
            ).first.fill(cfg.credentials.password)
            page.locator(
                '[data-testid="btn-login"], [type="submit"]'
            ).first.click()

            page.wait_for_url(
                lambda u: "/login" not in u,
                timeout=cfg.browser.timeout,
            )

        click.echo("✓ Login realizado com sucesso!")
    except Exception as exc:  # noqa: BLE001
        click.echo(f"✗ Falha no login: {exc}", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Fábrica de grupos de entidade
# ---------------------------------------------------------------------------


def _make_entity_group(name: str, help_text: str) -> click.Group:
    """Cria um grupo de comandos com o sub-comando 'import' para uma entidade."""

    @click.group(name=name, help=help_text)
    def group() -> None:
        pass

    @group.command("import")
    @click.option(
        "--csv",
        "csv_path",
        required=True,
        help="Caminho para o arquivo CSV",
    )
    @global_options
    def import_cmd(
        csv_path,
        config,
        env,
        url,
        username,
        password,
        headless,
        timeout,
        output_dir,
        output_format,
    ) -> None:
        """Importa registros a partir de um arquivo CSV."""
        cfg = _build_config(
            config, env, url, username, password, headless, timeout, output_dir, output_format
        )
        _run_entity(name, cfg, csv_path)

    return group


def _run_entity(entity: str, cfg, csv_path: str) -> None:
    """Executa a automação da entidade correspondente."""
    from automation.entities import (
        cells,
        churches,
        commissions,
        families,
        members,
    )

    mapping = {
        "churches": churches.create,
        "cells": cells.create,
        "members": members.create,
        "commissions": commissions.create,
        "families": families.create,
    }

    fn = mapping.get(entity)
    if fn is None:
        click.echo(f"Entidade desconhecida: {entity}", err=True)
        sys.exit(1)

    fn(cfg, csv_path)


# ---------------------------------------------------------------------------
# Registro dos grupos de entidade
# ---------------------------------------------------------------------------

cli.add_command(_make_entity_group("churches", "Gerencia igrejas"))
cli.add_command(_make_entity_group("cells", "Gerencia células"))
cli.add_command(_make_entity_group("members", "Gerencia membros"))
cli.add_command(_make_entity_group("commissions", "Gerencia comissões"))
cli.add_command(_make_entity_group("families", "Gerencia famílias"))


# ---------------------------------------------------------------------------
# Entry-point ao chamar python -m automation
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    cli()
