"""Selective, bounded reads from the installed Civ V FPK v6 archives."""
from pathlib import Path, PurePosixPath
import struct


class Archive:
    def __init__(self, path):
        self.path = Path(path)
        self.entries = {}
        length = self.path.stat().st_size
        with self.path.open('rb') as stream:
            def u32():
                return struct.unpack('<I', stream.read(4))[0]
            if stream.read(10) != b'\x06\0\0\0FPK_\0\0':
                raise ValueError('Unsupported FPK archive')
            count = u32()
            if count > 100_000:
                raise ValueError('Invalid FPK index')
            for _ in range(count):
                size = u32()
                if not 1 <= size <= 1024:
                    raise ValueError('Invalid FPK entry name length')
                name = stream.read(size).decode('utf8').replace('\\', '/')
                padding = u32()
                if padding > 3:
                    raise ValueError('Invalid FPK index padding')
                stream.read(padding)
                _, size, offset = u32(), u32(), u32()
                if offset+size > length or '..' in PurePosixPath(name).parts or name.startswith('/'):
                    raise ValueError('Invalid FPK entry')
                key = name.lower()
                if key in self.entries:
                    raise ValueError('Duplicate FPK entry')
                self.entries[key] = (offset, size)
            index_end = stream.tell()
            if any(offset < index_end for offset, _ in self.entries.values()):
                raise ValueError('FPK payload overlaps its index')

    def read(self, name):
        offset, size = self.entries[name.lower()]
        with self.path.open('rb') as stream:
            stream.seek(offset)
            result = stream.read(size)
        if len(result) != size:
            raise ValueError('Truncated FPK payload')
        return result

    def extract(self, name, directory):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / PurePosixPath(name).name.lower()
        target.write_bytes(self.read(name))
        return target
