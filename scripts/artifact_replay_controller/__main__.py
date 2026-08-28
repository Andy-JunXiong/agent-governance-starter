"""Fixed module entry point; no dynamic parent Python command is required."""

from .controller import main


if __name__ == "__main__":
    raise SystemExit(main())
