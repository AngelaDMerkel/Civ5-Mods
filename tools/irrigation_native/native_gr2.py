"""Read Civ V's little-endian, 32-bit Granny 7 meshes without the Granny SDK.

Reflection retains every vertex component and the model/material graph. Native
textures and meshes must stay in ignored local caches. Oodle1 is a vendored MPL
codec; use this reader only with trusted files from a local game installation.
"""
from pathlib import Path
import ctypes
import hashlib
import struct
import subprocess
import sys
import zlib

MAGIC = bytes.fromhex('29de6cc0baa4532b25f5b7a5f666e2ee')
SCALAR = {10: 'f', 11: 'b', 12: 'B', 13: 'b', 14: 'B', 15: 'h', 16: 'H',
          17: 'h', 18: 'H', 19: 'i', 20: 'I', 21: 'e'}
SIZES = {2: 4, 3: 8, 4: 8, 5: 8, 7: 12, 8: 4, 9: 68, 22: 4,
         **{k: struct.calcsize('<'+v) for k, v in SCALAR.items()}}


def build_decoder(cache):
    source = Path(__file__).parent / 'vendor/opengr2'
    inputs = sorted(p for p in source.iterdir() if p.suffix in ('.c', '.h'))
    digest = hashlib.sha256(b''.join(p.read_bytes() for p in inputs)).hexdigest()[:16]
    cache = Path(cache); cache.mkdir(parents=True, exist_ok=True)
    target = cache / ('oodle1-' + digest + ('.dylib' if sys.platform == 'darwin' else '.so'))
    if not target.exists():
        result = subprocess.run(['cc', '-dynamiclib' if sys.platform == 'darwin' else '-shared',
                        '-fPIC', '-O2', '-I'+str(source),
                        *[str(source / f) for f in ('compression.c', 'oodle1.c', 'platform.c')],
                        '-o', str(target)], capture_output=True, text=True)
        if result.returncode:
            raise RuntimeError('Cannot build Oodle1 decoder: '+result.stderr)
    return target


