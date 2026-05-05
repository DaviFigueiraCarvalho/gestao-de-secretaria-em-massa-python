"""
Módulo de logging estruturado para a ferramenta de automação.

Configura um logger Python padrão com saída em arquivo e console.
"""
from __future__ import annotations

import logging
import sys
from pathlib import Path


def setup_logger(
    name: str = "automation",
    level: int = logging.INFO,
    log_file: str | Path | None = None,
) -> logging.Logger:
    """
    Configura e retorna um logger com handlers de console e (opcionalmente) arquivo.

    Args:
        name: Nome do logger.
        level: Nível mínimo de log.
        log_file: Caminho para arquivo de log (None = só console).

    Returns:
        Logger configurado.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # evita duplicar handlers em chamadas repetidas
    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # handler de console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # handler de arquivo (opcional)
    if log_file is not None:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# logger padrão do pacote — pode ser importado diretamente
logger = setup_logger("automation")
