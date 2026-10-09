#!/usr/bin/env python3
"""Validate the package and optionally its SQL/XML against installed Civ V databases."""
import argparse
import hashlib
from pathlib import Path
import sqlite3
import struct
import xml.etree.ElementTree as ET
import zipfile
from packages import PACKAGES, BNW_ID, RT_ID, package_files

ROOT = Path(__file__).resolve().parents[1]


def validate_art(db):
    expected = [("Technologies", "TECH_RT_CARAVAN_LOGISTICS", 0),
                ("Buildings", "BUILDING_CARAVANSARY", 1),
                ("Improvements", "IMPROVEMENT_RT_RELIEF_STATION", 2)]
    for table, kind, index in expected:
        assert db.execute(f"SELECT IconAtlas, PortraitIndex FROM {table} WHERE Type=?", (kind,)).fetchone() == ('RT_PORTRAITS', index)
    assert db.execute("SELECT IconAtlas, IconIndex FROM Builds WHERE Type='BUILD_RT_RELIEF_STATION'").fetchone() == ('RT_CARAVANSARY_ACTION', 0)
    stage = PACKAGES[0]['stage']
    manifest = ET.parse(stage / 'Realistic Terrain.modinfo').getroot()
    vfs = {Path(n.text).name: stage / n.text for n in manifest.find('Files') if n.attrib['import'] == '1'}
    for atlas, sizes in [('RT_PORTRAITS', {32, 45, 64, 80, 128, 214, 256}), ('RT_CARAVANSARY_ACTION', {32, 45, 64})]:
        atlas_rows = db.execute('SELECT IconSize, Filename, IconsPerRow, IconsPerColumn FROM IconTextureAtlases WHERE Atlas=?', (atlas,)).fetchall()
        assert {r[0] for r in atlas_rows} == sizes and len(atlas_rows) == len(sizes)
        for size, filename, cols, rows in atlas_rows:
            assert filename in vfs, f'Atlas missing from VFS: {filename}'
            validate_dds(vfs[filename], (size * int(cols), size * int(rows)))
    filename, anchor = db.execute("SELECT WonderSplashImage, WonderSplashAnchor FROM Buildings WHERE Type='BUILDING_CARAVANSARY'").fetchone()
    assert filename == 'RT_MinistryOfCoin_Wonder.dds' and anchor == 'R,T'
    validate_dds(vfs[filename], (976, 576))
    ui = ET.parse(stage / 'UI/RT_Environment.xml').getroot()
    button = ui.find(".//*[@ID='ConstructionButton']")
    assert button.find('Image').attrib['Texture'] == 'RT_CaravansaryAction32.dds'
    assert button.find('Image').attrib['Texture'] in vfs
    print('Selected artwork: three portraits, worker button/action, wonder splash, atlas sizes, DDS headers and VFS paths validated')


def validate_dds(path, size):
    data = path.read_bytes()
    assert data[:4] == b'DDS ' and struct.unpack_from('<I', data, 4)[0] == 124
    height, width = struct.unpack_from('<2I', data, 12)
    assert (width, height) == size, f'Incorrect DDS size: {path}'
    assert struct.unpack_from('<4I', data, 76) == (32, 65, 0, 32), f'Expected legacy RGBA DDS: {path}'
    assert struct.unpack_from('<4I', data, 92) == (0xff0000, 0xff00, 0xff, 0xff000000)
    assert len(data) == 128 + width * height * 4, f'Truncated DDS: {path}'


def clone(path):
    source = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    memory = sqlite3.connect(":memory:")
    source.backup(memory)
    source.close()
    return memory


