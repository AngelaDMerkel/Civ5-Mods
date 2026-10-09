#!/usr/bin/env python3
"""Deterministically crop/size the selected art for Civ V; never regenerate it.

Requires Pillow. Game exports are legacy, lossless A8R8G8B8 DDS with straight
alpha and no mipmaps. This preserves small UI details and works without DX10.
The original Civ V comparison images are deliberately never opened or packaged.
"""
from pathlib import Path
import hashlib
import json
from PIL import Image, ImageChops, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SOURCES = ROOT / 'shared/art/terrain-icons-round-3'
DEST = ROOT / 'mods/realistic-terrain/src/Art'
PORTRAIT_SIZES = (32, 45, 64, 80, 128, 214, 256)
ACTION_SIZES = (32, 45, 64)


def selected_image(selection):
    image = Image.open(SOURCES / selection['source']).convert('RGBA')
    if selection['review_crop']:
        x, y, w, h = selection['review_crop']
        image = image.crop((x, y, x + w, y + h))
    return image


def export():
    DEST.mkdir(exist_ok=True)
    manifest = json.loads((SOURCES / 'selections.json').read_text())
    chosen = {s['id']: s for s in manifest['selections']}
    portraits = []
    for name in ('logistics', 'ministry', 'caravansary'):
        im = selected_image(chosen[name])
        # Match the reviewed circular aperture and remove outer alpha specks.
        mask = Image.new('L', im.size)
        ImageDraw.Draw(mask).ellipse((0, 0, im.width - 1, im.height - 1), fill=255)
        im.putalpha(ImageChops.multiply(im.getchannel('A'), mask))
        portraits.append(im)
    files = []

    def save(im, name):
        path = DEST / name
        im.save(path, format='DDS')
        # Decode the actual game file, not an intermediate PNG, for QA.
        decoded = Image.open(path).convert('RGBA')
        assert decoded.size == im.size and decoded.tobytes() == im.tobytes()
        files.append({'file': 'Art/' + name, 'size': list(im.size),
                      'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})

    for size in PORTRAIT_SIZES:
        atlas = Image.new('RGBA', (size * 4, size))
        diameter = round(size * 176 / 256)  # native portrait's 40px inset at 256
        inset = (size - diameter) // 2
        for index, im in enumerate(portraits):
            tile = im.resize((diameter, diameter), Image.Resampling.LANCZOS)
            atlas.paste(tile, (index * size + inset, inset))
        save(atlas, f'RT_Portraits{size}.dds')
    glyph = selected_image(chosen['worker'])
    for size in ACTION_SIZES:
        icon = Image.new('RGBA', (size, size))
        diameter = round(size * 0.78)
        inset = (size - diameter) // 2
        icon.paste(glyph.resize((diameter, diameter), Image.Resampling.LANCZOS), (inset, inset))
        save(icon, f'RT_CaravansaryAction{size}.dds')
    # Native wonder art is 976x576; use a proportional fill with a <2px edge crop.
    from PIL import ImageOps
    painting = ImageOps.fit(selected_image(chosen['wonder']), (976, 576), method=Image.Resampling.LANCZOS)
    save(painting, 'RT_MinistryOfCoin_Wonder.dds')
    report = {'format': 'legacy A8R8G8B8 DDS; straight alpha; no mipmaps',
              'selection_manifest': str((SOURCES / 'selections.json').relative_to(ROOT)),
              'source_sha256': {s['source']: hashlib.sha256((SOURCES / s['source']).read_bytes()).hexdigest()
                                for s in chosen.values()}, 'files': files}
    (SOURCES / 'exports.json').write_text(json.dumps(report, indent=2) + '\n')
    print(f'Exported and losslessly decoded {len(files)} DDS textures into {DEST}')


if __name__ == '__main__':
    export()
