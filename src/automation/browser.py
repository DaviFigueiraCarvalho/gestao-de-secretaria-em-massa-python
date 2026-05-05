"""
Módulo de gerenciamento do navegador Playwright.

Fornece um context manager que inicializa e finaliza o browser/page de forma segura.
"""
from __future__ import annotations

from contextlib import contextmanager
from typing import Generator

from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright

from automation.config import BrowserConfig


@contextmanager
def browser_context(
    config: BrowserConfig,
) -> Generator[tuple[Browser, BrowserContext, Page], None, None]:
    """
    Context manager que inicia o Playwright, abre um browser e uma página.

    Uso::

        with browser_context(config.browser) as (browser, context, page):
            page.goto("https://exemplo.com")

    Args:
        config: Configurações do navegador.

    Yields:
        Tupla (Browser, BrowserContext, Page) prontos para uso.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=config.headless,
            slow_mo=config.slow_mo,
        )

        context = browser.new_context(
            viewport={
                "width": config.viewport_width,
                "height": config.viewport_height,
            }
        )
        context.set_default_timeout(config.timeout)

        page = context.new_page()

        try:
            yield browser, context, page
        finally:
            context.close()
            browser.close()
