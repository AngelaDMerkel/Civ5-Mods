#include "C5M_RandomSeed.h"
#include <climits>
#include <iostream>

int main() {
    // Independent fixed-width reference, including high seed bits on LP64.
    if (UINT_MAX != 0xffffffffU) return 1;
    const unsigned long seeds[] = {0, 1, 42, 0x80000000UL, 0xffffffffUL, ULONG_MAX};
    unsigned long checks = 0;
    for (unsigned int s = 0; s < sizeof(seeds) / sizeof(seeds[0]); ++s) {
        unsigned long actual = C5M::NormalizeRandomSeed(seeds[s]);
        unsigned int reference = static_cast<unsigned int>(seeds[s]);
        if (actual != reference) return 2;
        for (int i = 0; i < 1000000; ++i) {
            reference = reference * 1103515245U + 12345U;
            actual = C5M::NextRandomSeed(actual, 1103515245UL, 12345UL);
            if (actual != reference) return 3;
            ++checks;
        }
    }
    std::cout << checks << " BNW RNG transitions match uint32 reference\n";
    return 0;
}
