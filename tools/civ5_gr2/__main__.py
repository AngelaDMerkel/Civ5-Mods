"""Run from the repository root: python3 -m tools.civ5_gr2 --help."""
import argparse
import json
import sys
from pathlib import Path

from .format import FormatError, Reader, load_strings, require
from .references import extract_fort, summarize
from .static import convert
from .batch import batch, verify_bundle
from .harness import harness


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
    conversion = commands.add_parser('convert', help='convert a rigid BR2 to experimental GR2, FXSXML and DDS bundle')
    conversion.add_argument('source', type=Path)
    conversion.add_argument('--output', type=Path, required=True)
    conversion.add_argument('--diffuse', type=Path, required=True)
    conversion.add_argument('--sref', type=Path, required=True, help='explicit BuildingSREF candidate; visual semantics need game verification')
    conversion.add_argument('--name')
    conversion.add_argument('--units-per-meter', type=float, default=1)
    conversion.add_argument('--probe', type=Path, help='optional native OpenGR2 independent-probe')
    verification = commands.add_parser('verify', help='recheck a conversion bundle against its BR2 source')
    verification.add_argument('manifest', type=Path)
    verification.add_argument('--source', type=Path, required=True)
    batches = commands.add_parser('batch', help='convert a hash-pinned batch; rendering remains unverified')
    batches.add_argument('manifest', type=Path)
    batches.add_argument('--output', type=Path, required=True)
    batches.add_argument('--probe', type=Path)
    fixture = commands.add_parser('harness', help='stage a disposable renderer fixture without installing it')
    fixture.add_argument('manifest', type=Path)
    fixture.add_argument('--source', type=Path, required=True)
    fixture.add_argument('--output', type=Path, required=True)
    fixture.add_argument('--scale', type=float, default=6)
    args = parser.parse_args()
    try:
        if args.command == 'extract-fort':
            result = extract_fort(args.fpk, args.output)
        elif args.command == 'convert':
            result = convert(args.source, args.output, args.diffuse, args.sref,
                             name=args.name, probe=args.probe, units_per_meter=args.units_per_meter)
        elif args.command == 'verify':
            result = verify_bundle(args.manifest, args.source)
        elif args.command == 'batch':
            result = batch(args.manifest, args.output, probe=args.probe)
        elif args.command == 'harness':
            result = harness(args.manifest, args.source, args.output, args.scale)
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
