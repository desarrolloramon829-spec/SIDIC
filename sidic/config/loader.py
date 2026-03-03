"""
Cargador de configuración — lee defaults.json y permite override por usuario.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_CONFIG_DIR = Path(__file__).parent
_DEFAULTS_PATH = _CONFIG_DIR / "defaults.json"

_loaded_config: Optional[Dict[str, Any]] = None


def load_defaults() -> Dict[str, Any]:
    """Carga la configuración por defecto desde defaults.json."""
    global _loaded_config
    if _loaded_config is not None:
        return _loaded_config

    if not _DEFAULTS_PATH.exists():
        logger.warning(f"No se encontró {_DEFAULTS_PATH}, usando config vacía.")
        _loaded_config = {}
        return _loaded_config

    with open(_DEFAULTS_PATH, "r", encoding="utf-8") as f:
        _loaded_config = json.load(f)

    logger.info(f"Configuración cargada desde {_DEFAULTS_PATH}")
    return _loaded_config


def load_user_config(user_path: Path) -> Dict[str, Any]:
    """
    Carga config de usuario y la fusiona con defaults.

    Los valores del usuario sobreescriben los defaults (merge superficial
    por clave de primer nivel).
    """
    defaults = load_defaults().copy()

    if not user_path.exists():
        logger.warning(f"Config de usuario no encontrada: {user_path}")
        return defaults

    with open(user_path, "r", encoding="utf-8") as f:
        user_data = json.load(f)

    # Merge: user overrides defaults
    for key, value in user_data.items():
        if key.startswith("_"):
            continue
        if isinstance(value, dict) and isinstance(defaults.get(key), dict):
            defaults[key] = {**defaults[key], **value}
        else:
            defaults[key] = value

    logger.info(f"Config de usuario fusionada desde {user_path}")
    return defaults


def get_section(section: str) -> Dict[str, Any]:
    """Obtiene una sección específica de la configuración."""
    config = load_defaults()
    return config.get(section, {})


def reload() -> Dict[str, Any]:
    """Fuerza recarga de configuración desde disco."""
    global _loaded_config
    _loaded_config = None
    return load_defaults()
