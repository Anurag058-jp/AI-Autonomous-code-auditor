"""Console entry point used by the bundled audit CLI executable."""
from auditor.cli import app


def main() -> None:
    app()


if __name__ == "__main__":
    main()
