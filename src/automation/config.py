"""
Módulo de configuração da ferramenta de automação.

Carrega configurações de arquivo YAML/JSON e permite sobrescrever via CLI.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


# ---------------------------------------------------------------------------
# Dataclasses de configuração
# ---------------------------------------------------------------------------


@dataclass
class BrowserConfig:
    """Configurações do navegador Playwright."""

    headless: bool = True
    slow_mo: int = 0
    timeout: int = 30_000
    viewport_width: int = 1280
    viewport_height: int = 720


@dataclass
class CredentialsConfig:
    """Credenciais de acesso à aplicação."""

    username: str = ""
    password: str = ""


@dataclass
class OutputConfig:
    """Configurações de saída dos resultados."""

    dir: str = "results"
    format: str = "csv"  # "csv" ou "json"


@dataclass
class Config:
    """Configuração completa da ferramenta."""

    base_url: str = "http://localhost:3000"
    credentials: CredentialsConfig = field(default_factory=CredentialsConfig)
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    csv_paths: dict[str, str] = field(default_factory=dict)
    output: OutputConfig = field(default_factory=OutputConfig)


# ---------------------------------------------------------------------------
# Carregamento de configuração
# ---------------------------------------------------------------------------


def _parse_raw(raw: dict[str, Any]) -> Config:
    """Converte um dicionário bruto em um objeto Config."""
    config = Config()

    if "base_url" in raw:
        config.base_url = raw["base_url"]

    if "credentials" in raw:
        creds = raw["credentials"]
        config.credentials = CredentialsConfig(
            username=creds.get("username", ""),
            password=creds.get("password", ""),
        )

    if "browser" in raw:
        b = raw["browser"]
        viewport = b.get("viewport", {})
        config.browser = BrowserConfig(
            headless=b.get("headless", True),
            slow_mo=b.get("slow_mo", 0),
            timeout=b.get("timeout", 30_000),
            viewport_width=viewport.get("width", 1280),
            viewport_height=viewport.get("height", 720),
        )

    if "csv_paths" in raw:
        config.csv_paths = dict(raw["csv_paths"])

    if "output" in raw:
        o = raw["output"]
        config.output = OutputConfig(
            dir=o.get("dir", "results"),
            format=o.get("format", "csv"),
        )

    return config


def load_config(path: str | Path | None = None) -> Config:
    """
    Carrega a configuração de um arquivo YAML ou JSON.

    Se ``path`` for None, tenta ``config.yaml`` e ``config.json`` no
    diretório atual. Se nenhum arquivo for encontrado, retorna Config padrão.
    """
    candidates: list[Path] = []

    if path is not None:
        candidates.append(Path(path))
    else:
        candidates = [Path("config.yaml"), Path("config.yml"), Path("config.json")]

    for candidate in candidates:
        if candidate.exists():
            raw = _read_file(candidate)
            return _parse_raw(raw)

    # nenhum arquivo encontrado — usa padrão
    return Config()


def _read_file(path: Path) -> dict[str, Any]:
    """Lê um arquivo YAML ou JSON e retorna o dicionário."""
    with open(path, "r", encoding="utf-8") as f:
        if path.suffix in {".yaml", ".yml"}:
            return yaml.safe_load(f) or {}
        if path.suffix == ".json":
            return json.load(f)
    raise ValueError(f"Formato não suportado: {path.suffix}")


def apply_overrides(
    config: Config,
    *,
    base_url: str | None = None,
    username: str | None = None,
    password: str | None = None,
    headless: bool | None = None,
    timeout: int | None = None,
    output_dir: str | None = None,
    output_format: str | None = None,
) -> Config:
    """
    Aplica sobrescritas de linha de comando sobre uma Config já carregada.

    Retorna a mesma instância modificada (mutável por conveniência).
    """
    if base_url is not None:
        config.base_url = base_url
    if username is not None:
        config.credentials.username = username
    if password is not None:
        config.credentials.password = password
    if headless is not None:
        config.browser.headless = headless
    if timeout is not None:
        config.browser.timeout = timeout
    if output_dir is not None:
        config.output.dir = output_dir
    if output_format is not None:
        config.output.format = output_format

    # lê variáveis de ambiente como último recurso (menor prioridade que CLI)
    if not config.credentials.username:
        config.credentials.username = os.environ.get("AUTOMATION_USERNAME", "")
    if not config.credentials.password:
        config.credentials.password = os.environ.get("AUTOMATION_PASSWORD", "")

    return config