def validate_terrain(db, loc, tags, original_trade, trade_fields):
    tech = db.execute("SELECT Description, Civilopedia, Help, Cost, Era, GridX, GridY FROM Technologies WHERE Type='TECH_RT_CARAVAN_LOGISTICS'").fetchone()
    assert tech and all(key in tags for key in tech[:3])
    assert tech[3:] == (275, 'ERA_MEDIEVAL', 5, 10)
    assert db.execute("SELECT COUNT(*) FROM Technologies WHERE GridX=5 AND GridY=10").fetchone()[0] == 1
    assert db.execute("SELECT PrereqTech FROM Technology_PrereqTechs WHERE TechType='TECH_RT_CARAVAN_LOGISTICS'").fetchall() == [('TECH_ENGINEERING',)]
    for unit in ('UNIT_CARAVAN', 'UNIT_CARGO_SHIP'):
        row = db.execute("SELECT Trade, Immobile, Help FROM Units WHERE Type=?", (unit,)).fetchone()
        assert row[:2] == (0, 0) and row[2] in tags
    print("Replacement trade: native trade actions disabled, mobile idle trade units, and Caravan Logistics technology validated")
    validate_motorized_caravan(db, loc, tags)
    ministry = db.execute("SELECT Description, Help, Civilopedia, Strategy, Cost, NumCityCostMod, HurryCostModifier, NeverCapture, NukeImmune, ConquestProb FROM Buildings WHERE Type='BUILDING_CARAVANSARY'").fetchone()
    assert ministry and all(key in tags for key in ministry[:4])
    assert ministry[4:] == (125, 30, -1, 1, 1, 0)
    assert db.execute(f"SELECT {trade_fields} FROM Buildings WHERE Type='BUILDING_CARAVANSARY'").fetchone() == original_trade
    assert original_trade == ('TECH_HORSEBACK_RIDING', 0, 50, 200, 0, 0)
    national_class = db.execute("SELECT Description, DefaultBuilding, MaxGlobalInstances, MaxTeamInstances, MaxPlayerInstances, ExtraPlayerInstances, NoLimit FROM BuildingClasses WHERE Type='BUILDINGCLASS_CARAVANSARY'").fetchone()
    assert national_class == ('TXT_KEY_RT_MINISTRY_OF_COIN', 'BUILDING_CARAVANSARY', -1, -1, 1, 0, 0)
    assert not db.execute("SELECT 1 FROM Building_PrereqBuildingClasses WHERE BuildingType='BUILDING_CARAVANSARY'").fetchall()
    assert loc.execute("SELECT Text FROM Language_en_US WHERE Tag=?", (ministry[0],)).fetchone()[0] == 'Ministry of Coin'
    print("Ministry of Coin: national-wonder limit, cost, capture rules, text, and unchanged native city trade benefits validated")
    promotions = db.execute("SELECT Type, Description, Help, CombatPercent, CannotBeChosen, IconAtlas, PortraitIndex FROM UnitPromotions WHERE Type LIKE 'PROMOTION_RT_%'").fetchall()
    assert len(promotions) == 2
    assert {p[3] for p in promotions} == {-10, -20}
    for kind, desc, help_tag, combat, unselectable, atlas, portrait in promotions:
        assert desc in tags and help_tag in tags and unselectable
        assert loc.execute("SELECT Text FROM Language_en_US WHERE Tag=?", (desc,)).fetchone()
        atlas_rows = db.execute("SELECT IconsPerRow, IconsPerColumn FROM IconTextureAtlases WHERE Atlas=?", (atlas,)).fetchall()
        assert atlas_rows and all(portrait < int(x) * int(y) for x, y in atlas_rows)
    print(f"Installed BNW database: {len(promotions)} promotions and {len(tags)} localized strings validated")
    station = db.execute("SELECT Description, Help, Civilopedia, ArtDefineTag, OutsideBorders, DestroyedWhenPillaged, DefenseModifier, IconAtlas, PortraitIndex FROM Improvements WHERE Type='IMPROVEMENT_RT_RELIEF_STATION'").fetchone()
    assert station and all(key in tags for key in station[:3])
    assert station[3:7] == ('ART_DEF_IMPROVEMENT_FORT', 1, 0, 0)
    atlas = db.execute("SELECT IconsPerRow, IconsPerColumn FROM IconTextureAtlases WHERE Atlas=?", (station[7],)).fetchall()
    assert atlas and all(station[8] < int(x) * int(y) for x, y in atlas)
    build = db.execute("SELECT PrereqTech, ImprovementType, Time, Description, Help FROM Builds WHERE Type='BUILD_RT_RELIEF_STATION'").fetchone()
    assert build[:2] == ('TECH_ENGINEERING', 'IMPROVEMENT_RT_RELIEF_STATION')
    assert build[2] == db.execute("SELECT Time FROM Builds WHERE Type='BUILD_FORT'").fetchone()[0]
    assert build[3] in tags and build[4] in tags
    workers = {r[0] for r in db.execute("SELECT UnitType FROM Unit_Builds WHERE BuildType='BUILD_RT_RELIEF_STATION'")}
    assert not workers, "Native worker actions would bypass the Ministry gate"
    assert db.execute("SELECT 1 FROM Unit_Builds WHERE UnitType='UNIT_WORKER' AND BuildType='BUILD_FORT'").fetchone()
    assert loc.execute("SELECT Text FROM Language_en_US WHERE Tag=?", (station[0],)).fetchone()[0] == 'Caravansary'
    terrains = {r[0] for r in db.execute("SELECT TerrainType FROM Improvement_ValidTerrains WHERE ImprovementType='IMPROVEMENT_RT_RELIEF_STATION'")}
    assert terrains == {'TERRAIN_GRASS', 'TERRAIN_PLAINS', 'TERRAIN_DESERT', 'TERRAIN_TUNDRA', 'TERRAIN_SNOW'}
    features = db.execute("SELECT FeatureType, Remove FROM BuildFeatures WHERE BuildType='BUILD_RT_RELIEF_STATION'").fetchall()
    assert ('FEATURE_JUNGLE', 0) in features and ('FEATURE_FOREST', 0) in features
    print("Caravansary: improvement, gated construction data, terrain validity, feature preservation, art, and technology validated")
    validate_irrigation(db, loc, tags)
    validate_art(db)


