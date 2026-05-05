"""
Testes unitários para o módulo de configuração.

Valida carregamento de YAML/JSON e aplicação de sobrescritas.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
import yaml

from automation.config import (
    BrowserConfig,
    Config,
    CredentialsConfig,
    OutputConfig,
    apply_overrides,
    load_config,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_yaml(path: Path, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True)


def _write_json(path: Path, data: dict) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Testes de load_config
# ---------------------------------------------------------------------------


class TestLoadConfig:
    """Testes para a função load_config."""

    def test_sem_arquivo_retorna_padrao(self, tmp_path, monkeypatch):
        """Sem arquivo de config, deve retornar Config com valores padrão."""
        monkeypatch.chdir(tmp_path)  # pasta sem config.yaml
        config = load_config()

        assert isinstance(config, Config)
        assert config.base_url == "http://localhost:3000"

    def test_carrega_yaml(self, tmp_path):
        """Deve carregar corretamente um arquivo YAML."""
        cfg_file = tmp_path / "config.yaml"
        _write_yaml(
            cfg_file,
            {
                "base_url": "http://meu-servidor.com",
                "credentials": {"username": "admin", "password": "secreta"},
                "browser": {"headless": False, "timeout": 10000},
                "output": {"dir": "saida", "format": "json"},
            },
        )

        config = load_config(cfg_file)

        assert config.base_url == "http://meu-servidor.com"
        assert config.credentials.username == "admin"
        assert config.credentials.password == "secreta"
        assert config.browser.headless is False
        assert config.browser.timeout == 10000
        assert config.output.dir == "saida"
        assert config.output.format == "json"

    def test_carrega_json(self, tmp_path):
        """Deve carregar corretamente um arquivo JSON."""
        cfg_file = tmp_path / "config.json"
        _write_json(
            cfg_file,
            {"base_url": "http://json-server.com"},
        )

        config = load_config(cfg_file)

        assert config.base_url == "http://json-server.com"

    def test_arquivo_nao_encontrado_usa_padrao(self, tmp_path):
        """Se o arquivo explícito não existir, deve retornar Config padrão."""
        config = load_config(tmp_path / "nao_existe.yaml")

        assert config.base_url == "http://localhost:3000"

    def test_yaml_com_csv_paths(self, tmp_path):
        """Deve carregar csv_paths do YAML."""
        cfg_file = tmp_path / "config.yaml"
        _write_yaml(
            cfg_file,
            {
                "csv_paths": {
                    "churches": "examples/igrejas.csv",
                    "members": "examples/membros.csv",
                }
            },
        )

        config = load_config(cfg_file)

        assert config.csv_paths["churches"] == "examples/igrejas.csv"
        assert config.csv_paths["members"] == "examples/membros.csv"

    def test_yaml_com_viewport(self, tmp_path):
        """Deve carregar viewport do YAML."""
        cfg_file = tmp_path / "config.yaml"
        _write_yaml(
            cfg_file,
            {"browser": {"viewport": {"width": 1920, "height": 1080}}},
        )

        config = load_config(cfg_file)

        assert config.browser.viewport_width == 1920
        assert config.browser.viewport_height == 1080


# ---------------------------------------------------------------------------
# Testes de apply_overrides
# ---------------------------------------------------------------------------


class TestApplyOverrides:
    """Testes para a função apply_overrides."""

    def test_sobrescreve_base_url(self):
        """Deve sobrescrever a URL base."""
        config = Config()
        apply_overrides(config, base_url="http://novo.com")

        assert config.base_url == "http://novo.com"

    def test_sobrescreve_credenciais(self):
        """Deve sobrescrever usuário e senha."""
        config = Config()
        apply_overrides(config, username="user_novo", password="senha_nova")

        assert config.credentials.username == "user_novo"
        assert config.credentials.password == "senha_nova"

    def test_sobrescreve_headless(self):
        """Deve sobrescrever modo headless."""
        config = Config()
        config.browser.headless = True

        apply_overrides(config, headless=False)

        assert config.browser.headless is False

    def test_sobrescreve_timeout(self):
        """Deve sobrescrever timeout."""
        config = Config()
        apply_overrides(config, timeout=60000)

        assert config.browser.timeout == 60000

    def test_sobrescreve_output(self):
        """Deve sobrescrever dir e formato de saída."""
        config = Config()
        apply_overrides(config, output_dir="meus_resultados", output_format="json")

        assert config.output.dir == "meus_resultados"
        assert config.output.format == "json"

    def test_none_nao_sobrescreve(self):
        """Valores None não devem alterar a configuração existente."""
        config = Config(base_url="http://original.com")
        apply_overrides(config, base_url=None)

        assert config.base_url == "http://original.com"

    def test_variaveis_de_ambiente(self, monkeypatch):
        """Deve ler usuário/senha de variáveis de ambiente quando não configurados."""
        monkeypatch.setenv("AUTOMATION_USERNAME", "env_user")
        monkeypatch.setenv("AUTOMATION_PASSWORD", "env_pass")

        config = Config()
        apply_overrides(config)

        assert config.credentials.username == "env_user"
        assert config.credentials.password == "env_pass"

    def test_env_nao_sobrescreve_explicito(self, monkeypatch):
        """Variável de ambiente não deve sobrescrever valor explícito."""
        monkeypatch.setenv("AUTOMATION_USERNAME", "env_user")

        config = Config()
        config.credentials.username = "explicit_user"
        apply_overrides(config)

        assert config.credentials.username == "explicit_user"
