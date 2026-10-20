#!/usr/bin/env python3
"""Opt-in, bounded Mac GameCore startup test; restores every temporary game change.

Uses only startup/background/capture helpers from the pinned existing port. It
does not invoke its installer, WSDLC or any Lekmod gameplay/content.
"""
import argparse
from datetime import datetime, timezone
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import time
import uuid

sys.dont_write_bytecode = True
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from tools.civ5_test_lock import LOCK_PATH, native_test_lock
from native_session import Session, digest, DATA_FOLDERS
from native_mods import prepare_mods, install_mods, verify_mods, activate_mods

HARNESS_REVISION = '181b7232160a5661424c275f2a62deb5c56a7a34'
APP = Path.home() / "Library/Application Support/Steam/steamapps/common/Sid Meier's Civilization V/Civilization V.app"
DATA = Path.home() / "Library/Application Support/Sid Meier's Civilization 5"
DOMAIN = 'com.aspyr.civ5xp.steam'
CORE = 'Contents/MacOS/libCvGameCoreDLL_Expansion2_DLL.dylib'
HOST = 'Contents/MacOS/Civilization V'


def module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(value)
    finally:
        sys.path.pop(0)
    return value


def load_harness(path):
    head = subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True).strip()
    dirty = subprocess.check_output(['git', '-C', str(path), 'status', '--porcelain'], text=True)
    if head != HARNESS_REVISION or dirty:
        raise ValueError('Use a clean test harness checkout at ' + HARNESS_REVISION)
    return module(path / 'LEKMOD_DLL/macos/automated-playtest.py', 'c5m_native_harness')


def readiness(harness):
    if harness.game_pids():
        raise RuntimeError('Civ V is running; no files changed')
    harness.require_existing_steam_session()
    harness.require_unlocked_desktop()


def validate_build(binary, app):
    lock = json.loads((REPO / 'gamecore/compat.lock.json').read_text())
    compat = REPO / 'gamecore/.compat' / lock['commit']
    # This test does not fetch dependencies or alter an installed executable.
    head = subprocess.check_output(['git', '-C', str(compat), 'rev-parse', 'HEAD'], text=True).strip()
    dirty = subprocess.check_output(['git', '-C', str(compat), 'status', '--porcelain'], text=True)
    if head != lock['commit'] or dirty:
        raise ValueError('Compatibility checkout is missing, dirty or at the wrong revision')
    result = module(compat / 'tools/validate.py', 'c5m_native_validator').validate(binary, app=app)
    abi = json.loads((compat / 'abi/aspyr-bnw.json').read_text())
    if digest(app / CORE) not in abi['stock_gamecore_sha256']:
        raise ValueError('Baseline test requires the verified stock installed GameCore')
    report = json.loads(binary.with_name('build-report.json').read_text())
    if report['binary_sha256'] != result['sha256'] or report['compat_commit'] != lock['commit']:
        raise ValueError('Binary does not match its build provenance')
    if report['source_dirty']:
        raise ValueError('Use a committed, clean developer build')
    return {'validation': result, 'build': report, 'host_sha256': digest(app / HOST)}


def startup(source):
    values = {
        '__TEST_LOAD_PATH__': 'nil', '__TEST_WORLD_SIZE__': 'WORLDSIZE_DUEL',
        '__TEST_MINORS__': '0', '__TEST_MAP_SCRIPT__': 'Continents.lua',
        '__TEST_GAME_SPEED__': 'GAMESPEED_QUICK', '__TEST_START_ERA__': 'ERA_ANCIENT',
        '__TEST_GAME_TURN_LIMIT__': '0', '__TEST_GAME_OPTIONS__': '{}',
        '__TEST_MAJORS__': '2', '__TEST_HANDICAP__': 'HANDICAP_PRINCE',
        '__TEST_AUTOPLAY__': 'false', '__TEST_CIVILIZATION__': 'CIVILIZATION_ROME',
        '__TEST_OPPONENT_CIVILIZATION__': 'CIVILIZATION_GREECE',
        '__TEST_SLOT_CIVILIZATIONS__': '{}', '__TEST_SLOT_TEAMS__': '{}',
    }
    text = source.read_text()
    for key, value in values.items():
        text = text.replace(key, value)
    if re.search(r'__TEST_\w+__', text):
        raise ValueError('Unresolved startup parameter')
    return text.encode()


def outcome(text, run):
    rows = re.findall(r'\[C5M_NATIVE\] run=' + re.escape(run) + r' status=(PASS|FAIL)\b', text)
    return 'FAIL' if 'FAIL' in rows else ('PASS' if rows == ['PASS'] else None)


def prior_recovery(path):
    if path.exists():
        report = json.loads(path.read_text())
        if not report.get('restored') and report.get('state') != 'restored':
            raise RuntimeError('Recover the previous native session before testing: ' + str(path))