def validate_motorized_caravan(db, loc, tags):
    kind = 'UNIT_RT_MOTORIZED_CARAVAN'
    row = db.execute('SELECT Description, Civilopedia, Strategy, Help, Class, PrereqTech, Cost, Moves, Trade, Immobile, Domain, Combat, NoMaintenance FROM Units WHERE Type=?', (kind,)).fetchone()
    assert row and all(key in tags for key in row[:4])
    assert row[4:] == ('UNITCLASS_RT_MOTORIZED_CARAVAN', 'TECH_COMBUSTION', 150, 2, 0, 0, 'DOMAIN_LAND', 0, 1)
    assert loc.execute('SELECT Text FROM Language_en_US WHERE Tag=?', (row[0],)).fetchone()[0] == 'Motorized Caravan'
    assert db.execute("SELECT DefaultUnit, MaxGlobalInstances, MaxTeamInstances, MaxPlayerInstances FROM UnitClasses WHERE Type='UNITCLASS_RT_MOTORIZED_CARAVAN'").fetchone() == (kind, -1, -1, -1)
    assert not db.execute("SELECT 1 FROM Unit_ClassUpgrades WHERE UnitClassType='UNITCLASS_RT_MOTORIZED_CARAVAN'").fetchall()
    assert db.execute("SELECT ObsoleteTech, Cost FROM Units WHERE Type='UNIT_CARAVAN'").fetchone() == (None, 75)
    assert not db.execute('SELECT 1 FROM Unit_ResourceQuantityRequirements WHERE UnitType=?', (kind,)).fetchall()
    promotions = {r[0] for r in db.execute('SELECT PromotionType FROM Unit_FreePromotions WHERE UnitType=?', (kind,))}
    assert 'PROMOTION_IGNORE_TERRAIN_COST' in promotions
    assert db.execute("SELECT IgnoreTerrainCost FROM UnitPromotions WHERE Type='PROMOTION_IGNORE_TERRAIN_COST'").fetchone() == (1,)
    assert {r[0] for r in db.execute("SELECT PromotionType FROM Unit_FreePromotions WHERE UnitType='UNIT_CARAVAN'")} <= promotions
    art = 'UnitArtInfo, UnitArtInfoEraVariation, UnitFlagIconOffset, PortraitIndex, IconAtlas, UnitFlagAtlas'
    assert db.execute(f'SELECT {art} FROM Units WHERE Type=?', (kind,)).fetchone() == db.execute(f"SELECT {art} FROM Units WHERE Type='UNIT_CARAVAN'").fetchone()
    assert db.execute('SELECT FlavorType, Flavor FROM Unit_Flavors WHERE UnitType=? ORDER BY FlavorType', (kind,)).fetchall() == db.execute("SELECT FlavorType, Flavor FROM Unit_Flavors WHERE UnitType='UNIT_CARAVAN' ORDER BY FlavorType").fetchall()
    print('Motorized Caravan: independent Combustion unlock, both units trainable, no replacement chain, movement promotion, text and stock art validated')


