"""Release identities and source composition, separate from mod ownership.

Irrigation has its own source directory but still ships inside Terrain v2.
Only explicitly listed src/ roots may contribute runtime files to a package.
"""
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
BNW_ID = '6DA07636-4123-4018-B643-6575B4EC336B'
RT_ID = 'd571e16c-bb58-40bf-a81f-a919249e7995'
RO_ID = '4547ae42-3d17-4993-99e8-a7a5a2c1ec2c'
TERRAIN = ROOT / 'mods/realistic-terrain/src'
OUTPOSTS = ROOT / 'mods/resource-outposts/src'
IRRIGATION = ROOT / 'mods/irrigated-farm/src'
RUNTIME_SUFFIXES = {'.lua', '.sql', '.xml', '.dds', '.gr2', '.fxsxml', '.ftsxml'}
PACKAGES = [
    dict(source=TERRAIN, components=[IRRIGATION], stage=ROOT/'build/realistic-terrain', name='Realistic Terrain', slug='Realistic-Terrain', version=2, id=RT_ID,
         description='Environmental exposure, cooperative trade logistics and connected desert irrigation. Build Irrigation Works, irrigated farms, the Ministry of Coin, road-connected Caravansaries and patrols. Optional Resource Outposts integration shelters its stationed defenders. Requires Brave New World. Single-player alpha; start a new game.',
         actions=['Text/RT_Text.xml','SQL/RT_Promotions.sql','SQL/RT_ReliefStation.sql','SQL/RT_MinistryOfCoin.sql','SQL/RT_Trade.sql','SQL/RT_MotorizedCaravan.sql','SQL/RT_Irrigation.sql','SQL/RT_Art.sql'], entry='UI/RT_Environment.xml'),
    dict(source=OUTPOSTS, components=[], stage=ROOT/'build/resource-outposts', name='Resource Outposts', slug='Resource-Outposts', version=1, id=RO_ID,
         description='Independent worker-built outposts claim neutral strategic and luxury deposits. Includes an outpost overview, upkeep, abandonment previews, territorial conversion, resource notifications and AI expeditions with escorts, recovery and stalled-order handling. No roads or supply connections required. Optional Realistic Terrain integration adds garrison shelter only. Requires Brave New World. Single-player alpha; start a new game.',
         actions=['Text/RO_Text.xml','SQL/RO_Outposts.sql','SQL/RO_Art.sql'], entry='UI/RO_UI.xml', reload_strategic_view=True),
]


def package_files(spec):
    """Map installed paths to their single authoritative source; reject collisions."""
    files = {}
    installed_paths = {}
    vfs_names = {}
    for source in [spec['source'], *spec['components']]:
        if not source.is_dir():
            raise ValueError(f'Missing package source directory: {source}')
        for path in sorted(source.rglob('*')):
            if not path.is_file() or path.suffix.lower() not in RUNTIME_SUFFIXES:
                continue
            rel = path.relative_to(source).as_posix()
            key = rel.casefold()
            if key in installed_paths:
                raise ValueError(f'Duplicate package path {rel}: {installed_paths[key]} and {path}')
            installed_paths[key] = path
            # Lua and art are flattened into Civ V's shared virtual filesystem.
            if rel.startswith('Lua/') or path.suffix.lower() in {'.dds', '.gr2', '.fxsxml', '.ftsxml'}:
                key = path.name.casefold()
                if key in vfs_names:
                    raise ValueError(f'Duplicate VFS name {path.name}: {vfs_names[key]} and {path}')
                vfs_names[key] = path
            files[rel] = path
    return dict(sorted(files.items()))
