#!/usr/bin/env python3
"""Exercise the real batch-allocator templates under ASan/UBSan on LP64.

Only unrelated engine headers and allocation/assert macros are substituted.
The allocator definitions themselves come directly from FBatchAllocate.h.
"""
# Adapted from the user's Mac port at the revision in platforms/macos/reused-sdk.json.
from pathlib import Path
import subprocess
import tempfile
import unittest

HEADER = Path(__file__).resolve().parents[1] / "engine/sdk/FirePlace/include/FireWorks/FBatchAllocate.h"
PREFIX = """
#include <cassert>
#include <cstddef>
#include <cstdint>
#define FAssert(value) assert(value)
#define FNEW(value, pool, subid) new value
"""
TEST = r'''
struct TwelveBytes { int x, y, z; };
int main() {
    static_assert(sizeof(void*) == 8, "This regression targets the 64-bit port");
    for (unsigned count = 0; count < 64; ++count) {
        for (unsigned height : {0u, 1u, 3u, 31u}) {
            char* bytes; TwelveBytes* structs; double** matrix;
            using Batch = FAllocArrayType<char,
                FAllocArrayType<TwelveBytes,
                FAllocArray2DType<double, FAllocBase<0, 0>>>>;
            AllocData data[] = {{&bytes, count, 0}, {&structs, count, 0}, {&matrix, count, height}};
            Batch batch;
            batch.Alloc(data);
            assert(reinterpret_cast<uintptr_t>(structs) % alignof(TwelveBytes) == 0);
            assert(reinterpret_cast<uintptr_t>(matrix) % alignof(double*) == 0);
            for (unsigned i = 0; i < count; ++i) {
                bytes[i] = static_cast<char>(i);
                structs[i] = {int(i), int(i+1), int(i+2)};
                assert(reinterpret_cast<uintptr_t>(matrix[i]) % alignof(double) == 0);
                for (unsigned j = 0; j < height; ++j) matrix[i][j] = i * 100 + j;
            }
            for (unsigned i = 0; i < count; ++i) {
                assert(bytes[i] == static_cast<char>(i));
                assert(structs[i].x == int(i) && structs[i].y == int(i+1) && structs[i].z == int(i+2));
                for (unsigned j = 0; j < height; ++j) assert(matrix[i][j] == i * 100 + j);
            }
            batch.Free();
        }
    }
}
'''


class BatchAllocatorTests(unittest.TestCase):
    def test_mixed_and_two_dimensional_arrays(self):
        body = "\n".join(line for line in HEADER.read_text(encoding="latin1").splitlines()
                         if not line.startswith(("#include", "#pragma once")))
        with tempfile.TemporaryDirectory(prefix="c5m-batch-test-") as temp:
            source, binary = Path(temp) / "batch.cpp", Path(temp) / "batch"
            source.write_text(PREFIX + "\n#include <initializer_list>\n" + body + TEST)
            subprocess.run(["clang++", "-std=c++11", "-O1", "-g", "-fsanitize=address,undefined",
                            "-fno-sanitize-recover=all", str(source), "-o", str(binary)],
                           check=True, capture_output=True, text=True)
            result = subprocess.run([str(binary)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