def validate_irrigation(db, loc, tags):
    building = db.execute("SELECT Description, Civilopedia, Strategy, Help, Cost, GoldMaintenance, PrereqTech, FoodKept, BuildingClass, IconAtlas, PortraitIndex FROM Buildings WHERE Type='BUILDING_RT_IRRIGATION_WORKS'").fetchone()
    assert building and all(key in tags for key in building[:4])
    assert building[4:9] == (100, 1, 'TECH_ENGINEERING', 0, 'BUILDINGCLASS_RT_IRRIGATION_WORKS')
    assert db.execute("SELECT MaxGlobalInstances, MaxTeamInstances, MaxPlayerInstances FROM BuildingClasses WHERE Type='BUILDINGCLASS_RT_IRRIGATION_WORKS'").fetchone() == (-1, -1, -1)
    for kind, food in [('IMPROVEMENT_RT_IRRIGATED_FARM', 3), ('IMPROVEMENT_RT_DRY_FARM', 1)]:
        row = db.execute("SELECT Description, Civilopedia, Help, ArtDefineTag, RequiresFlatlands, OutsideBorders, DestroyedWhenPillaged, FreshWaterMakesValid, IconAtlas, PortraitIndex FROM Improvements WHERE Type=?", (kind,)).fetchone()
        assert all(key in tags for key in row[:3])
        assert row[3:8] == ('ART_DEF_IMPROVEMENT_FARM', 1, 0, 0, 0)
        assert db.execute("SELECT TerrainType FROM Improvement_ValidTerrains WHERE ImprovementType=?", (kind,)).fetchall() == [('TERRAIN_DESERT',)]
        assert db.execute("SELECT YieldType, Yield FROM Improvement_Yields WHERE ImprovementType=?", (kind,)).fetchall() == [('YIELD_FOOD', food)]
        assert db.execute("SELECT ResourceType, ResourceMakesValid, ResourceTrade FROM Improvement_ResourceTypes WHERE ImprovementType=?", (kind,)).fetchall() == [('RESOURCE_WHEAT', 1, 1)]
        for table in ['Improvement_TechYieldChanges', 'Improvement_TechFreshWaterYieldChanges', 'Improvement_TechNoFreshWaterYieldChanges']:
            assert db.execute(f"SELECT TechType, YieldType, Yield FROM {table} WHERE ImprovementType=? ORDER BY TechType, YieldType", (kind,)).fetchall() == db.execute(f"SELECT TechType, YieldType, Yield FROM {table} WHERE ImprovementType='IMPROVEMENT_FARM' ORDER BY TechType, YieldType").fetchall()
        atlas = db.execute("SELECT IconsPerRow, IconsPerColumn FROM IconTextureAtlases WHERE Atlas=?", (row[8],)).fetchall()
        assert atlas and all(row[9] < int(x) * int(y) for x, y in atlas)
    atlas = db.execute("SELECT IconsPerRow, IconsPerColumn FROM IconTextureAtlases WHERE Atlas=?", (building[9],)).fetchall()
    assert atlas and all(building[10] < int(x) * int(y) for x, y in atlas)
    build = db.execute("SELECT PrereqTech, ImprovementType, Time, Description, Help FROM Builds WHERE Type='BUILD_RT_IRRIGATED_FARM'").fetchone()
    assert build[:2] == ('TECH_ENGINEERING', 'IMPROVEMENT_RT_DRY_FARM')
    assert build[2] == db.execute("SELECT Time FROM Builds WHERE Type='BUILD_FARM'").fetchone()[0]
    assert build[3] in tags and build[4] in tags
    assert not db.execute("SELECT 1 FROM Unit_Builds WHERE BuildType='BUILD_RT_IRRIGATED_FARM'").fetchall(), 'Native action would bypass local works and water gates'
    assert not db.execute("SELECT 1 FROM BuildFeatures WHERE BuildType='BUILD_RT_IRRIGATED_FARM'").fetchall(), 'Irrigation must not clear features'
    print("Irrigation: local building, gated worker action, wet/dry yields, farm technology progression, wheat, localization and native art validated")


