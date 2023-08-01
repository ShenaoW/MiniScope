from pathlib import Path


__all__ = ('ConfMan', )


class ConfMan:
    def __init__(self) -> None:
        self.config_path = Path.cwd() / 'config' / 'crawler' / 'config.toml'