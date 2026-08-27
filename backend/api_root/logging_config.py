"""
Configuração centralizada de logging do projeto.
Consumida por api_root.settings (LOGGING) e aplicada a todos os módulos
que usam logging.getLogger(__name__).
"""
import sys

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "stream": sys.stdout,
            "formatter": "default",
        },
    },
    "root": {
        "level": "INFO",
        "handlers": ["console"],
    },
    "loggers": {
        # api_rest e filhos (api_rest.PydanticAi, api_rest.views) em DEBUG para logs no container
        "api_rest": {"level": "DEBUG", "propagate": False, "handlers": ["console"]},
    },
}
