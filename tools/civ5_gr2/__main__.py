"""Run from the repository root: python3 -m tools.civ5_gr2 --help."""
import argparse
import json
import sys
from pathlib import Path

from .format import FormatError, Reader, load_strings, require
from .references import extract_fort, summarize


def main():
    parser = argparse.ArgumentParser(description='Shared experimental Civ V static GR2 tools')
    commands = parser.add_subparsers(dest='command', required=True)
    inspect = commands.add_parser('inspect', help='validate container and inspect dynamic records')
    inspect.add_argument('input', type=Path)
    inspect.add_argument('--strings', type=Path, help='matching local GSD for hashed stock strings')
    inspect.add_argument('--codec', type=Path, help='OpenGR2 codec dylib; trusted local Oodle1 inputs only')
    inspect.add_argument('--json', type=Path)
    extract = commands.add_parser('extract-fort', help='extract local references to ignored cache')
    extract.add_argument('fpk', type=Path)
    extract.add_argument('--output', type=Path, default=Path('shared/references/local/fort'))
    args = parser.parse_args()
    try:
        if args.command == 'extract-fort':
            result = extract_fort(args.fpk, args.output)
        else:
            db_id, strings = load_strings(args.strings) if args.strings else (0, {})
            reader = Reader(args.input.read_bytes(), strings=strings, codec=args.codec)
            require(not reader.header[14] or reader.header[14] == db_id, 'missing or mismatched string database ID')
            result = summarize(reader)
        text = json.dumps(result, indent=2) + '\n'
        if getattr(args, 'json', None):
            args.json.parent.mkdir(parents=True, exist_ok=True)
            args.json.write_text(text)
        else:
            print(text, end='')
        return 0
    except (FormatError, OSError, UnicodeError) as e:
        print(f'civ5-gr2: {e}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
