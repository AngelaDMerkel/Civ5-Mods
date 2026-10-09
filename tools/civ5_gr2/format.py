"""GR2 v7 little-endian/32-bit containers and dynamic record graphs.

Format research: LSLib GR2/{Format,Reader,Writer}.cs (MIT; see NOTICE).
Only uncompressed output is written. No proprietary code or template is used.
"""
from __future__ import annotations

import ctypes
import struct
import zlib
from dataclasses import dataclass, field
from pathlib import Path

MAGIC = bytes.fromhex('29de6cc0baa4532b25f5b7a5f666e2ee')
SCALARS = {10: 'f', 11: 'b', 12: 'B', 13: 'b', 14: 'B', 15: 'h',
           16: 'H', 17: 'h', 18: 'H', 19: 'i', 20: 'I', 21: 'e'}
SIZES = {2: 4, 3: 8, 4: 8, 5: 8, 7: 12, 8: 4, 9: 68, 22: 4,
         **{k: struct.calcsize('<' + v) for k, v in SCALARS.items()}}
MAX_BYTES = 256 * 1024 * 1024
MAX_ITEMS = 2_000_000


class FormatError(ValueError):
    """Unsupported or invalid data, reported without a CLI traceback."""


def require(condition, message):
    if not condition:
        raise FormatError(message)


def plus(address, offset):
    require(address is not None, 'null data pointer')
    return address[0], address[1] + offset


@dataclass(eq=False)
class Member:
    name: str
    kind: int
    definition: Definition | None = None
    width: int = 0
    extra: tuple = (0, 0, 0)

    def size(self):
        return (self.definition.size() if self.kind == 1 else SIZES[self.kind]) * max(1, self.width)


@dataclass(eq=False)
class Definition:
    members: list[Member] = field(default_factory=list)

    def size(self, ancestors=()):
        require(self not in ancestors and len(ancestors) < 64, 'recursive or excessively nested inline type')
        return sum((m.definition.size(ancestors + (self,)) if m.kind == 1 else SIZES[m.kind])
                   * max(1, m.width) for m in self.members)


@dataclass(eq=False)
class Node:
    definition: Definition
    values: dict = field(default_factory=dict)

    def __getitem__(self, key):
        return self.values[key]


@dataclass
class VariantArray:
    definition: Definition | None
    items: list[Node]


