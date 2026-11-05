from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("castdevices")
except PackageNotFoundError:  # rodando sem o pacote instalado
    __version__ = "dev"


def main() -> None:
    from scrcpy_ui.app import run
    raise SystemExit(run())
