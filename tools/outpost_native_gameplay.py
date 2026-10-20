#!/usr/bin/env python3
"""Stage production Outposts UI/runtime for guarded, disposable native tests.

The DLC transport is diagnostic only. It does not test the ordinary mod loader.
Production UI XML is unchanged; its Lua copy receives one test include at EOF.
"""
import argparse
import hashlib
import json
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

from build import manifest, write_xml
from civ5_gr2.harness import FIXTURE_ID, FIXTURES
from outpost_native_production import ROOT, SOURCE, prepare
from packages import PACKAGES, package_files, RO_ID


def stage(database, output, scenario='core'):
    prepare(database, output)
    for path in (SOURCE / 'Lua').glob('*.lua'):
        shutil.copyfile(path, output / 'Lua' / path.name)
    shutil.copytree(SOURCE / 'UI', output / 'UI')
    checks = ROOT / 'mods/resource-outposts/tests/native'
    shutil.copyfile(checks / 'RO_AdvancedChecks.lua', output / 'Lua/RO_AdvancedChecks.lua')
    shutil.copyfile(checks / 'RO_GameplayScene.lua', output / 'Lua/CG2_Scene.lua')
    (output / 'Lua/RO_GameplayChecks.lua').write_text(
        (checks / 'RO_GameplayChecks.lua').read_text().replace('__RO_SCENARIO__', scenario))
    with (output / 'UI/RO_UI.lua').open('a') as ui:
        ui.write('\n-- Disposable native fixture only; never packaged for play.\ninclude("RO_GameplayChecks");\n')
    # Rebuild the temporary manifest. The packer cannot translate XML-context
    # entrypoints, so the guarded scene loads the original context explicitly.
    (output / 'Outpost Production Art Probe.modinfo').unlink()
    (output / 'Outpost Production Art Probe.civ5proj').unlink()
    files = {p.relative_to(output).as_posix(): p for p in sorted(output.rglob('*'))
             if p.is_file() and p.name != 'fixture.json'}
    spec = dict(id=FIXTURE_ID, version=1, name='Outpost Native Gameplay Probe',
                description='Disposable gameplay checks using production UI and runtime.',
                actions=['Text/RO_Text.xml', 'XML/CG2_Production.xml'], entry='Lua/CG2_Scene.lua')
    mod = manifest(files, spec)
    mod.find('References').clear(); mod.find('Blocks').clear()
    for item in mod.find('Files'):
        if item.text.startswith('UI/'):
            item.set('import', '1')
    entry = ET.SubElement(mod.find('EntryPoints'), 'EntryPoint',
                          type='MapScript', file='Maps/CG2_StaticTest.lua')
    ET.SubElement(entry, 'Name').text = 'Outpost gameplay probe'
    ET.SubElement(entry, 'Description').text = 'Disposable native checks only.'
    write_xml(mod, output / 'Outpost Native Gameplay Probe.modinfo')
    evidence = json.loads((output / 'fixture.json').read_text())
    evidence.update(scope='Native production UI/runtime via temporary DLC; ordinary mod activation excluded', scenario=scenario,
                    instrumentation='Append include("RO_GameplayChecks") to the fixture UI Lua copy only',
                    fixture_hashes={name: hashlib.sha256(path.read_bytes()).hexdigest()
                                    for name, path in files.items()})
    (output / 'fixture.json').write_text(json.dumps(evidence, indent=2) + '\n')


def ordinary(output, scenario):
    """Keep SQL, imports, UUIDs and UI entries on the ordinary mod-loader path."""
    if output.exists():
        raise ValueError('Use a new ordinary-mod fixture directory')
    source = output / 'transport'
    (source / 'Lua').mkdir(parents=True); (source / 'Maps').mkdir()
    checks = ROOT / 'mods/resource-outposts/tests/native'
    (source / 'Lua/CG2_Scene.lua').write_text((checks / 'RO_OrdinaryScene.lua').read_text())
    if scenario == 'integration':
        shutil.copyfile(checks / 'RO_IncludeProbe.lua', source / 'Lua/RO_IncludeProbe.lua')
        with (source / 'Lua/CG2_Scene.lua').open('a') as scene:
            scene.write('\nEvents.SequenceGameInitComplete.Add(function() ContextPtr:LoadNewContext("RO_IncludeProbe"); end);\n')
    shutil.copyfile(FIXTURES / 'CG2_StaticTest.lua', source / 'Maps/CG2_StaticTest.lua')
    files = {p.relative_to(source).as_posix(): p for p in sorted(source.rglob('*')) if p.is_file()}
    spec = dict(id=FIXTURE_ID, version=1, name='Outpost Ordinary Loader Probe',
                description='Only the diagnostic map and loader checks; gameplay comes from normal mods.',
                actions=[], entry='Lua/CG2_Scene.lua')
    mod = manifest(files, spec); mod.find('References').clear(); mod.find('Blocks').clear()
    entry = ET.SubElement(mod.find('EntryPoints'), 'EntryPoint', type='MapScript', file='Maps/CG2_StaticTest.lua')
    ET.SubElement(entry, 'Name').text = 'Outpost ordinary loader probe'
    ET.SubElement(entry, 'Description').text = 'Disposable scene only.'
    write_xml(mod, source / 'Outpost Ordinary Loader Probe.modinfo')
    hashes = {}
    for package in PACKAGES:
        if scenario not in ('integration', 'ui_terrain') and package['id'] != RO_ID:
            continue
        target = output / 'mods' / package['slug']
        original = package_files(package)
        hashes[package['slug']] = {name: hashlib.sha256(path.read_bytes()).hexdigest() for name, path in original.items()}
        for name, path in original.items():
            dest = target / name; dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, dest)
        if package['id'] == RO_ID:
            shutil.copyfile(checks / 'RO_AdvancedChecks.lua', target / 'Lua/RO_AdvancedChecks.lua')
            (target / 'Lua/RO_GameplayChecks.lua').write_text(
                (checks / 'RO_GameplayChecks.lua').read_text().replace('__RO_SCENARIO__', scenario))
            with (target / 'UI/RO_UI.lua').open('a') as ui:
                ui.write('\n-- Disposable fixture only.\ninclude("RO_GameplayChecks");\n')
        else:
            with (target / 'UI/RT_Environment.lua').open('a') as ui:
                ui.write('\n-- Read-only diagnostic bridge; never packaged for play.\n' +
                         (checks / 'RO_TerrainProbe.lua').read_text())
        files = {p.relative_to(target).as_posix(): p for p in sorted(target.rglob('*')) if p.is_file()}
        write_xml(manifest(files, package), target / (package['name'] + '.modinfo'))
    (output / 'fixture.json').write_text(json.dumps(dict(scenario=scenario, source_hashes=hashes,
        scope='Ordinary mod activation and production SQL/UI/runtime; test checks appended only to fixture UI copies'), indent=2) + '\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--scenario', choices=('core', 'persistence', 'ai', 'integration', 'recovery', 'threat', 'ui', 'ui_terrain'), default='core')
    parser.add_argument('--ordinary-mods', action='store_true')
    args = parser.parse_args()
    if args.ordinary_mods:
        ordinary(args.output, args.scenario)
    else:
        if not args.database or args.scenario in ('integration', 'ui_terrain'):
            parser.error('DLC fixture needs --database; integration requires --ordinary-mods')
        stage(args.database, args.output, args.scenario)
