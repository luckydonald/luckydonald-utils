from ..fully_qualified_name import fqn
from ..logger import ColoredFormatter, ColoredStreamHandler


def get_uvicorn_log_config(*, disable_existing_loggers: bool = False, project: str | None = None) -> dict[str, Any]:
    """
    ## Function
    ### Args:
        disable_existing_loggers:
        project:

    ### Returns:
        the config dict.

    ## Usage:

    ### Albemic:
    ```py
    # alembic/env.py
    # # Import:
    from logging.config import dictConfig
    from luckydonald_utils.uvicorns.log_config import get_uvicorn_log_config

    # Replacing/adding any `*Config` lines - i.e. `dictConfig(…)` or `fileConfig(…)`.
    dictConfig(get_uvicorn_log_config(disable_existing_loggers=False, project="your_app"))
    ```
    ```py
    if __name__ == "__main__":
        logging.add_colored_handler(level=logging.DEBUG, date_formatter="%Y-%m-%d %H:%M:%S")
        logger.info("Starting server...")
        # ... migrations ...
        print('Migrations done, reapplying logger config.')
        logging_config.dictConfig(get_uvicorn_log_config())
    # end if
    # …
    uvicorn.run(
        app=f'{app_module_path}:app',
        host='0.0.0.0',
        port=port,
        reload=False,
        workers=None,
        root_path="",
        proxy_headers=False,
        log_config=get_uvicorn_log_config(),
        log_level="trace",
        use_colors=None,
    )
    ```
    """
    config = {
        "version": 1,
        "disable_existing_loggers": disable_existing_loggers,
        "formatters": {
            "default": {
                "()": fqn(ColoredFormatter),
                "format": "%(levelprefix)s %(message)s",
                "use_colors": True,
            },
            "access": {
                "()": fqn(ColoredFormatter),
                "format": "%(levelprefix)s %(client_addr)s - '%(request_line)s' %(status_code)s",
                "use_colors": True,
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": fqn(ColoredStreamHandler),
                "stream": "ext://sys.stdout",
            },
            "access": {
                "formatter": "access",
                "class": fqn(ColoredStreamHandler),
                "stream": "ext://sys.stdout",
            },
            "root": {
                "formatter": "default",
                "class": fqn(ColoredStreamHandler),
                "stream": "ext://sys.stdout",
            },
        },
        "loggers": {
            "uvicorn": {
                "level": "INFO",
                "handlers": ["default"],
            },
            "uvicorn.error": {
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.access": {
                "level": "INFO",
                "handlers": ["access"],
                "propagate": False,
            },
            "uvicorn.asgi.trace": {
                "level": "INFO", # yes, they only log at "TRACE" level.
                "handlers": ["default"],
                "propagate": False,
            },
        },
        "root": {
            "level": "DEBUG",
            "handlers": ["root"],
            "propagate": False,
        },
    }
    if project:
        config['loggers'][project] = {
            "level": "DEBUG",
            "handlers": ["default"],
            "propagate": False,
        }
    # end if
    print(f"get_uvicorn_log_config() = {config}")
    return config
# end def
