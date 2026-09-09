"""Single application version source used by UI and native package metadata."""

__version__ = "2.0.0"


def window_title(translated_name: str) -> str:
    return f"{translated_name} · {__version__}"
