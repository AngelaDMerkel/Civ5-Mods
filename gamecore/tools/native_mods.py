"""Temporary ordinary-mod stages for the guarded native acceptance runner."""
import hashlib
from pathlib import Path
import re
import xml.etree.ElementTree as ET

from native_session import digest, plain_path


def payload(root):
    files = {}
    for path in sorted(root.rglob('*')):
        relative = path.relative_to(root).as_posix()
        plain_path(root, relative)
        if path.is_file():
            files[relative] = digest(path)
        elif not path.is_dir():
            raise ValueError('Unsupported mod entry: ' + str(path))
    return files


def prepare_mods(stages, data):
    existing = {}
    mods = plain_path(data, 'MODS')
    for manifest in mods.rglob('*.modinfo'):
        plain_path(data, manifest.relative_to(data))
        root = ET.parse(manifest).getroot()
        existing[root.get('id', '').lower()] = str(manifest)
    result = []
    for stage in stages:
        if stage.is_symlink():
            raise ValueError('Mod stage must not be a symlink')
        source = stage.resolve()
        manifests = list(source.glob('*.modinfo'))
        if len(manifests) != 1:
            raise ValueError('Mod stage needs exactly one manifest')
        files = payload(source)
        root = ET.parse(manifests[0]).getroot()
        identity, version = root.get('id', '').lower(), root.get('version', '')
        if not re.fullmatch(r'[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}', identity) or not version.isdigit():
            raise ValueError('Invalid mod identity')
        relative = 'MODS/C5M_Native_' + identity
        target = plain_path(data, relative)
        if identity in existing or target.exists():
            raise ValueError('Refusing existing mod identity or test folder: ' + identity)
        existing[identity] = str(source)
        result.append(dict(id=identity, version=int(version), source=str(source),
                           relative=relative, payload=files))
    return result


def install_mods(mods, data):
    # The session must already have journaled these absent data directories.
    for mod in mods:
        if payload(Path(mod['source'])) != mod['payload']:
            raise RuntimeError('Mod stage changed since preparation')
        if plain_path(data, mod['relative']).exists():
            raise RuntimeError('Temporary mod appeared since preparation')
    for mod in mods:
        target = plain_path(data, mod['relative'])
        for relative, sha in mod['payload'].items():
            source = plain_path(Path(mod['source']), relative)
            contents = source.read_bytes()
            if hashlib.sha256(contents).hexdigest() != sha:
                raise RuntimeError('Mod stage changed while copying')
            destination = plain_path(target, relative)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(contents)


def verify_mods(mods, data):
    # A partially installed stage can be recovered, but independent edits cannot.
    for mod in mods:
        target = plain_path(data, mod['relative'])
        if target.exists():
            for relative, sha in payload(target).items():
                if mod['payload'].get(relative) != sha:
                    raise RuntimeError('Temporary mod changed independently: ' + relative)


def activate_mods(code, mods, loading=False):
    if not mods:
        return code
    marker = b'local function startMatch()' if loading else b'print("[LEKMOD_TEST] starting unattended match")'
    if code.count(marker) != 1:
        raise ValueError('External startup activation hook changed')
    lines = ['for _,m in pairs(Modding.GetModBrowserInstalledListings()) do',
             '  Modding.DisableMod(m.ModId, m.Version)', 'end']
    for mod in mods:
        lines.append('Modding.EnableMod("%s", %d)' % (mod['id'], mod['version']))
    lines.extend(['Modding.ActivateEnabledMods()', 'local active={}',
                  'for _,m in pairs(Modding.GetActivatedMods()) do active[string.lower(m.ID)]=true end'])
    for mod in mods:
        lines.append('assert(active["%s"], "C5M ordinary mod activation failed")' % mod['id'])
    return code.replace(marker, marker + b'\n' + '\n'.join(lines).encode())


def validate_load(code):
    """Perform the same header/compatibility preflight as the stock Load menu."""
    marker = b'if loadPath then'
    if code.count(marker) != 1:
        raise ValueError('External saved-game hook changed')
    checks = b'''
            local header = PreGame.GetFileHeader(loadPath)
            assert(header, "C5M saved-game header is unreadable")
            local compatible = Modding.CanLoadSavedGame(loadPath)
            print("[C5M_LOAD] world=" .. tostring(header.WorldSize) ..
                  " civilization=" .. tostring(header.PlayerCivilization) ..
                  " turn=" .. tostring(header.TurnNumber) ..
                  " compatible=" .. tostring(compatible))
            assert(compatible == 0, "C5M saved-game compatibility check failed: " .. tostring(compatible))
'''
    return code.replace(marker, marker + checks)
