#!/usr/bin/env python3
"""Export the selected Outpost B icons without regenerating approved artwork.

Only selected original art is read. Cropping, native cell padding, faint alpha
speck removal and resizing are deterministic export preparation. Game reference
pixels are never opened or copied. Requires Pillow (requirements-art.txt).
"""
from pathlib import Path
import hashlib
import json
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'shared/art/resource-outpost-icons-v1'
DEST = ROOT / 'mods/resource-outposts/src/Art'
PREVIEW = ROOT / 'output/art-concepts/2026-10-09/resource-outposts-round-1/exported'
PORTRAIT_SIZES = (32, 45, 64, 80, 128, 214, 256)
ACTION_SIZES = (32, 45, 64)


def selected_image(selection):
    path = SOURCE / selection['source']
    assert hashlib.sha256(path.read_bytes()).hexdigest() == selection['sha256'], \
        f'Approved source changed: {path}'
    im = Image.open(path).convert('RGBA')
    x, y, width, height = selection['review_crop']
    im = im.crop((x, y, x + width, y + height))
    # Discard only near-invisible alpha noise, retaining the reviewed silhouette
    # and all visible edge pixels. No recoloring or architectural changes.
    im.putalpha(im.getchannel('A').point(lambda a: 0 if a < 8 else a))
    return im


def cell(im, size, aperture):
    extent = round(size * aperture)
    scale = extent / max(im.size)
    width, height = max(1, round(im.width * scale)), max(1, round(im.height * scale))
    tile = im.resize((width, height), Image.Resampling.LANCZOS)
    out = Image.new('RGBA', (size, size))
    out.paste(tile, ((size - width) // 2, (size - height) // 2))
    return out


def export():
    manifest = json.loads((SOURCE / 'selections.json').read_text())
    chosen = {s['id']: s for s in manifest['selections']}
    emblem, worker = selected_image(chosen['emblem']), selected_image(chosen['construction'])
    DEST.mkdir(parents=True, exist_ok=True)
    PREVIEW.mkdir(parents=True, exist_ok=True)
    files = []

    def save(im, name, role):
        path = DEST / name
        im.save(path, format='DDS')
        decoded = Image.open(path).convert('RGBA')
        assert decoded.size == im.size and decoded.tobytes() == im.tobytes()
        assert decoded.getchannel('A').getextrema() == (0, 255)
        # QA previews come from the actual DDS, not from the pre-export PNG.
        decoded.save(PREVIEW / (path.stem + '.png'))
        files.append({'file': 'Art/' + name, 'role': role, 'size': list(im.size),
                      'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})

    for size in PORTRAIT_SIZES:
        save(cell(emblem, size, 176 / 256), f'RO_OutpostPortrait{size}.dds', 'emblem')
    for size in ACTION_SIZES:
        save(cell(worker, size, .78), f'RO_OutpostAction{size}.dds', 'construction')
    # Native Fort strategic texture has a 170px alpha aperture in a 256px cell.
    save(cell(emblem, 256, 170 / 256), 'RO_OutpostStrategic.dds', 'strategic view')
    report = {'format': 'legacy A8R8G8B8 DDS; straight alpha; no mipmaps',
              'selection_manifest': str((SOURCE / 'selections.json').relative_to(ROOT)),
              'preparation': 'reviewed crops; alpha below 8 removed; proportional Lanczos resize; centered transparent padding',
              'source_sha256': {s['source']: s['sha256'] for s in chosen.values()},
              'files': files, 'native_rendering': 'pending in-game verification'}
    (SOURCE / 'exports.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f'Exported and losslessly decoded {len(files)} Outpost DDS textures into {DEST}')


if __name__ == '__main__':
    export()
