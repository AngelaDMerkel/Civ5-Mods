"""Journaled, temporary file changes for a developer GameCore test.

Callers must hold the repository's native test lease and refuse running games.
This layer does not launch a game or implement a permanent player installer.
"""
import hashlib
import json
import os
from pathlib import Path
import shutil

LEGACY_DATA_FOLDERS = ('Saves', 'ModdedSaves', 'cache', 'Logs')
DATA_FOLDERS = (*LEGACY_DATA_FOLDERS, 'ModUserData')
SETTINGS = ('config.ini', 'UserSettings.ini', 'GraphicsSettingsDX9.ini')


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    temporary = path.with_suffix('.pending')
    with temporary.open('w') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
    temporary.replace(path)


def plain_path(root, relative):
    relative = Path(relative)
    if relative.is_absolute() or '..' in relative.parts or not relative.parts:
        raise ValueError('Invalid session-relative path')
    path = root
    for part in relative.parts:
        path = path / part
        if path.is_symlink():
            raise ValueError('Session paths must not contain symlinks: ' + str(path))
    return path


def replace_file(path, contents, metadata=None):
    temporary = path.with_name(path.name + '.c5m-pending')
    if temporary.exists() or temporary.is_symlink():
        # A kill between write and rename leaves only a temporary copy. Never
        # delete an unrelated file to recover it.
        if temporary.is_symlink() or temporary.read_bytes() != contents:
            raise RuntimeError('Unrecognized interrupted replacement: ' + str(temporary))
        temporary.unlink()
    try:
        with temporary.open('xb') as stream:
            stream.write(contents)
            stream.flush()
            os.fsync(stream.fileno())
        if metadata is not None:
            shutil.copystat(metadata, temporary)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def data_inventory(data, folders=DATA_FOLDERS):
    result = {}
    directories = []
    for folder in folders:
        root = plain_path(data, folder)
        if root.exists():
            if not root.is_dir():
                raise ValueError('Expected data directory: ' + str(root))
            directories.append(folder)
            for path in sorted(root.rglob('*')):
                relative = path.relative_to(data).as_posix()
                plain_path(data, relative)
                if path.is_dir():
                    directories.append(relative)
                elif path.is_file():
                    result[relative] = digest(path)
                else:
                    raise ValueError('Unsupported data entry: ' + str(path))
    for name in SETTINGS:
        path = plain_path(data, name)
        result[name] = digest(path) if path.exists() else None
    return result, sorted(directories)


