#!/usr/bin/env python3
"""Record installed farm layout handlers; never infer engine layout from a GR2."""
from pathlib import Path
import argparse
import hashlib
import json
import xml.etree.ElementTree as ET
from import_native_farms import OUT
from native_fpk import Archive


def audit(output):
    imported = json.loads((output/'native-import.json').read_text())
    game = Path(imported['source_installation'])
    archive = Archive(game/'Resource/Common/MiscData.fpk')
    raw = archive.read('civ5artdefines_landmarks.xml')
    rows = [{child.tag: child.text for child in row}
            for row in ET.fromstring(raw)
            if row.findtext('ImprovementType') == 'ART_DEF_IMPROVEMENT_FARM']
    relative = 'Assets/DLC/DLC_02/Features/Civ5ArtDefines_Landmarks_DLC_02.xml'
    terrace = (game/relative).read_bytes()
    terrace_rows = [{child.tag: child.text for child in row}
                    for row in ET.fromstring(terrace)
                    if row.findtext('ImprovementType') == 'ART_DEF_IMPROVEMENT_TERRACE_FARM']
    regular = [r for r in rows if r['ResourceType'] == 'ART_DEF_RESOURCE_NONE']
    assert len(regular) == 6
    assert all(r['LayoutHandler'] == 'FARM' and r['bTerrainContour'] == 'True' for r in regular)
    assert len(terrace_rows) == 3
    assert all(r['LayoutHandler'] == 'SNAPSHOT' and r['bTerrainContour'] == 'True' for r in terrace_rows)
    models = Archive(game/'Resource/Common/ImprovementModels.fpk')
    bindings = []
    for row in regular:
        wrapper = Path(row['FXSXML']).name.lower()
        data = models.read(wrapper)
        mesh = ET.fromstring(data).find('Mesh').attrib['file']
        bindings.append({'era': row['Era'], 'wrapper': wrapper, 'mesh': mesh,
                         'wrapper_sha256': hashlib.sha256(data).hexdigest()})
    return {'source_installation': str(game), 'engine_rendering_verified': False,
            'sources': [{'archive': 'Resource/Common/MiscData.fpk',
                         'entry': 'civ5artdefines_landmarks.xml', 'sha256': hashlib.sha256(raw).hexdigest()},
                        {'loose_asset': relative, 'sha256': hashlib.sha256(terrace).hexdigest()}],
            'ordinary_farm_rows': rows, 'terrace_rows': terrace_rows,
            'regular_farm_bindings': bindings,
            'correction': 'Authored crop parcels and terrain fixtures are not original game farm layouts.',
            'fixture_prop_mismatch': 'Medieval_Farm.gr2 is referenced by constructed wheat-resource farms; resource-free farms reference Medieval_Farm1/2/3.gr2.',
            'remaining_engine_work': 'Preserve FARM placement and terrace terrain contouring; establish in-game stock baselines before evaluating irrigation changes.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=OUT)
    args = parser.parse_args()
    report = audit(args.output.resolve())
    (args.output/'native-layout-audit.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
