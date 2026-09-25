import sys

from footyscores.cli import main


if __name__ == "__main__":
    try:
        raise SystemExit(main(sys.argv[1:]))
    except Exception as error:
        sys.stderr.write(f"Error: {error}\n")
        raise SystemExit(1)
