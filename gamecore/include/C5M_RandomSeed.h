#ifndef C5M_RANDOM_SEED_H
#define C5M_RANDOM_SEED_H

namespace C5M {
// Preserve BNW's Windows uint32 sequence on LP64 hosts. Keep the public
// unsigned-long signature and host serialization ABI unchanged.
inline unsigned long NormalizeRandomSeed(unsigned long seed) {
    return seed & 0xffffffffUL;
}

inline unsigned long NextRandomSeed(unsigned long seed,
                                   unsigned long multiplier,
                                   unsigned long increment) {
    return NormalizeRandomSeed(seed * multiplier + increment);
}
}
#endif