def display_state():
    result = subprocess.run(['defaults', 'read', DOMAIN, 'DisplayFullScreen'], capture_output=True, text=True)
    if result.returncode == 0 and result.stdout.strip() not in ('0', '1'):
        raise RuntimeError('Unexpected DisplayFullScreen preference type')
    return {'existed': result.returncode == 0, 'value': result.stdout.strip() == '1'}


def restore(session, harness):
    if harness.game_pids():
        raise RuntimeError('Close Civ V before restoring the journal')
    if digest(Path(session.report['app']) / HOST) != session.report['host_sha256']:
        raise RuntimeError('Host executable changed independently; retain recovery evidence')
    verify_mods(session.report.get('temporary_mods', []), Path(session.report['data']))
    session.restore_files()
    before = session.report['display_before']
    now = display_state()
    if now != before:
        args = ['defaults', 'write', DOMAIN, 'DisplayFullScreen', '-bool', str(before['value']).lower()]
        if not before['existed']:
            args = ['defaults', 'delete', DOMAIN, 'DisplayFullScreen']
        subprocess.run(args, check=True, capture_output=True)
    if display_state() != before:
        raise RuntimeError('Display preference restoration verification failed')
    session.report['restored'] = True
    session.save()


def compile_helpers(harness, directory, host_stat):
    external = Path(harness.__file__).parent
    background = directory / 'background.dylib'
    command = ['clang', '-arch', 'x86_64', '-dynamiclib', '-framework', 'AppKit',
               '-framework', 'Foundation', str(external / 'background-playtest.m'), '-o', str(background)]
    if host_stat:
        command.append('-DLEKMOD_TEST_EXTERNAL_LEGACY_STAT')
    subprocess.run(command, check=True)
    libraries = [background]
    if host_stat:
        correction = directory / 'host-stat.dylib'
        subprocess.run(['clang', '-arch', 'x86_64', '-dynamiclib', '-O2',
                        str(external / 'host-stat-compat.c'), '-o', str(correction)], check=True)
        libraries.append(correction)
    capture = harness.REPO / 'build/macos/capture-test-window'
    capture.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['clang', '-fobjc-arc', '-framework', 'AppKit', '-framework', 'Foundation',
                    '-framework', 'CoreGraphics', '-framework', 'ScreenCaptureKit',
                    '-framework', 'ImageIO', str(external / 'capture-test-window.m'), '-o', str(capture)], check=True)
    return libraries


