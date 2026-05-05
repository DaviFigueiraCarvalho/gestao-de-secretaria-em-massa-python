"""
Teste e2e fake usando Playwright com servidor HTTP embutido.

Simula uma tela de login + formulário de criação de igreja para validar
a lógica de automação sem depender de um back-end real.

O servidor HTTP é criado com http.server da stdlib e serve um HTML mínimo
com os data-testids esperados pela automação.
"""
from __future__ import annotations

import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

import pytest
from playwright.sync_api import sync_playwright

# ---------------------------------------------------------------------------
# HTML mínimo simulando a aplicação
# ---------------------------------------------------------------------------

_LOGIN_HTML = b"""
<!DOCTYPE html>
<html>
<head><title>Login</title></head>
<body>
  <form id="login-form" action="/dashboard" method="get">
    <input data-testid="input-username" name="username" type="text" />
    <input data-testid="input-password" name="password" type="password" />
    <button data-testid="btn-login" type="submit">Entrar</button>
  </form>
</body>
</html>
"""

_DASHBOARD_HTML = b"""
<!DOCTYPE html>
<html>
<head><title>Dashboard</title></head>
<body>
  <h1>Dashboard</h1>
  <a href="/igrejas/criar">Nova Igreja</a>
</body>
</html>
"""

_CRIAR_IGREJA_HTML = b"""
<!DOCTYPE html>
<html>
<head><title>Criar Igreja</title></head>
<body>
  <form id="create-form" action="/igrejas/criado" method="get">
    <input data-testid="input-nome" name="nome" type="text" />
    <input data-testid="input-cidade" name="cidade" type="text" />
    <input data-testid="input-estado" name="estado" type="text" />
    <button data-testid="btn-submit" type="submit">Salvar</button>
  </form>
</body>
</html>
"""

_CRIADO_HTML = b"""
<!DOCTYPE html>
<html>
<head><title>Igreja criada</title></head>
<body>
  <p id="status">Igreja criada com sucesso!</p>
</body>
</html>
"""

# mapa de rotas → conteúdo HTML
_ROUTES: dict[str, bytes] = {
    "/login": _LOGIN_HTML,
    "/dashboard": _DASHBOARD_HTML,
    "/igrejas/criar": _CRIAR_IGREJA_HTML,
    "/igrejas/criado": _CRIADO_HTML,
}


# ---------------------------------------------------------------------------
# Servidor HTTP embutido
# ---------------------------------------------------------------------------


class _Handler(BaseHTTPRequestHandler):
    """Handler HTTP simples que serve HTML estático por rota."""

    def do_GET(self) -> None:  # noqa: N802
        # ignora query string ao buscar a rota
        path = self.path.split("?")[0]
        body = _ROUTES.get(path, b"<h1>404</h1>")
        status = 200 if path in _ROUTES else 404

        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args) -> None:
        """Silencia os logs do servidor para não poluir a saída dos testes."""


@pytest.fixture(scope="module")
def fake_server():
    """
    Fixture que inicia um servidor HTTP local em uma thread separada.

    Retorna a URL base (ex: http://localhost:PORT).
    """
    server = HTTPServer(("127.0.0.1", 0), _Handler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    yield f"http://127.0.0.1:{port}"

    server.shutdown()


# ---------------------------------------------------------------------------
# Testes E2E
# ---------------------------------------------------------------------------


class TestLoginFake:
    """Testa o fluxo de login contra o servidor fake."""

    def test_login_e_redirect(self, fake_server):
        """Deve preencher o formulário de login e ser redirecionado."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(f"{fake_server}/login")
            page.wait_for_load_state("networkidle")

            # preenche usuário e senha
            page.locator('[data-testid="input-username"]').fill("admin")
            page.locator('[data-testid="input-password"]').fill("senha")

            # clica em login e aguarda navegação
            page.locator('[data-testid="btn-login"]').click()
            page.wait_for_load_state("networkidle")

            # deve ter saído da tela de login
            assert "/login" not in page.url

            browser.close()


class TestCriarIgrejaFake:
    """Testa o formulário de criação de igreja contra o servidor fake."""

    def test_preenche_e_submete_formulario(self, fake_server):
        """Deve preencher o formulário e ver mensagem de sucesso."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(f"{fake_server}/igrejas/criar")
            page.wait_for_load_state("networkidle")

            # preenche campos pelo data-testid
            page.locator('[data-testid="input-nome"]').fill("Igreja Teste")
            page.locator('[data-testid="input-cidade"]').fill("São Paulo")
            page.locator('[data-testid="input-estado"]').fill("SP")

            page.locator('[data-testid="btn-submit"]').click()
            page.wait_for_load_state("networkidle")

            # verifica mensagem de sucesso
            assert page.locator("#status").inner_text() == "Igreja criada com sucesso!"

            browser.close()

    def test_data_testid_presentes_no_form(self, fake_server):
        """Todos os data-testids esperados devem estar presentes no formulário."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.goto(f"{fake_server}/igrejas/criar")
            page.wait_for_load_state("networkidle")

            testids = ["input-nome", "input-cidade", "input-estado", "btn-submit"]
            for testid in testids:
                count = page.locator(f'[data-testid="{testid}"]').count()
                assert count == 1, f"data-testid='{testid}' não encontrado no form"

            browser.close()