class Session:
    def __init__(self, output, report):
        self.output = Path(output)
        self.report = report

    def save(self):
        write_json(self.output / 'session.json', self.report)

    @classmethod
    def prepare(cls, output, app, data, mutations, metadata, data_folders=DATA_FOLDERS):
        output, app, data = map(lambda p: Path(p).resolve(), (output, app, data))
        output.mkdir(parents=True, exist_ok=False)
        original, directories = data_inventory(data, data_folders)
        report = dict(metadata, format=1, app=str(app), data=str(data),
                      status='preparing', restored=False, data_originals=original,
                      data_directories=directories, data_folders=list(data_folders),
                      app_originals={}, installed={})
        session = cls(output, report)
        # No game files are changed until all backups and the journal exist.
        for relative, sha in original.items():
            if sha is not None:
                session.backup(data, relative, 'data-backup', sha)
        for relative, contents in mutations.items():
            path = plain_path(app, relative)
            sha = digest(path) if path.exists() else None
            report['app_originals'][relative] = sha
            report['installed'][relative] = hashlib.sha256(contents).hexdigest()
            if sha is not None:
                session.backup(app, relative, 'app-backup', sha)
        report['status'] = 'prepared'
        session.save()
        return session

    def backup(self, root, relative, directory, expected):
        destination = plain_path(self.output / directory, relative)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(root / relative, destination)
        if digest(destination) != expected:
            raise RuntimeError('Backup did not match source: ' + relative)

    @classmethod
    def load(cls, output):
        output = Path(output).resolve()
        report = json.loads((output / 'session.json').read_text())
        if report.get('format') != 1:
            raise ValueError('Unsupported session journal')
        return cls(output, report)

    def install(self, mutations):
        app = Path(self.report['app'])
        if set(mutations) != set(self.report['installed']):
            raise ValueError('Mutation set does not match journal')
        # Validate all inputs before writing any of them.
        for relative, contents in mutations.items():
            path = plain_path(app, relative)
            actual = digest(path) if path.exists() else None
            if actual != self.report['app_originals'][relative]:
                raise RuntimeError('Game file changed since backup: ' + relative)
            if hashlib.sha256(contents).hexdigest() != self.report['installed'][relative]:
                raise ValueError('Mutation bytes do not match journal')
        for relative, contents in mutations.items():
            path = app / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            # Atomic rename avoids a half-written native library after interruption.
            replace_file(path, contents, path if path.exists() else None)
        self.report['status'] = 'installed'
        self.save()

    def restore_files(self):
        report = self.report
        app, data = Path(report['app']), Path(report['data'])
        # Refuse to overwrite independently changed app files or corrupted backups.
        # A partially installed/restored transaction is safe to resume.
        for relative, sha in report['app_originals'].items():
            path = plain_path(app, relative)
            actual = digest(path) if path.exists() else None
            if actual not in (sha, report['installed'][relative]):
                raise RuntimeError('App file changed independently: ' + relative)
            pending = path.with_name(path.name + '.c5m-pending')
            if pending.exists() or pending.is_symlink():
                if pending.is_symlink() or digest(pending) not in (sha, report['installed'][relative]):
                    raise RuntimeError('Unrecognized interrupted replacement: ' + relative)
        for directory, originals in (('app-backup', report['app_originals']),
                                     ('data-backup', report['data_originals'])):
            for relative, sha in originals.items():
                if sha is not None and digest(plain_path(self.output / directory, relative)) != sha:
                    raise RuntimeError('Recovery backup changed: ' + relative)
        folders = report.get('data_folders', LEGACY_DATA_FOLDERS)
        current, directories = data_inventory(data, folders)
        for relative, sha in current.items():
            if sha is None:
                continue
            path = data / relative
            if sha != report['data_originals'].get(relative) or relative.startswith('Logs/'):
                # Do not replace first-run evidence when restoration is retried.
                dest = plain_path(self.output / 'after', relative)
                if not dest.exists():
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(path, dest)
            if report['data_originals'].get(relative) is None:
                path.unlink()
        for directory, root, originals in (
                ('data-backup', data, report['data_originals']),
                ('app-backup', app, report['app_originals'])):
            for relative, sha in originals.items():
                path = plain_path(root, relative)
                if sha is None:
                    path.unlink(missing_ok=True)
                else:
                    path.parent.mkdir(parents=True, exist_ok=True)
                    backup = self.output / directory / relative
                    pending = path.with_name(path.name + '.c5m-pending')
                    if directory == 'app-backup' and pending.exists():
                        pending.unlink()  # Hash checked above before restoring anything.
                    replace_file(path, backup.read_bytes(), backup)
        for relative in sorted(set(directories) - set(report['data_directories']),
                               key=lambda p: len(Path(p).parts), reverse=True):
            (data / relative).rmdir()
        for relative in report['data_directories']:
            (data / relative).mkdir(parents=True, exist_ok=True)
        restored, directories = data_inventory(data, folders)
        if restored != report['data_originals'] or directories != report['data_directories']:
            raise RuntimeError('Data restoration verification failed')
        for relative, expected in report['app_originals'].items():
            path = app / relative
            if (digest(path) if path.exists() else None) != expected:
                raise RuntimeError('App restoration verification failed: ' + relative)
        report['files_restored'] = True
        self.save()
