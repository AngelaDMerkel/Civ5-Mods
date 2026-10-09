"""Experimental uncompressed Granny 7 writer for the reader's reflected graph.

Preserves native schemas and material parameters; emits ordinary relocated UTF-8
strings (no external GSD). Output must pass native-engine testing before shipping.
"""
from pathlib import Path
import struct
import zlib
from native_gr2 import MAGIC, SCALAR


class Writer:
    def __init__(self, reader):
        self.reader = reader
        self.sections = [bytearray() for _ in range(8)]
        self.fix = [{} for _ in range(8)]
        self.objects, self.types, self.strings = {}, {}, {}

    def allocate(self, section, size, alignment=4):
        data = self.sections[section]
        data.extend(b'\0'*(-len(data) % alignment))
        pointer = (section, len(data))
        data.extend(b'\0'*size)
        return pointer

    def put(self, pointer, fmt, *values):
        struct.pack_into('<'+fmt, self.sections[pointer[0]], pointer[1], *values)

    def link(self, source, target):
        if target is not None:
            self.fix[source[0]][source[1]] = target

    def string(self, value):
        if value is None:
            return None
        if value not in self.strings:
            raw = value.encode('utf8')+b'\0'
            p = self.allocate(7, len(raw), 1)
            self.sections[7][p[1]:p[1]+len(raw)] = raw
            self.strings[value] = p
        return self.strings[value]

    def schema(self, old):
        if old is None:
            return None
        if old in self.types:
            return self.types[old]
        members = self.reader.schema(old)
        p = self.allocate(6, (len(members)+1)*32)
        self.types[old] = p
        for i, member in enumerate(members):
            q = p[1]+i*32
            section, offset = member['defptr']
            # Array-size zero differs from one in type metadata; preserve it.
            raw = self.reader.data[section][offset:offset+32]
            self.sections[6][q:q+32] = raw
            self.put((6, q+4), 'II', 0, 0)
            self.link((6, q+4), self.string(member['name']))
            self.link((6, q+8), self.schema(member['nested']))
        return p

    def obj(self, value, kind=None, destination=None):
        if value is None:
            return None
        kind = kind or value['_type']
        key = id(value)
        if destination is None and key in self.objects:
            return self.objects[key]
        p = destination or self.allocate(0, self.reader.size(kind))
        self.objects[key] = p
        offset = p[1]
        for member in self.reader.schema(kind):
            values = value[member['name']]
            if member['count'] == 1:
                values = [values]
            for item in values:
                self.value((p[0], offset), member, item)
                offset += self.reader.member_size(member)
        return p

    def value(self, p, member, value):
        kind, nested = member['type'], member['nested']
        s, o = p
        if kind == 1:
            self.obj(value, nested, p)
        elif kind == 2:
            self.link(p, self.obj(value, nested))
        elif kind in (3, 4, 7):
            if kind == 7:
                nested = value[0]['_type'] if value else None
                self.link(p, self.schema(nested))
                o += 4
            self.put((s, o), 'I', len(value))
            if value:
                # Native vertex/index storage remains separated from object records.
                section = 1 if member['name'] == 'Vertices' else 2 if member['name'] in ('Indices16', 'Indices') else 0
                stride = 4 if kind == 4 else self.reader.size(nested)
                array = self.allocate(section, len(value)*stride)
                self.link((s, o+4), array)
                for i, item in enumerate(value):
                    q = (array[0], array[1]+i*stride)
                    if kind == 4:
                        self.link(q, self.obj(item, nested))
                    else:
                        self.obj(item, nested, q)
        elif kind == 5:
            if value:
                self.link(p, self.schema(value['_type']))
                self.link((s, o+4), self.obj(value))
        elif kind == 8:
            self.link(p, self.string(value))
        elif kind == 9:
            self.put(p, 'I16f', *value)
        elif kind == 22:
            if value is not None:
                raise ValueError('Cannot serialize an untyped non-null reference')
        else:
            self.put(p, SCALAR[kind], value)

    def write(self, path, root):
        root_type = self.schema(root['_type'])
        root_node = self.obj(root)
        blob = bytearray(456)
        headers = []
        for i, data in enumerate(self.sections):
            blob.extend(b'\0'*(-len(blob) % 4))
            offset = len(blob)
            blob.extend(data)
            blob.extend(b'\0'*(-len(blob) % 4))
            reloc_offset = len(blob)
            for source, target in sorted(self.fix[i].items()):
                blob.extend(struct.pack('<III', source, *target))
            headers.append((0, offset, len(data), len(data), 4, len(data), len(data),
                            reloc_offset, len(self.fix[i]), 0, 0))
        blob[:16] = MAGIC
        struct.pack_into('<4I', blob, 16, 456, 0, 0, 0)
        h = list(self.reader.header)
        h[1], h[2], h[3], h[4] = len(blob), 0, 72, 8
        h[5:9] = [*root_type, *root_node]
        # No external string database: all names now have ordinary relocations.
        h[14] = 0
        struct.pack_into('<18I', blob, 32, *h)
        for i, header in enumerate(headers):
            struct.pack_into('<11I', blob, 104+44*i, *header)
        struct.pack_into('<I', blob, 40, zlib.crc32(blob[104:]))
        Path(path).write_bytes(blob)
        return len(blob)
