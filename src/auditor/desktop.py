"""Windows desktop entry point used by the bundled dashboard executable."""
import sys
from importlib.resources import files


def main() -> None:
    from streamlit.web import cli as streamlit_cli

    dashboard = files("auditor").joinpath("dashboard.py")
    sys.argv = ["streamlit", "run", str(dashboard), "--server.headless=false"]
    streamlit_cli.main()


if __name__ == "__main__":
    main()