class Reader:
    def __init__(self, path, gsd=None, decoder=None):
        self.path = Path(path)
        self.raw = self.path.read_bytes()
        if len(self.raw) < 104 or self.raw[:16] != MAGIC:
            raise ValueError('Expected a little-endian 32-bit Granny 7 file')
        self.header = struct.unpack_from('<18I', self.raw, 32)
        h = self.header
        if h[0] != 7 or h[1] != len(self.raw) or h[3] != 72 or not 1 <= h[4] <= 64:
            raise ValueError('Unsupported or truncated Granny header')
        if zlib.crc32(self.raw[104:]) != h[2]:
            raise ValueError('Granny checksum mismatch')
        self.sections = [struct.unpack('<11I', self.raw_slice(104+44*i, 44)) for i in range(h[4])]
        self.data, self.fix, self.strings, self.types, self.cache = [], {}, {}, {}, {}
        decode = None
        if any(s[0] == 2 and s[3] for s in self.sections):
            if decoder is None:
                raise ValueError('Oodle1 decoder required for compressed native files')
            self.library = ctypes.CDLL(str(decoder))
            decode = self.library.Compression_UnOodle1
            decode.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p,
                               ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_bool]
            decode.restype = ctypes.c_bool
        for i, section in enumerate(self.sections):
            comp, off, count, size, _, stop16, stop8, fixoff, nfix, _, nmixed = section
            if size > 256*1024*1024 or not 0 <= stop16 <= stop8 <= size:
                raise ValueError('Invalid or excessively large Granny section')
            data = self.raw_slice(off, count)
            if comp == 2 and size:
                if len(data) < 36:
                    raise ValueError('Truncated Oodle1 payload')
                src = ctypes.create_string_buffer(data+b'\0'*16)
                dst = ctypes.create_string_buffer(size+16)
                if not decode(src, count, dst, size, stop16, stop8, False):
                    raise ValueError('Oodle1 decompression failed')
                data = dst.raw[:size]
            elif comp not in (0, 2):
                raise ValueError(f'Unsupported Granny compression {comp}')
            if len(data) != size:
                raise ValueError('Section size mismatch')
            self.data.append(data)
            for j in range(nfix):
                source, target, offset = struct.unpack('<III', self.raw_slice(fixoff+12*j, 12))
                if source+4 > size or target >= h[4] or offset >= self.sections[target][3]:
                    raise ValueError('Granny relocation out of bounds')
                if (i, source) in self.fix:
                    raise ValueError('Duplicate Granny relocation')
                self.fix[i, source] = (target, offset)
        if gsd:
            database = Reader(gsd, decoder=decoder)
            ptr = database.ptr(0, 4)
            for i in range(database.u(0, 0)):
                value = database.string(database.ptr(ptr[0], ptr[1]+4*i))
                self.strings[(~zlib.crc32(value.encode())) & 0xffffffff] = value

    def raw_slice(self, offset, size):
        if offset < 0 or offset+size > len(self.raw):
            raise ValueError('Read outside Granny file')
        return self.raw[offset:offset+size]

    def u(self, section, offset):
        return struct.unpack_from('<I', self.data[section], offset)[0]

    def ptr(self, section, offset):
        return self.fix.get((section, offset))

    def string(self, pointer):
        if pointer is None:
            return None
        section, offset = pointer
        data = self.data[section]
        return data[offset:data.index(b'\0', offset)].decode('utf8')

    def strfield(self, section, offset):
        pointer = self.ptr(section, offset)
        if pointer:
            return self.string(pointer)
        value = self.u(section, offset)
        if not value:
            return None
        if value not in self.strings:
            raise ValueError(f'Missing string database entry {value:08x}')
        return self.strings[value]

    def schema(self, pointer):
        if pointer in self.types:
            return self.types[pointer]
        out = []
        self.types[pointer] = out
        section, offset = pointer
        for i in range(1024):
            q = offset+32*i
            kind = self.u(section, q)
            if not kind:
                return out
            if kind not in SIZES and kind != 1:
                raise ValueError(f'Unsupported Granny member type {kind}')
            out.append({'type': kind, 'name': self.strfield(section, q+4),
                        'nested': self.ptr(section, q+8), 'count': max(1, self.u(section, q+12)),
                        'defptr': (section, q)})
        raise ValueError('Unterminated Granny type')

    def size(self, pointer):
        return sum(self.member_size(m)*m['count'] for m in self.schema(pointer))

    def member_size(self, member):
        return self.size(member['nested']) if member['type'] == 1 else SIZES[member['type']]

    def obj(self, pointer, kind):
        if pointer is None:
            return None
        key = (pointer, kind)
        if key in self.cache:
            return self.cache[key]
        section, offset = pointer
        if offset+self.size(kind) > len(self.data[section]):
            raise ValueError('Object outside Granny section')
        result = {'_ptr': pointer, '_type': kind, '_fields': {}}
        self.cache[key] = result
        for member in self.schema(kind):
            result['_fields'][member['name']] = (section, offset)
            values = []
            for _ in range(member['count']):
                values.append(self.value(section, offset, member))
                offset += self.member_size(member)
            result[member['name']] = values[0] if member['count'] == 1 else values
        return result

    def value(self, section, offset, member):
        kind, nested = member['type'], member['nested']
        if kind == 1:
            return self.obj((section, offset), nested)
        if kind == 2:
            return self.obj(self.ptr(section, offset), nested)
        if kind in (3, 4, 7):
            if kind == 7:
                nested = self.ptr(section, offset); offset += 4
            count, pointer = self.u(section, offset), self.ptr(section, offset+4)
            if not count:
                return []
            if pointer is None or nested is None or count > 10_000_000:
                raise ValueError('Invalid Granny array')
            stride = 4 if kind == 4 else self.size(nested)
            if pointer[1]+stride*count > len(self.data[pointer[0]]):
                raise ValueError('Array outside Granny section')
            return [self.obj(self.ptr(pointer[0], pointer[1]+i*stride) if kind == 4
                             else (pointer[0], pointer[1]+i*stride), nested) for i in range(count)]
        if kind == 5:
            nested, pointer = self.ptr(section, offset), self.ptr(section, offset+4)
            return self.obj(pointer, nested) if pointer and nested else None
        if kind == 8:
            return self.strfield(section, offset)
        if kind == 9:
            return list(struct.unpack_from('<I16f', self.data[section], offset))
        if kind == 22:
            return self.ptr(section, offset)
        return struct.unpack_from('<'+SCALAR[kind], self.data[section], offset)[0]

    def root(self):
        h = self.header
        return self.obj((h[7], h[8]), (h[5], h[6]))
