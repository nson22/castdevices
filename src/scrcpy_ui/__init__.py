from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("scrcpy-ui")
except PackageNotFoundError:  # rodando sem o pacote instalado
    __version__ = "dev"


def main() -> None:
    from scrcpy_ui.app import run
    raise SystemExit(run())