def validate_outposts(db, loc, tags):
    outpost = db.execute("SELECT Description, Help, Civilopedia, ArtDefineTag, OutsideBorders, DestroyedWhenPillaged, DefenseModifier, BuildableOnResources, GoldMaintenance FROM Improvements WHERE Type='IMPROVEMENT_RT_RESOURCE_OUTPOST'").fetchone()
    assert outpost and all(key in tags for key in outpost[:3])
    assert outpost[3:] == ('ART_DEF_IMPROVEMENT_FORT', 1, 0, 50, 0, 0)
    outpost_build = db.execute("SELECT PrereqTech, ImprovementType, Time FROM Builds WHERE Type='BUILD_RT_RESOURCE_OUTPOST'").fetchone()
    assert outpost_build == ('TECH_ENGINEERING', 'IMPROVEMENT_RT_RESOURCE_OUTPOST', db.execute("SELECT Time FROM Builds WHERE Type='BUILD_FORT'").fetchone()[0])
    assert not db.execute("SELECT 1 FROM Unit_Builds WHERE BuildType='BUILD_RT_RESOURCE_OUTPOST'").fetchall()
    resources = {r[0] for r in db.execute("SELECT ResourceType FROM Improvement_ResourceTypes WHERE ImprovementType='IMPROVEMENT_RT_RESOURCE_OUTPOST' AND ResourceMakesValid=1 AND ResourceTrade=1")}
    assert {'RESOURCE_IRON', 'RESOURCE_HORSE', 'RESOURCE_COAL', 'RESOURCE_OIL', 'RESOURCE_ALUMINUM', 'RESOURCE_URANIUM', 'RESOURCE_SILK', 'RESOURCE_MARBLE', 'RESOURCE_IVORY', 'RESOURCE_COCOA'} <= resources
    assert not resources.intersection({'RESOURCE_ARTIFACTS', 'RESOURCE_HIDDEN_ARTIFACTS', 'RESOURCE_WHEAT', 'RESOURCE_WHALE', 'RESOURCE_PEARLS', 'RESOURCE_CRAB', 'RESOURCE_JEWELRY'})
    outpost_features = db.execute("SELECT FeatureType, PrereqTech, Remove FROM BuildFeatures WHERE BuildType='BUILD_RT_RESOURCE_OUTPOST' ORDER BY FeatureType").fetchall()
    assert outpost_features == db.execute("SELECT FeatureType, PrereqTech, Remove FROM BuildFeatures WHERE BuildType='BUILD_FORT' ORDER BY FeatureType").fetchall()
    print(f"Resource Outposts: {len(resources)} land resources, normal annexed extraction, fort defense/work, gated construction, and text validated")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cache", type=Path, help="Civ V cache directory for real-schema validation")
    args = parser.parse_args()
    all_tags, vfs_names = set(), set()
    for spec in PACKAGES:
        mod = spec["stage"]
        sources = package_files(spec)
        manifest = ET.parse(mod / (spec["name"] + ".modinfo")).getroot()
        assert manifest.attrib == {"id": spec["id"], "version": str(spec["version"])}
        files = set()
        for node in manifest.find("Files"):
            path = mod / node.text
            assert node.text in sources, f'Unexpected packaged source: {node.text}'
            assert path.is_file(), f"Missing {path}"
            assert path.read_bytes() == sources[node.text].read_bytes(), f'Stale build: {sources[node.text]}; run tools/build.py'
            assert hashlib.md5(path.read_bytes()).hexdigest().upper() == node.attrib["md5"], f"Stale manifest hash: {path}"
            if path.suffix == ".xml": ET.parse(path)
            if node.attrib["import"] == "1":
                assert path.name.casefold() not in vfs_names, f"Cross-mod VFS collision: {path.name}"
                vfs_names.add(path.name.casefold())
            files.add(node.text)
            if path.suffix == '.dds':
                assert node.attrib['import'] == '1', f'Texture must be in VFS: {path}'
        assert files == set(sources), 'Manifest must contain every runtime source exactly once'
        for node in manifest.findall("Actions/OnModActivated/UpdateDatabase") + manifest.findall("EntryPoints/EntryPoint"):
            assert (node.text if node.tag == "UpdateDatabase" else node.attrib["file"]) in files
        assert [n.text for n in manifest.findall("Actions/OnModActivated/UpdateDatabase")] == spec["actions"]
        assert manifest.find("Dependencies/Dlc").attrib["id"] == BNW_ID
        assert manifest.find("Dependencies/Mod") is None, "Both packages must work independently"
        if spec["id"] != RT_ID:
            assert manifest.find("References/Mod").attrib["id"] == RT_ID
            assert manifest.find("References/Mod").attrib["minversion"] == "2"
            assert manifest.find("Blocks/Mod").attrib["maxversion"] == "1"
        rows = ET.parse(mod / spec["actions"][0]).getroot().find("Language_en_US")
        tags = {row.attrib["Tag"] for row in rows}
        assert len(tags) == len(rows), "Duplicate translation tag"
        assert not tags & all_tags, "Cross-mod translation collision"
        all_tags |= tags
        folder = spec["name"] + " (v " + str(spec["version"]) + ")"
        archive = ROOT / "dist" / (spec["slug"] + "-v" + str(spec["version"]) + ".zip")
        payload = files | {spec["name"] + ".modinfo"}
        with zipfile.ZipFile(archive) as z:
            assert set(z.namelist()) == {folder + "/" + f for f in payload}
            for f in payload:
                assert z.read(folder + "/" + f) == (mod / f).read_bytes() == (ROOT / "dist" / folder / f).read_bytes()
        print(f'{spec["name"]}: {len(files)} files, hashes, XML and ZIP/source parity valid')
    if not args.cache: return
    # Also test both SQL load orders: optional integration cannot depend on one.
    for specs in ([PACKAGES[0]], [PACKAGES[1]], PACKAGES, list(reversed(PACKAGES))):
        db = clone(args.cache / "Civ5DebugDatabase.db")
        loc = clone(args.cache / "Localization-Merged.db")
        trade_fields = "PrereqTech, GoldMaintenance, TradeRouteLandDistanceModifier, TradeRouteLandGoldBonus, TradeRouteSeaDistanceModifier, TradeRouteSeaGoldBonus"
        original_trade = db.execute(f"SELECT {trade_fields} FROM Buildings WHERE Type='BUILDING_CARAVANSARY'").fetchone()
        original_building = db.execute("SELECT * FROM Buildings WHERE Type='BUILDING_CARAVANSARY'").fetchone()
        original_units = db.execute("SELECT Type, Trade, Immobile, Help FROM Units WHERE Type IN ('UNIT_CARAVAN', 'UNIT_CARGO_SHIP') ORDER BY Type").fetchall()
        tags = set()
        for spec in specs:
            for action in spec["actions"]:
                path = spec["stage"] / action
                if path.suffix == ".sql": db.executescript(path.read_text())
                else:
                    for row in ET.parse(path).getroot().find("Language_en_US"):
                        loc.execute("INSERT INTO Language_en_US (Tag, Text) VALUES (?, ?)", (row.attrib["Tag"], row.findtext("Text")))
                        tags.add(row.attrib["Tag"])
        print("Database configuration: " + " + ".join(s["name"] for s in specs))
        if PACKAGES[0] in specs:
            validate_terrain(db, loc, tags, original_trade, trade_fields)
        else:
            assert db.execute("SELECT * FROM Buildings WHERE Type='BUILDING_CARAVANSARY'").fetchone() == original_building
            assert db.execute("SELECT Type, Trade, Immobile, Help FROM Units WHERE Type IN ('UNIT_CARAVAN', 'UNIT_CARGO_SHIP') ORDER BY Type").fetchall() == original_units
            assert not db.execute("SELECT 1 FROM UnitPromotions WHERE Type LIKE 'PROMOTION_RT_%'").fetchall()
            assert not db.execute("SELECT 1 FROM Improvements WHERE Type='IMPROVEMENT_RT_RELIEF_STATION'").fetchall()
            assert not db.execute("SELECT 1 FROM Technologies WHERE Type='TECH_RT_CARAVAN_LOGISTICS'").fetchall()
            assert not db.execute("SELECT 1 FROM Units WHERE Type='UNIT_RT_MOTORIZED_CARAVAN'").fetchall()
            assert not db.execute("SELECT 1 FROM Unit_ClassUpgrades WHERE UnitType='UNIT_CARAVAN'").fetchall()
            assert not db.execute("SELECT 1 FROM Buildings WHERE Type='BUILDING_RT_IRRIGATION_WORKS'").fetchall()
            assert not db.execute("SELECT 1 FROM Improvements WHERE Type IN ('IMPROVEMENT_RT_IRRIGATED_FARM', 'IMPROVEMENT_RT_DRY_FARM')").fetchall()
            print("Outposts alone: native trade, buildings and environment unchanged")
        if PACKAGES[1] in specs: validate_outposts(db, loc, tags)
        else:
            assert not db.execute("SELECT 1 FROM Improvements WHERE Type='IMPROVEMENT_RT_RESOURCE_OUTPOST'").fetchall()
            assert not db.execute("SELECT 1 FROM Builds WHERE Type='BUILD_RT_RESOURCE_OUTPOST'").fetchall()
            print("Terrain alone: no outpost definitions")
        db.close(); loc.close()


if __name__ == "__main__": main()