class Reader:
    """Bounds-checked parser. Optional OpenGR2 codec is for trusted local files only.

    The upstream C decompressor is not hardened for hostile compressed input.
    It is never needed for conversion or validation of this tool's output.
    """
    def __init__(self, data: bytes, *, strings=None, codec=None):
        require(104 <= len(data) <= MAX_BYTES, 'invalid GR2 file size')
        require(data[:16] == MAGIC, 'only GR2 v7 little-endian 32-bit signature is supported')
        self.data = data
        headers_size, header_format, r1, r2 = self.unpack_file(16, '4I')
        require(header_format == 0 and r1 == r2 == 0, 'unsupported compressed/reserved header')
        self.header = self.unpack_file(32, '18I')
        h = self.header
        require(h[0] == 7 and h[3] == 72, 'only version 7 headers are supported')
        require(h[1] == len(data), 'header file size mismatch')
        require(zlib.crc32(data[104:]) == h[2], 'CRC32 mismatch')
        require(0 < h[4] <= 64 and headers_size == 104 + h[4] * 44, 'invalid section table')
        self.sections = [self.unpack_file(104 + i * 44, '11I') for i in range(h[4])]
        require(sum(s[3] for s in self.sections) <= MAX_BYTES, 'expanded sections exceed size limit')
        self.buffers = []
        for compression, offset, length, size, align, stop0, stop1, *_ in self.sections:
            require(align in (1, 2, 4, 8, 16, 32), 'unsupported section alignment')
            require(0 <= stop0 <= stop1 <= size, 'invalid compression stops')
            content = self.slice_file(offset, length)
            if not size:
                require(length == 0, 'nonempty encoding of empty section')
                self.buffers.append(b'')
            elif compression == 0:
                require(length == size, 'uncompressed section size mismatch')
                self.buffers.append(content)
            elif compression == 2 and codec:
                require(length >= 36, 'truncated Oodle1 header')
                lib = ctypes.CDLL(str(Path(codec).resolve()))
                fn = lib.Compression_UnOodle1
                fn.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_void_p,
                               ctypes.c_uint32, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_bool]
                fn.restype = ctypes.c_bool
                src = ctypes.create_string_buffer(content + b'\0' * 4)
                dst = ctypes.create_string_buffer(size)
                require(fn(src, length, dst, size, stop0, stop1, False), 'Oodle1 decode failed')
                self.buffers.append(dst.raw)
            else:
                raise FormatError(f'compression {compression} unsupported; trusted Oodle1 references need --codec')
        self.relocations = {}
        for section, s in enumerate(self.sections):
            self.slice_file(s[7], s[8] * 12)
            self.slice_file(s[9], s[10] * 16)
            for i in range(s[8]):
                src, target_section, target_offset = self.unpack_file(s[7] + i * 12, '3I')
                self.slice((section, src), 4)
                self.slice((target_section, target_offset), 1)
                require((section, src) not in self.relocations, 'duplicate relocation')
                self.relocations[section, src] = target_section, target_offset
            for i in range(s[10]):
                count, src, ts, to = self.unpack_file(s[9] + i * 16, '4I')
                require(count <= MAX_ITEMS, 'marshalling count exceeds limit')
                self.slice((section, src), 1)
                self.slice((ts, to), 32)
        self.strings = strings or {}
        self.definitions = {}
        self.nodes = {}
        self.string_slots = set()
        self.budget = MAX_ITEMS
        self.root_type = h[5], h[6]
        self.root_address = h[7], h[8]

    def slice_file(self, offset, size):
        require(0 <= offset <= len(self.data) and 0 <= size <= len(self.data) - offset, 'file range out of bounds')
        return self.data[offset:offset + size]

    def unpack_file(self, offset, fmt):
        return struct.unpack('<' + fmt, self.slice_file(offset, struct.calcsize('<' + fmt)))

    def slice(self, address, size):
        require(address is not None, 'missing required reference')
        section, offset = address
        require(0 <= section < len(self.buffers), 'section reference out of bounds')
        b = self.buffers[section]
        require(0 <= offset <= len(b) and 0 <= size <= len(b) - offset, 'section range out of bounds')
        return b[offset:offset + size]

    def read(self, address, fmt):
        return struct.unpack('<' + fmt, self.slice(address, struct.calcsize('<' + fmt)))

    def pointer(self, address):
        self.slice(address, 4)
        ref = self.relocations.get(address)
        require(ref is not None or self.read(address, 'I')[0] == 0, 'non-null pointer missing relocation')
        return ref

    def string(self, address):
        self.string_slots.add(address)
        ref = self.relocations.get(address)
        if ref is not None:
            section, offset = ref
            b = self.buffers[section]
            end = b.find(b'\0', offset, offset + 65536)
            require(end != -1, 'unterminated string')
            try:
                return b[offset:end].decode('utf-8')
            except UnicodeDecodeError as e:
                raise FormatError('invalid UTF-8 string') from e
        value = self.read(address, 'I')[0]
        if self.header[14]:
            require(value in self.strings, f'unresolved string hash 0x{value:08x}; supply matching --strings GSD')
            return self.strings[value]
        require(value == 0, 'string pointer missing relocation')
        return None

    def definition(self, address, depth=0):
        require(address is not None and depth < 64, 'missing or excessively nested type')
        if address in self.definitions:
            return self.definitions[address]
        result = Definition()
        self.definitions[address] = result
        for i in range(1024):
            slot = plus(address, i * 32)
            kind, _, _, width, a, b, c, reserved = self.read(slot, '8I')
            if kind == 0:
                return result
            require(kind == 1 or kind in SIZES, f'unknown member kind {kind}')
            require(width <= 65536 and reserved == 0, 'invalid member descriptor')
            name = self.string(plus(slot, 4))
            require(name and all(m.name != name for m in result.members), 'empty or duplicate field name')
            ref = self.pointer(plus(slot, 8))
            sub = self.definition(ref, depth + 1) if ref is not None else None
            require(kind not in (1, 2, 3, 4) or sub is not None, 'typed member has no definition')
            require(kind != 1 or sub.members, 'recursive inline type is unsupported')
            result.members.append(Member(name, kind, sub, width, (a, b, c)))
        raise FormatError('unterminated type definition')

    def node(self, definition, address, depth=0):
        if address is None:
            return None
        require(definition is not None and depth < 100, 'missing type or excessively nested graph')
        key = definition, address
        if key in self.nodes:
            return self.nodes[key]
        self.budget -= 1
        require(self.budget >= 0, 'record budget exhausted')
        self.slice(address, definition.size())
        result = Node(definition)
        self.nodes[key] = result
        for member in definition.members:
            step = member.size() // max(1, member.width)
            values = [self.value(member, plus(address, i * step), depth + 1)
                      for i in range(max(1, member.width))]
            result.values[member.name] = values if member.width else values[0]
            address = plus(address, member.size())
        return result

    def value(self, m, p, depth):
        k = m.kind
        if k in SCALARS:
            return self.read(p, SCALARS[k])[0]
        if k == 9:
            return list(self.read(p, 'I16f'))
        if k == 8:
            return self.string(p)
        if k == 1:
            return self.node(m.definition, p, depth)
        if k == 2:
            return self.node(m.definition, self.pointer(p), depth)
        if k == 22:
            require(self.read(p, 'I')[0] == 0, 'nonempty empty-reference field')
            return None
        if k == 5:
            tp, dp = self.pointer(p), self.pointer(plus(p, 4))
            require((tp is None) == (dp is None), 'incomplete variant reference')
            return self.node(self.definition(tp), dp, depth) if tp else None
        if k == 7:
            tp = self.pointer(p)
            definition = self.definition(tp) if tp else None
            count = self.read(plus(p, 4), 'I')[0]
            target = self.pointer(plus(p, 8))
        else:
            definition = m.definition
            count = self.read(p, 'I')[0]
            target = self.pointer(plus(p, 4))
        require(count <= self.budget and (count == 0 or (target is not None and definition)), 'invalid array count/reference')
        items = []
        if count:
            step = 4 if k == 4 else definition.size()
            require(step > 0, 'array of empty records')
            self.slice(target, step * count)
            for i in range(count):
                q = plus(target, i * step)
                items.append(self.node(definition, self.pointer(q) if k == 4 else q, depth))
        return VariantArray(definition, items) if k == 7 else items

    def root(self):
        return self.node(self.definition(self.root_type), self.root_address)


