"""Synthetic, redistributable GR2 regression fixtures; no game install needed."""
import struct
import unittest
import zlib

from tools.civ5_gr2.format import Definition, FormatError, Member, Node, Reader, VariantArray, Writer


def crc(data):
    data = bytearray(data)
    struct.pack_into('<I', data, 40, zlib.crc32(data[104:]))
    return bytes(data)


class ContainerTests(unittest.TestCase):
    def fixture(self):
        child = Definition([Member('Name', 8), Member('Values', 10, width=3)])
        root = Definition([Member('Direct', 2, child), Member('References', 4, child),
                           Member('Array', 3, child), Member('Variant', 5), Member('Vertices', 7)])
        a = Node(child, {'Name': 'shared', 'Values': [1.25, -2, 3.5]})
        b = Node(child, {'Name': 'second', 'Values': [4, 5, 6]})
        return Node(root, {'Direct': a, 'References': [a], 'Array': [b], 'Variant': a,
                           'Vertices': VariantArray(child, [Node(child, b.values.copy())])})

    def test_graph_identity_and_dynamic_arrays(self):
        data = Writer().encode(self.fixture())
        reader = Reader(data)
        root = reader.root()
        self.assertIs(root['Direct'], root['References'][0])
        self.assertIs(root['Direct'], root['Variant'])
        self.assertEqual(root['Array'][0]['Values'], [4, 5, 6])
        self.assertEqual(root['Vertices'].items[0]['Name'], 'second')
        self.assertEqual(root['Direct']['Values'], [1.25, -2, 3.5])
        self.assertTrue(all(s[0] == 0 for s in reader.sections))

    def test_deterministic_serialization(self):
        self.assertEqual(Writer().encode(self.fixture()), Writer().encode(self.fixture()))

    def test_corruption_and_truncation(self):
        data = Writer().encode(self.fixture())
        for damaged in (b'', data[:-1], data[:500], data[:500] + bytes([data[500] ^ 1]) + data[501:]):
            with self.subTest(length=len(damaged)), self.assertRaises(FormatError):
                Reader(damaged)

    def test_invalid_relocation_checked_after_crc(self):
        data = bytearray(Writer().encode(self.fixture()))
        section = struct.unpack_from('<11I', data, 104)
        struct.pack_into('<I', data, section[7] + 4, 99)
        with self.assertRaisesRegex(FormatError, 'section reference'):
            Reader(crc(data))

    def test_duplicate_relocation(self):
        data = bytearray(Writer().encode(self.fixture()))
        section = struct.unpack_from('<11I', data, 104)
        data[section[7] + 12:section[7] + 24] = data[section[7]:section[7] + 12]
        with self.assertRaisesRegex(FormatError, 'duplicate relocation'):
            Reader(crc(data))

    def test_unresolved_hash_rejected(self):
        data = bytearray(Writer().encode(self.fixture()))
        struct.pack_into('<I', data, 88, 2)
        reader = Reader(data)
        address = reader.root_type[0], reader.root_type[1] + 4
        del reader.relocations[address]
        with self.assertRaisesRegex(FormatError, 'unresolved string hash'):
            reader.root()

    def test_array_count_cannot_allocate_unbounded(self):
        data = Writer().encode(self.fixture())
        reader = Reader(data)
        b = bytearray(reader.buffers[0]);struct.pack_into('<I', b, 4, 0xffffffff)
        reader.buffers[0] = b
        with self.assertRaisesRegex(FormatError, 'invalid array count'):
            reader.root()


if __name__ == '__main__':
    unittest.main()
