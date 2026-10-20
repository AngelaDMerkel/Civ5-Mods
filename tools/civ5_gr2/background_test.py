"""Bounded stock-game GR2 scene using a locally checked-out Lekmod test harness.

This is optional native test infrastructure, never a conversion dependency.
External harness sources and generated stock UI copies remain in ignored output.
Run with the game closed; see README.md for setup and evidence interpretation.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET

from tools.civ5_test_lock import native_test_lock

REPO = Path(__file__).resolve().parents[2]
HARNESS_REVISION = '181b7232160a5661424c275f2a62deb5c56a7a34'
APP = Path.home() / "Library/Application Support/Steam/steamapps/common/Sid Meier's Civilization V/Civilization V.app"
DATA = Path.home() / 'Library/Application Support/Sid Meier\'s Civilization 5'
DOMAIN = 'com.aspyr.civ5xp.steam'
LEGACY_DATA_FOLDERS = ('Saves', 'ModdedSaves', 'cache', 'Logs')
DATA_FOLDERS = (*LEGACY_DATA_FOLDERS, 'ModUserData')
SETTINGS = ('config.ini', 'UserSettings.ini', 'GraphicsSettingsDX9.ini')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory(root):
    return {p.relative_to(root).as_posix(): digest(p)
            for p in sorted(root.rglob('*')) if p.is_file()}


def save_report(output, report):
    (output / 'session.json').write_text(json.dumps(report, indent=2) + '\n')


def load_harness(checkout):
    head = subprocess.check_output(['git', '-C', str(checkout), 'rev-parse', 'HEAD'], text=True).strip()
    dirty = subprocess.check_output(['git', '-C', str(checkout), 'status', '--porcelain'], text=True)
    if head != HARNESS_REVISION or dirty:
        raise ValueError('Harness must be clean at ' + HARNESS_REVISION)
    path = checkout / 'LEKMOD_DLL/macos/automated-playtest.py'
    sys.path.insert(0, str(path.parent))
    try:
        spec = importlib.util.spec_from_file_location('cg2_external_harness', path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


def start_parameters(load_save=None):
    return {
        '__TEST_LOAD_PATH__': json.dumps(str(load_save)) if load_save else 'nil', '__TEST_WORLD_SIZE__': 'WORLDSIZE_DUEL',
        '__TEST_MINORS__': '0', '__TEST_MAP_SCRIPT__': 'CG2_StaticTest.lua',
        '__TEST_GAME_SPEED__': 'GAMESPEED_QUICK', '__TEST_START_ERA__': 'ERA_ANCIENT',
        '__TEST_GAME_TURN_LIMIT__': '0', '__TEST_GAME_OPTIONS__': '{}',
        '__TEST_MAJORS__': '2', '__TEST_HANDICAP__': 'HANDICAP_PRINCE',
        '__TEST_AUTOPLAY__': 'false', '__TEST_CIVILIZATION__': 'CIVILIZATION_ROME',
        '__TEST_OPPONENT_CIVILIZATION__': 'CIVILIZATION_GREECE',
        '__TEST_SLOT_CIVILIZATIONS__': '{}', '__TEST_SLOT_TEAMS__': '{}',
        '__TEST_TURNS__': '0', '__TEST_FUNCTIONAL__': 'true',
    }


def render_template(source, load_save=None):
    text = source.read_text()
    for key, value in start_parameters(load_save).items():
        text = text.replace(key, value)
    if re.search(r'__TEST_\w+__', text):
        raise ValueError('Unresolved external harness parameter')
    return text.encode()


def mod_payloads(stages, data):
    """Only add new, uniquely identified diagnostic mod folders; never replace."""
    existing = {}
    for path in (data / 'MODS').rglob('*.modinfo'):
        root = ET.parse(path).getroot()
        existing[root.get('id', '').lower()] = str(path)
    result = []
    for stage in stages:
        source = stage.resolve()
        manifests = list(source.glob('*.modinfo'))
        if len(manifests) != 1:
            raise ValueError('A diagnostic mod stage needs exactly one manifest')
        root = ET.parse(manifests[0]).getroot()
        mod_id, version = root.get('id', '').lower(), root.get('version', '')
        if not re.fullmatch(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', mod_id) or not version.isdigit():
            raise ValueError('Invalid diagnostic mod identity')
        target = data / 'MODS' / ('CG2_Native_' + mod_id)
        if mod_id in existing or target.exists():
            raise ValueError('Refusing an existing mod identity or test folder: ' + mod_id)
        existing[mod_id] = str(source)
        result.append(dict(id=mod_id, version=int(version), source=str(source),
                           target=str(target), payload=inventory(source)))
    return result


def activate_mods(code, mods):
    if not mods:
        return code
    marker = b'print("[LEKMOD_TEST] starting unattended match")'
    if code.count(marker) != 1:
        raise ValueError('External fresh-game activation hook changed')
    lines = ['-- Activate only the temporary diagnostic stages; cache is restored afterward.',
             'for _,m in pairs(Modding.GetModBrowserInstalledListings()) do',
             '  Modding.DisableMod(m.ModId, m.Version)', 'end']
    for mod in mods:
        lines.append(f'Modding.EnableMod("{mod["id"]}", {mod["version"]})')
    lines += ['Modding.ActivateEnabledMods()', 'local active={}',
              'for _,m in pairs(Modding.GetActivatedMods()) do active[string.lower(m.ID)]=true end']
    for mod in mods:
        lines.append(f'assert(active["{mod["id"]}"], "[ROTEST] FAIL ordinary mod activation {mod["id"]}")')
    lines.append('print("[ROTEST] ordinary mod activation verified")')
    return code.replace(marker, marker + b'\n' + '\n'.join(lines).encode())


def restore(output, report, harness):
    if harness.game_pids():
        raise RuntimeError('Close Civ V before restoration')
    app, data, target = (Path(report[k]) for k in ('app', 'data', 'target'))
    # Fail closed on any independently changed binary, UI hook or test payload.
    for rel, sha in report['binaries'].items():
        if digest(app / rel) != sha:
            raise RuntimeError('Game binary changed; retained recovery journal')
    for rel, sha in report.get('installed_hooks', {}).items():
        path = app / rel
        original = report['ui_originals'][rel]
        allowed = {sha, original}
        if path.exists() and digest(path) not in allowed:
            raise RuntimeError('UI changed during test: ' + rel)
    if target.exists() and inventory(target) != report['payload']:
        raise RuntimeError('Test DLC changed during test; retained recovery journal')
    for mod in report.get('temporary_mods', []):
        path = Path(mod['target'])
        if path.exists() and inventory(path) != mod['payload']:
            raise RuntimeError('Diagnostic mod changed during test; retained recovery journal')
    for rel, sha in report['originals'].items():
        if digest(output / 'backup' / rel) != sha:
            raise RuntimeError('Recovery backup changed: ' + rel)
    for rel, sha in report['ui_originals'].items():
        if sha is not None and digest(output / 'ui-original' / rel) != sha:
            raise RuntimeError('UI backup changed: ' + rel)
    for folder in report.get('data_folders', LEGACY_DATA_FOLDERS):
        for path in list((data / folder).rglob('*')):
            if not path.is_file():
                continue
            rel = path.relative_to(data).as_posix()
            if folder == 'Logs' or digest(path) != report['originals'].get(rel):
                dest = output / 'after' / rel
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, dest)
            if rel not in report['originals']:
                path.unlink()
    for rel in report['originals']:
        dest = data / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(output / 'backup' / rel, dest)
    for rel, sha in report['ui_originals'].items():
        path = app / rel
        if sha is None:
            path.unlink(missing_ok=True)
        else:
            shutil.copy2(output / 'ui-original' / rel, path)
    if target.exists():
        shutil.rmtree(target)
    for mod in report.get('temporary_mods', []):
        path = Path(mod['target'])
        if path.exists():
            shutil.rmtree(path)
    display = report['display_before']
    command = ['defaults', 'write', DOMAIN, 'DisplayFullScreen', '-bool', display['value']]
    if not display['existed']:
        command = ['defaults', 'delete', DOMAIN, 'DisplayFullScreen']
    subprocess.run(command, check=True, capture_output=True)
    if any(digest(data / rel) != sha for rel, sha in report['originals'].items()):
        raise RuntimeError('Restoration verification failed')
    report['restored'] = True
    report['restored_original_files'] = len(report['originals'])
    save_report(output, report)


def run(args, harness):
    output = args.output.resolve()
    if output.exists():
        raise ValueError('Use a new evidence directory')
    if harness.game_pids():
        raise ValueError('Civ V must be closed')
    harness.require_unlocked_desktop()
    harness.require_existing_steam_session()
    source = args.dlc.resolve()
    load_save = args.load_save.resolve() if args.load_save else None
    if load_save and (not load_save.is_file() or load_save.suffix.lower() != '.civ5save'):
        raise ValueError('Load requires an existing diagnostic .Civ5Save file')
    if not (source / 'Maps/CG2_StaticTest.lua').is_file() or not (source / 'Files/CG2_Scene.lua').is_file():
        raise ValueError('Expected the WSDLC-packaged CG2 render fixture')
    assets = APP / 'Contents/Assets/Assets'
    target = assets / 'DLC/CG2_StaticRenderTest'
    map_path = assets / 'Maps/CG2_StaticTest.lua'
    if target.exists() or map_path.exists():
        raise ValueError('Refusing an existing CG2 test installation')
    mods = mod_payloads(args.mod_stage, DATA)
    output.mkdir(parents=True)
    external = Path(harness.__file__).parent
    lib = output / 'background-playtest.dylib'
    subprocess.run(['clang', '-arch', 'x86_64', '-dynamiclib', '-framework', 'AppKit',
                    '-framework', 'Foundation', str(external / 'background-playtest.m'),
                    '-o', str(lib)] + (['-DLEKMOD_TEST_ACTIVATION_ONLY'] if args.activation_only else []), check=True)
    capture = harness.REPO / 'build/macos/capture-test-window'
    capture.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['clang', '-fobjc-arc', '-framework', 'AppKit', '-framework', 'Foundation',
                    '-framework', 'CoreGraphics', '-framework', 'ScreenCaptureKit',
                    '-framework', 'ImageIO', str(external / 'capture-test-window.m'),
                    '-o', str(capture)], check=True)
    frontend = assets / 'UI/FrontEnd'
    # Register the guarded scene in the loading context before its completion
    # callback. This also covers stock UI skins that ignore DLC InGame overrides.
    hooks = {frontend / 'MainMenu.lua': activate_mods(render_template(external / 'playtest-start.lua', load_save), mods),
             frontend / 'LoadScreen.lua': (source / 'Files/CG2_Scene.lua').read_bytes() + b'\n' + render_template(external / 'playtest-loaded.lua'),
             # Only this disposable launch. No global input or window activation.
             frontend / 'LegalScreen.lua': b'\ndo local elapsed=0; ContextPtr:SetUpdate(function(dt) if not ContextPtr:IsHidden() then elapsed=elapsed+dt; if elapsed>1 then UIManager:DequeuePopup(ContextPtr); ContextPtr:ClearUpdate() end end end) end\n',
             map_path: (source / 'Maps/CG2_StaticTest.lua').read_bytes()}
    report = {'app': str(APP), 'data': str(DATA), 'target': str(target),
              'started_utc': datetime.now(timezone.utc).isoformat(),
              'harness_revision': HARNESS_REVISION, 'background': True,
              'activation_only': args.activation_only,
              'data_folders': DATA_FOLDERS,
              'native_rendering': 'unverified', 'status': 'prepared', 'restored': False,
              'payload': inventory(source), 'originals': {}, 'ui_originals': {}, 'binaries': {}}
    report['temporary_mods'] = mods
    if load_save:
        report['load_save'] = {'path': str(load_save), 'sha256': digest(load_save)}
    display = subprocess.run(['defaults', 'read', DOMAIN, 'DisplayFullScreen'], capture_output=True, text=True)
    report['display_before'] = {'existed': display.returncode == 0,
                               'value': 'true' if display.stdout.strip() == '1' else 'false'}
    files = [p for folder in DATA_FOLDERS for p in (DATA / folder).rglob('*') if p.is_file()]
    files += [DATA / name for name in SETTINGS]
    for path in files:
        rel = path.relative_to(DATA).as_posix()
        dest = output / 'backup' / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, dest)
        report['originals'][rel] = digest(dest)
    for path in hooks:
        rel = path.relative_to(APP).as_posix()
        report['ui_originals'][rel] = digest(path) if path.exists() else None
        if path.exists():
            dest = output / 'ui-original' / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(path, dest)
    for rel in ('Contents/MacOS/Civilization V', 'Contents/MacOS/libCvGameCoreDLL_Expansion2_DLL.dylib'):
        report['binaries'][rel] = digest(APP / rel)
    save_report(output, report)
    process = None
    try:
        shutil.copytree(source, target)
        for mod in mods:
            shutil.copytree(mod['source'], mod['target'])
        config = DATA / 'config.ini'
        config.write_text(harness.edit_ini(config.read_text(), {
            ('CONFIG', 'QuickStart'): 0, ('CONFIG', 'SyncRandSeed'): 12345,
            ('CONFIG', 'MapRandSeed'): 67890, ('DEBUG', 'Autorun'): 0,
            ('DEBUG', 'LoggingEnabled'): 1}))
        settings = DATA / 'UserSettings.ini'
        settings.write_bytes(re.sub(rb'(?m)^(SkipIntroVideo\s*=\s*)[^\r\n]*',
                                    rb'\g<1>1', settings.read_bytes()))
        report['installed_hooks'] = {}
        for path, code in hooks.items():
            contents = (path.read_bytes() if path.exists() else b'') + b'\n' + code
            rel = path.relative_to(APP).as_posix()
            report['installed_hooks'][rel] = hashlib.sha256(contents).hexdigest()
            save_report(output, report)
            path.write_bytes(contents)
        subprocess.run(['defaults', 'write', DOMAIN, 'DisplayFullScreen', '-bool', 'false'], check=True)
        env = {**os.environ, 'DYLD_INSERT_LIBRARIES': str(lib), 'SteamAppId': '8930', 'SteamGameId': '8930'}
        harness.require_unlocked_desktop()
        with (output / 'process.log').open('w') as log:
            process = subprocess.Popen([str(APP / 'Contents/MacOS/Civilization V')],
                cwd=APP / 'Contents/MacOS', env=env, stdin=subprocess.DEVNULL, stdout=log, stderr=log)
        report.update(pid=process.pid, status='running')
        save_report(output, report)
        print(json.dumps({'event': 'background-launched', 'pid': process.pid, 'evidence': str(output)}), flush=True)
        start = time.monotonic()
        ready = None
        last_capture = 0
        while time.monotonic() - start < args.timeout:
            elapsed = time.monotonic() - start
            if process.poll() is not None:
                report.update(status='game-exited', exit_code=process.returncode)
                break
            lua = DATA / 'Logs/Lua.log'
            text = lua.read_text(errors='replace') if lua.exists() else ''
            failure = next((marker for marker in args.fail_marker if marker in text), None)
            if failure:
                report.update(status='native-check-failed', failure_marker=failure)
                print(json.dumps({'event': 'native-check-failed', 'marker': failure}), flush=True)
                break
            if '[CG2] scene-ready' in text and ready is None:
                ready = elapsed
                print(json.dumps({'event': 'scene-placed', 'elapsed': round(elapsed)}), flush=True)
            if elapsed - last_capture > 90 or (ready is not None and elapsed - ready > 20):
                name = 'scene.png' if ready is not None else f'progress-{int(elapsed)}.png'
                captured = harness.capture_game_window(process.pid, output / name)
                report['last_capture'] = {'file': name, 'success': captured}
                status = harness.command([str(harness.window_helper()), '--process-status', str(process.pid)])
                if status.returncode == 0:
                    state = json.loads(status.stdout)
                    report['background_observation'] = {key: state.get(key) for key in ('pid', 'active', 'activation_policy')}
                last_capture = elapsed
                print(json.dumps({'event': 'capture', **report['last_capture']}), flush=True)
                save_report(output, report)
                if ready is not None:
                    report['status'] = 'scene-placed-capture-unreviewed'
                    break
            time.sleep(2)
        else:
            report['status'] = 'timeout'
    except KeyboardInterrupt:
        report['status'] = 'interrupted'
    except Exception as error:
        report.update(status='runner-error', error=str(error))
        raise
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=8)
        save_report(output, report)
        restore(output, report, harness)
        print(json.dumps({'status': report['status'], 'restored': report['restored']}), flush=True)
    return 0 if report['status'] == 'scene-placed-capture-unreviewed' and report['last_capture']['success'] else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--harness', type=Path, default=REPO / 'output/gr2-research/upstream/lekmod-harness')
    parser.add_argument('--dlc', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--timeout', type=int, default=600)
    parser.add_argument('--activation-only', action='store_true', help='Disable upstream diagnostic interposers, retain background guard')
    parser.add_argument('--load-save', type=Path, help='Reload a retained disposable fixture save; scene guards still apply')
    parser.add_argument('--fail-marker', action='append', default=[], help='Stop and restore when this diagnostic log marker appears')
    parser.add_argument('--mod-stage', type=Path, action='append', default=[],
                        help='Temporarily install and normally activate a diagnostic mod stage')
    parser.add_argument('--restore', action='store_true', help='Recover an interrupted session with Civ V closed')
    args = parser.parse_args()
    if not args.restore and (args.dlc is None or not 60 <= args.timeout <= 1200):
        parser.error('Run requires --dlc and timeout between 60 and 1200 seconds')
    harness = load_harness(args.harness.resolve())
    with native_test_lock('GR2 background renderer', args.output):
        if args.restore:
            restore(args.output, json.loads((args.output / 'session.json').read_text()), harness)
        else:
            raise SystemExit(run(args, harness))


if __name__ == '__main__':
    main()
