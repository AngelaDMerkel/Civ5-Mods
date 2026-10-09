#!/usr/bin/env python3
"""Build an installable folder and ZIP; regenerate MD5s and a ModBuddy project."""
from pathlib import Path
import hashlib
import shutil
import xml.etree.ElementTree as ET
import zipfile

from packages import ROOT, BNW_ID, RT_ID, PACKAGES


def imports_into_vfs(path):
    return path.startswith("Lua/") or Path(path).suffix.lower() in {".dds", ".gr2", ".fxsxml", ".ftsxml"}


def write_xml(root, path):
    ET.indent(root, space="  ")
    ET.ElementTree(root).write(path, encoding="utf-8", xml_declaration=True)


def manifest(files, spec):
    source = spec["source"]
    mod = ET.Element("Mod", id=spec["id"], version=str(spec["version"]))
    props = ET.SubElement(mod, "Properties")
    for key, value in {
        "Name": spec["name"], "Stability": "Alpha",
        "Teaser": "Prepare expeditions beyond your borders." if spec["id"] == RT_ID else "Secure remote resources with independent, defended outposts.",
        "Description": spec["description"],
        "Authors": "Duffy", "HideSetupGame": "0", "AffectsSavedGames": "1",
        "MinCompatibleSaveVersion": str(spec["version"]), "SupportsSinglePlayer": "1",
        "SupportsMultiplayer": "0", "SupportsHotSeat": "0", "SupportsMac": "1",
        "SupportsLeaderboards": "0", "ReloadLandmarkSystem": "1",
        "ReloadStrategicViewSystem": "0", "ReloadUnitSystem": "0",
    }.items():
        ET.SubElement(props, key).text = value
    deps = ET.SubElement(mod, "Dependencies")
    ET.SubElement(deps, "Dlc", id=BNW_ID, minversion="0", maxversion="999")
    refs = ET.SubElement(mod, "References")
    if spec["id"] != RT_ID:
        ET.SubElement(refs, "Mod", id=RT_ID, minversion="2", maxversion="999", title="Realistic Terrain")
    blocks = ET.SubElement(mod, "Blocks")
    if spec["id"] != RT_ID:
        ET.SubElement(blocks, "Mod", id=RT_ID, minversion="0", maxversion="1", title="Realistic Terrain (old bundled outposts)")
    entries = ET.SubElement(mod, "Files")
    for path in files:
        rel = path.relative_to(source).as_posix()
        ET.SubElement(entries, "File", {"md5": hashlib.md5(path.read_bytes()).hexdigest().upper(),
            "import": "1" if imports_into_vfs(rel) else "0"}).text = rel
    actions = ET.SubElement(ET.SubElement(mod, "Actions"), "OnModActivated")
    for path in spec["actions"]:
        ET.SubElement(actions, "UpdateDatabase").text = path
    entry = ET.SubElement(ET.SubElement(mod, "EntryPoints"), "EntryPoint",
                          type="InGameUIAddin", file=spec["entry"])
    ET.SubElement(entry, "Name").text = spec["name"]
    ET.SubElement(entry, "Description").text = spec["description"]
    return mod


def modbuddy(files, mod, spec):
    source = spec["source"]
    ns = "http://schemas.microsoft.com/developer/msbuild/2003"
    ET.register_namespace("", ns)
    def tag(s): return f"{{{ns}}}{s}"
    project = ET.Element(tag("Project"), ToolsVersion="4.0", DefaultTargets="Build")
    props = ET.SubElement(project, tag("PropertyGroup"))
    values = {"ProjectGuid": "{" + spec["id"].upper() + "}", "ModGuid": spec["id"],
              "ModVersion": str(spec["version"]), "RootNamespace": spec["name"].replace(" ", ""), "AssemblyName": spec["name"]}
    values.update({el.tag: el.text for el in mod.find("Properties")})
    for k, v in values.items(): ET.SubElement(props, tag(k)).text = v
    # ModBuddy serializes these sections as XML strings inside project properties.
    for key in ("Dependencies", "References", "Blocks", "Actions", "EntryPoints"):
        ET.SubElement(props, tag(key)).text = ET.tostring(mod.find(key), encoding="unicode")
    for configuration in ("Debug", "Release"):
        group = ET.SubElement(project, tag("PropertyGroup"), Condition=f"'$(Configuration)' == '{configuration}'")
        ET.SubElement(group, tag("OutputPath")).text = f"bin\\{configuration}\\"
    items = ET.SubElement(project, tag("ItemGroup"))
    for path in files:
        rel = path.relative_to(source).as_posix()
        item = ET.SubElement(items, tag("Content"), Include=rel.replace("/", "\\"))
        ET.SubElement(item, tag("ImportIntoVFS")).text = "True" if imports_into_vfs(rel) else "False"
    ET.SubElement(project, tag("Import"), Project="$(MSBuildExtensionsPath)\\Firaxis\\ModBuddy\\Civ5Mod.targets")
    return project


def build(spec):
    source = spec["source"]
    files = sorted(p for p in source.rglob("*") if p.suffix.lower() in {".lua", ".sql", ".xml", ".dds", ".gr2", ".fxsxml", ".ftsxml"})
    mod = manifest(files, spec)
    manifest_path = source / (spec["name"] + ".modinfo")
    write_xml(mod, manifest_path)
    write_xml(modbuddy(files, mod, spec), source / (spec["name"] + ".civ5proj"))
    output = ROOT / "dist" / (spec["name"] + " (v " + str(spec["version"]) + ")")
    if output.exists(): shutil.rmtree(output)
    output.mkdir(parents=True)
    for path in files + [manifest_path]:
        dest = output / path.relative_to(source)
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)
    archive = ROOT / "dist" / (spec["slug"] + "-v" + str(spec["version"]) + ".zip")
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
        for path in sorted(output.rglob("*")):
            if path.is_file():
                info = zipfile.ZipInfo(path.relative_to(output.parent).as_posix(), (2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o644 << 16
                z.writestr(info, path.read_bytes())
    print(f"Packaged {archive}")


if __name__ == "__main__":
    for spec in PACKAGES: build(spec)