def run(args, harness, helper_dir):
    readiness(harness)
    provenance = validate_build(args.binary, APP)
    output = args.output.resolve()
    if output.exists():
        raise ValueError('Use a new evidence directory')
    # The baseline must not accidentally load a third-party gameplay DLC.
    dlc = APP / 'Contents/Assets/Assets/DLC'
    allowed = {'Expansion', 'Expansion2', 'Shared', 'DLC_Deluxe', 'DLC_SP_Maps',
               'DLC_SP_Maps_2', 'DLC_SP_Maps_3'} | {'DLC_%02d' % i for i in range(1, 8)}
    if {p.name for p in dlc.iterdir() if p.is_dir()} - allowed:
        raise ValueError('Unexpected installed DLC directory; baseline test requires stock content')
    run_id = uuid.uuid4().hex
    mods = prepare_mods(args.mod_stage, DATA)
    external = Path(harness.__file__).parent
    libraries = compile_helpers(harness, helper_dir, args.host_stat_compat)
    frontend = 'Contents/Assets/Assets/UI/FrontEnd/'
    additions = {
        frontend + 'MainMenu.lua': activate_mods(startup(external / 'playtest-start.lua'), mods),
        frontend + 'LoadScreen.lua': (REPO / 'gamecore/tests/native/baseline.lua').read_text()
            .replace('__C5M_RUN__', run_id).replace('__C5M_PROBE__', args.probe_event or '').encode(),
        frontend + 'LegalScreen.lua': b'\ndo local elapsed=0; ContextPtr:SetUpdate(function(dt) if not ContextPtr:IsHidden() then elapsed=elapsed+dt; if elapsed>1 then UIManager:DequeuePopup(ContextPtr); ContextPtr:ClearUpdate() end end end) end\n',
    }
    mutations = {name: (APP / name).read_bytes() + b'\n' + code for name, code in additions.items()}
    mutations[CORE] = args.binary.read_bytes()
    # Ensure settings edits are possible before creating a journal/installing.
    config = harness.edit_ini((DATA / 'config.ini').read_text(), {
        ('CONFIG', 'QuickStart'): 0, ('CONFIG', 'SyncRandSeed'): 12345,
        ('CONFIG', 'MapRandSeed'): 67890, ('DEBUG', 'Autorun'): 0, ('DEBUG', 'LoggingEnabled'): 1})
    settings = harness.edit_ini((DATA / 'UserSettings.ini').read_text(), {('GameSettings', 'SkipIntroVideo'): 1})
    readiness(harness)
    session = Session.prepare(output, APP, DATA, mutations, dict(
        provenance, run=run_id, harness_revision=HARNESS_REVISION,
        display_before=display_state(), host_stat_compat=args.host_stat_compat,
        temporary_mods=mods, probe_event=args.probe_event,
        started_utc=datetime.now(timezone.utc).isoformat(), native_baseline='unverified'),
        data_folders=(*DATA_FOLDERS, *(mod['relative'] for mod in mods)))
    process = None
    try:
        session.install(mutations)
        install_mods(mods, DATA)
        (DATA / 'config.ini').write_text(config)
        (DATA / 'UserSettings.ini').write_text(settings)
        subprocess.run(['defaults', 'write', DOMAIN, 'DisplayFullScreen', '-bool', 'false'], check=True)
        readiness(harness)
        environment = dict(os.environ, DYLD_INSERT_LIBRARIES=':'.join(map(str, libraries)),
                           SteamAppId='8930', SteamGameId='8930')
        with (output / 'process.log').open('w') as log:
            process = subprocess.Popen([str(APP / HOST)], cwd=APP / 'Contents/MacOS',
                env=environment, stdin=subprocess.DEVNULL, stdout=log, stderr=log)
        session.report.update(status='running', pid=process.pid)
        session.save()
        print(json.dumps({'event': 'launched', 'pid': process.pid, 'evidence': str(output)}), flush=True)
        start = time.monotonic()
        passed_at = None
        while time.monotonic() - start < args.timeout:
            if process.poll() is not None:
                session.report.update(status='game-exited', exit_code=process.returncode)
                break
            lua = DATA / 'Logs/Lua.log'
            result = outcome(lua.read_text(errors='replace') if lua.exists() else '', run_id)
            if result == 'FAIL':
                session.report['status'] = 'baseline-failed'
                break
            if result == 'PASS' and passed_at is None:
                passed_at = time.monotonic()
                print(json.dumps({'event': 'baseline-checks-passed'}), flush=True)
            if passed_at is not None and time.monotonic() - passed_at >= 15:
                captured = harness.capture_game_window(process.pid, output / 'game.png')
                session.report.update(status='baseline-passed', native_baseline='passed',
                                      capture=captured, visual_review='unreviewed')
                break
            time.sleep(2)
        else:
            session.report['status'] = 'timeout'
    except (Exception, KeyboardInterrupt, SystemExit) as error:
        session.report.update(status='runner-error', error=str(error))
        raise
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=8)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=8)
        session.save()
        restore(session, harness)
        print(json.dumps({'status': session.report['status'], 'restored': session.report['restored']}), flush=True)
    return 0 if session.report['native_baseline'] == 'passed' else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--harness', type=Path, required=True)
    parser.add_argument('--binary', type=Path, default=REPO / 'build/gamecore/macos/libCvGameCoreDLL_Expansion2_DLL.dylib')
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--timeout', type=int, default=600)
    parser.add_argument('--host-stat-compat', action='store_true', help='Verified-host, process-only startup correction')
    parser.add_argument('--mod-stage', type=Path, action='append', default=[],
                        help='Temporarily activate a staged ordinary mod; existing identities are refused')
    parser.add_argument('--probe-event', help='C5M Lua event that receives the run ID and must emit the final PASS/FAIL')
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--check', action='store_true', help='Read-only readiness/binary check')
    action.add_argument('--run', action='store_true', help='Explicit temporary activation and bounded game launch')
    action.add_argument('--restore', action='store_true', help='Recover an interrupted session; does not launch')
    args = parser.parse_args()
    if not 60 <= args.timeout <= 1200:
        parser.error('Timeout must be between 60 and 1200 seconds')
    if args.probe_event and (not args.mod_stage or not re.fullmatch(r'C5M_[A-Za-z0-9_]+', args.probe_event)):
        parser.error('Probe events must start with C5M_ and require a staged mod')
    harness = load_harness(args.harness.resolve())
    if args.check:
        readiness(harness)
        prepare_mods(args.mod_stage, DATA)
        print(json.dumps(validate_build(args.binary, APP)['validation'], indent=2))
        return 0
    previous = json.loads(LOCK_PATH.read_text()).get('evidence') if LOCK_PATH.exists() else None
    if previous and not args.restore:
        prior_recovery(Path(previous) / 'session.json')
    with native_test_lock('C5M baseline acceptance', args.output):
        if args.restore:
            restore(Session.load(args.output), harness)
            print('Restoration verified')
            return 0
        if previous:
            prior_recovery(Path(previous) / 'session.json')
        # Recover old GameCore tests even if another runner has since held the lease.
        for journal in args.output.resolve().parent.glob('*/session.json'):
            prior_recovery(journal)
        signal.signal(signal.SIGTERM, lambda *_: (_ for _ in ()).throw(InterruptedError('SIGTERM')))
        with tempfile.TemporaryDirectory(prefix='c5m-native-') as directory:
            return run(args, harness, Path(directory))


if __name__ == '__main__':
    try:
        sys.exit(main())
    except (ValueError, RuntimeError, OSError, subprocess.CalledProcessError) as error:
        sys.exit(str(error))
