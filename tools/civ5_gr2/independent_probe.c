/* Independent container/geometry check using OpenGR2, not the Python reader.
 * Narrow known Civ V static record layout; does not validate shader behavior.
 */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "gr2.h"
#include "virtual_ptr.h"
#include "crc.h"

static uint32_t u32(const void *p) { uint32_t n; memcpy(&n, p, 4); return n; }
static void *ptr(TGr2 *g, const void *p) { return decode_ptr(&g->virtual_ptr, u32(p)); }

int main(int argc, char **argv) {
    if (argc != 2) { fprintf(stderr, "usage: independent-probe asset.gr2\n"); return 2; }
    FILE *f = fopen(argv[1], "rb");
    if (!f) return 2;
    fseek(f, 0, SEEK_END); long length = ftell(f); rewind(f);
    if (length < 456 || length > 256 * 1024 * 1024) { fclose(f); return 2; }
    unsigned char *data = malloc((size_t)length);
    if (!data || fread(data, 1, length, f) != (size_t)length) { fclose(f); free(data); return 2; }
    fclose(f);
    /* The upstream library is not hardened. Only our uncompressed profile enters it. */
    if (u32(data + 32) != 7 || u32(data + 48) != 8 || u32(data + 88) != 0) { free(data); return 2; }
    for (int i = 0; i < 8; i++) if (u32(data + 104 + 44 * i) != 0) { free(data); return 2; }
    TGr2 g;
    if (!Gr2_Init(&g)) { free(data); return 2; }
    if (!Gr2_Load(data, length, &g)) { Gr2_Free(&g); free(data); return 1; }
    free(data);
    unsigned char *root = g.data + g.sectorOffsets[g.fileInfo.root.sector] + g.fileInfo.root.position;
    unsigned char *type = g.data + g.sectorOffsets[g.fileInfo.type.sector] + g.fileInfo.type.position;
    const char *expected[] = {"ArtToolInfo", "ExporterInfo", "FromFileName", "Textures", "Materials", "Skeletons", "VertexDatas", "TriTopologies", "Meshes", "Models", "TrackGroups", "Animations", "ExtendedData"};
    for (int i = 0; i < 13; i++) {
        const char *name = ptr(&g, type + i * 32 + 4);
        if (!name || strcmp(name, expected[i])) { Gr2_Free(&g); return 1; }
    }
    uint32_t nv = u32(root + 36), nt = u32(root + 44);
    if (nv != nt || nv > 1024) { Gr2_Free(&g); return 1; }
    unsigned char *vs = ptr(&g, root + 40), *ts = ptr(&g, root + 48);
    printf("{\"reader\":\"OpenGR2\",\"meshes\":[");
    for (uint32_t i = 0; i < nv; i++) {
        unsigned char *v = ptr(&g, vs + i * 4), *t = ptr(&g, ts + i * 4);
        uint32_t vertices = u32(v + 4), indices = u32(t + 16);
        unsigned char *vt = ptr(&g, v);
        const char *fields[] = {"Position", "Normal", "Tangent", "Binormal", "TextureCoordinates0"};
        for (int j = 0; j < 5; j++) {
            const char *name = ptr(&g, vt + j * 32 + 4);
            if (!name || strcmp(name, fields[j]) || u32(vt + j * 32) != 10 || u32(vt + j * 32 + 12) != 3) { Gr2_Free(&g); return 1; }
        }
        if (!vertices || vertices > 65536 || !indices || indices > 2000000 || u32(t + 8)) { Gr2_Free(&g); return 1; }
        unsigned char *vp = ptr(&g, v + 8), *ip = ptr(&g, t + 20);
        if (!vp || !ip) { Gr2_Free(&g); return 1; }
        printf("%s{\"vertices\":%u,\"indices\":%u,\"vertex_crc32\":%u,\"index_crc32\":%u}", i ? "," : "", vertices, indices, CRC32(vp, vertices * 60), CRC32(ip, indices * 2));
    }
    printf("]}\n");
    Gr2_Free(&g);
    return 0;
}
