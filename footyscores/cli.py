import argparse
import json
from typing import List

from .pipeline.generate import generate_match_endpoint, generate_matches
from .presentation.match_list import format_match_list


def run_generate_command(match_code: str | None) -> None:
    if match_code:
        endpoint = generate_match_endpoint(match_code)
        print(json.dumps(endpoint, ensure_ascii=False, indent=2))
        return

    matches = generate_matches()
    print(format_match_list(matches))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python main.py")
    subparsers = parser.add_subparsers(dest="command")
    generate = subparsers.add_parser("generate")
    generate.add_argument("match_code", nargs="?")
    return parser


def main(arguments: List[str]) -> int:
    parser = build_parser()
    if not arguments:
        parser.print_help()
        return 0

    parsed = parser.parse_args(arguments)
    run_generate_command(parsed.match_code)
    return 0