def load_strings(path):
    reader = Reader(Path(path).read_bytes())
    root = reader.root()
    require('Strings' in root.values and 'DatabaseCRC' in root.values, 'not a string database')
    result = {}
    for item in root['Strings']:
        value = item['String']
        key = ~zlib.crc32(value.encode('utf-8')) & 0xffffffff
        require(key not in result or result[key] == value, 'string hash collision')
        result[key] = value
    return root['DatabaseCRC'], result


class Writer:
    """Deterministic uncompressed writer; stores real strings, never GSD hashes."""
    def __init__(self, tag=0x80000031):
        self.tag = tag
        self.buffers = [bytearray() for _ in range(8)]
        self.relocations = [[] for _ in range(8)]
        self.types = {}
        self.objects = {}
        self.strings = {}

    def allocate(self, section, size, alignment=4):
        b = self.buffers[section]
        b.extend(b'\0' * (-len(b) % alignment))
        p = section, len(b)
        b.extend(b'\0' * size)
        return p

    def put(self, p, fmt, *values):
        struct.pack_into('<' + fmt, self.buffers[p[0]], p[1], *values)

    def reference(self, p, target):
        if target is not None:
            self.relocations[p[0]].append((p[1], *target))

    def string(self, value):
        if value is None:
            return None
        require('\0' not in value, 'embedded null in string')
        if value not in self.strings:
            encoded = value.encode('utf-8') + b'\0'
            p = self.allocate(0, len(encoded))
            self.buffers[0][p[1]:p[1] + len(encoded)] = encoded
            self.strings[value] = p
        return self.strings[value]

    def definition(self, definition):
        if definition is None:
            return None
        if definition in self.types:
            return self.types[definition]
        p = self.allocate(6, 32 * (len(definition.members) + 1))
        self.types[definition] = p
        for i, m in enumerate(definition.members):
            q = plus(p, i * 32)
            self.put(q, '8I', m.kind, 0, 0, m.width, *m.extra, 0)
            self.reference(plus(q, 4), self.string(m.name))
            self.reference(plus(q, 8), self.definition(m.definition))
        return p

    def node(self, node, address=None):
        if node is None:
            return None
        if address is None and node in self.objects:
            return self.objects[node]
        p = address if address is not None else self.allocate(0, node.definition.size())
        self.objects[node] = p
        q = p
        for m in node.definition.members:
            value = node.values.get(m.name)
            if m.width:
                require(value is not None and len(value) == m.width, f'bad width for {m.name}')
                step = m.size() // m.width
                for i, v in enumerate(value):
                    self.value(m, plus(q, i * step), v)
            else:
                self.value(m, q, value)
            q = plus(q, m.size())
        return p

    def value(self, m, p, value):
        k = m.kind
        if k in SCALARS:
            self.put(p, SCALARS[k], value if value is not None else 0)
        elif k == 9:
            require(value is not None and len(value) == 17, 'transform must have flags and 16 floats')
            self.put(p, 'I16f', *value)
        elif k == 8:
            self.reference(p, self.string(value))
        elif k == 1:
            require(value is not None and value.definition is m.definition, 'invalid inline record')
            self.node(value, p)
        elif k == 2:
            require(value is None or value.definition is m.definition, f'wrong reference type: {m.name}')
            self.reference(p, self.node(value))
        elif k == 5:
            if value is not None:
                self.reference(p, self.definition(value.definition))
                self.reference(plus(p, 4), self.node(value))
        elif k in (3, 4, 7):
            definition = value.definition if k == 7 else m.definition
            items = value.items if k == 7 else (value or [])
            if k == 7:
                self.reference(p, self.definition(definition))
                p = plus(p, 4)
            self.put(p, 'I', len(items))
            if items:
                require(all(n is not None and n.definition is definition for n in items), f'wrong array type: {m.name}')
                step = 4 if k == 4 else definition.size()
                section = 1 if m.name == 'Vertices' else 2 if m.name in ('Indices', 'Indices16') else 0
                q = self.allocate(section, step * len(items))
                self.reference(plus(p, 4), q)
                for i, n in enumerate(items):
                    slot = plus(q, i * step)
                    if k == 4:
                        self.reference(slot, self.node(n))
                    else:
                        self.node(n, slot)
        elif k != 22:
            raise FormatError(f'unsupported writer member {k}')

    def encode(self, root):
        require(not self.objects, 'writer instances are single-use')
        root_address = self.node(root)
        root_type = self.definition(root.definition)
        result = bytearray(456)
        sections = []
        for b in self.buffers:
            result.extend(b'\0' * (-len(result) % 4))
            offset = len(result)
            result.extend(b)
            sections.append([0, offset, len(b), len(b), 4, len(b), len(b), 0, 0, 0, 0])
        for i, entries in enumerate(self.relocations):
            result.extend(b'\0' * (-len(result) % 4))
            sections[i][7:9] = len(result), len(entries)
            for entry in sorted(entries):
                result.extend(struct.pack('<3I', *entry))
        for i, s in enumerate(sections):
            s[9] = len(result)
            struct.pack_into('<11I', result, 104 + i * 44, *s)
        result[:16] = MAGIC
        struct.pack_into('<4I', result, 16, 456, 0, 0, 0)
        struct.pack_into('<18I', result, 32, 7, len(result), zlib.crc32(result[104:]),
                         72, 8, *root_type, *root_address, self.tag, *([0] * 8))
        return bytes(result)
