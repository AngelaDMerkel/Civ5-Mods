"""Strict static BR2 input; never silently drop animation/weights or transform art."""
import math
import re
import shlex
import struct
from dataclasses import dataclass
from pathlib import Path

from .format import FormatError, require

IDENTITY = [1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1]


@dataclass
class Mesh:
    name: str
    vertices: list
    triangles: list


@dataclass
class Model:
    bone: str
    meshes: list[Mesh]


def asset_name(value):
    require(bool(re.fullmatch(r'[A-Za-z][A-Za-z0-9_-]{0,95}', value)), 'asset name must start with a letter and contain only ASCII letters, digits, _ or -')
    return value


def parse(text):
    lines = [(i, line.strip()) for i, line in enumerate(text.splitlines(), 1)
             if line.strip() and not line.lstrip().startswith('//')]
    cursor = 0
    def take():
        nonlocal cursor
        require(cursor < len(lines), 'unexpected end of BR2')
        line = lines[cursor]
        cursor += 1
        return line
    def expect(token):
        line, value = take()
        require(value == token, f'BR2 line {line}: expected {token}')
    def numbers(tokens, line):
        try:
            result = [float(t) for t in tokens]
        except ValueError as e:
            raise FormatError(f'BR2 line {line}: invalid number') from e
        require(all(math.isfinite(v) and abs(v) <= 1e12 for v in result), f'BR2 line {line}: invalid/nonfinite value')
        return result
    def quoted(value, line):
        try:
            return shlex.split(value)
        except ValueError as e:
            raise FormatError(f'BR2 line {line}: malformed quoted name') from e
    expect('skeleton')
    line, value = take()
    tokens = quoted(value, line)
    require(len(tokens) == 26 and tokens[0] == '0' and tokens[2] == '-1', 'only one root bone (ID 0, parent -1) is supported')
    bone = tokens[1]
    require(bone and '\0' not in bone and len(bone.encode()) <= 255, 'invalid bone name')
    values = numbers(tokens[3:], line)
    require(values == [0, 0, 0, 0, 0, 0, 1] + IDENTITY, 'only identity static root transforms are supported')
    line, value = take()
    match = re.fullmatch(r'meshes:(\d+)', value)
    require(match is not None, 'only one static bone is supported; expected meshes:N')
    count = int(match[1])
    require(0 < count <= 128, 'BR2 mesh count must be 1..128')
    meshes = []
    for _ in range(count):
        line, value = take()
        require(value.startswith('mesh:'), f'BR2 line {line}: expected mesh name')
        names = quoted(value[5:], line)
        require(len(names) == 1 and names[0] and '\0' not in names[0]
                and len(names[0].encode()) <= 255, 'invalid mesh name')
        name = names[0]
        require(all(m.name != name for m in meshes), 'duplicate mesh name')
        expect('vertices')
        vertices = []
        while True:
            line, value = take()
            if value == 'triangles':
                break
            tokens = value.split()
            require(len(tokens) == 22, f'BR2 line {line}: expected 22 vertex components (tangent/binormal required)')
            v = numbers(tokens, line)
            require(v[8:16] == [0, 0, 0, 0, 255, 0, 0, 0], f'BR2 line {line}: only full rigid root weights are supported')
            for start in (3, 16, 19):
                require(abs(sum(x*x for x in v[start:start+3]) - 1) < 2e-4, f'BR2 line {line}: non-unit normal/tangent/binormal')
            vertices.append(v)
            require(len(vertices) <= 65536, '16-bit profile supports at most 65536 vertices per mesh')
        require(len(vertices) >= 3, 'mesh needs at least three vertices')
        triangles = []
        while cursor < len(lines):
            line, value = lines[cursor]
            if value.startswith('mesh:') or value == 'end':
                break
            cursor += 1
            try:
                tri = [int(v) for v in value.split()]
            except ValueError as e:
                raise FormatError(f'BR2 line {line}: invalid triangle') from e
            require(len(tri) == 3 and len(set(tri)) == 3 and all(0 <= n < len(vertices) for n in tri), f'BR2 line {line}: invalid triangle indices')
            # Test the actual output precision: large coordinates can collapse
            # otherwise distinct source positions when represented as float32.
            a, b, c = [struct.unpack('<3f', struct.pack('<3f', *vertices[i][:3])) for i in tri]
            u, v = [b[i]-a[i] for i in range(3)], [c[i]-a[i] for i in range(3)]
            cross = [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]]
            require(sum(x*x for x in cross) > 1e-20, f'BR2 line {line}: degenerate triangle')
            triangles.append(tri)
            require(len(triangles) <= 500000, 'too many triangles')
        require(triangles, 'mesh has no triangles')
        meshes.append(Mesh(name, vertices, triangles))
    expect('end')
    require(cursor == len(lines), 'unexpected trailing BR2 records')
    return Model(bone, meshes)


def read(path):
    path = Path(path)
    require(path.stat().st_size <= 64 * 1024 * 1024, 'BR2 exceeds size limit')
    return parse(path.read_text())
