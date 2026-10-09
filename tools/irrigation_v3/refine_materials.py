"""Pack the original painted atlas for mesh-review and DDS consumption."""
from pathlib import Path
from PIL import Image

HERE=Path(__file__).resolve().parent
SOURCE_ATLAS=HERE/'painted_atlas.png' if HERE.name=='source' else HERE.parents[1]/'shared/art/irrigated-farm/mesh-v3-review/painted-atlas.png'
SOURCE_PROMPT=SOURCE_ATLAS.with_name('texture-prompt.txt')

def make_atlas(folder):
    im=Image.open(SOURCE_ATLAS).convert('RGBA')
    # Standard GPU texture size; this does not add painted source detail.
    atlas=im.resize((2048,2048),Image.Resampling.LANCZOS)
    atlas.save(folder/'RT_IF_Diffuse.png');atlas.save(folder/'RT_IF_Diffuse.dds')
    Image.new('RGBA',(4,4),(128,128,255,255)).save(folder/'RT_IF_FlatNormal.dds')
    Image.new('RGBA',(4,4),(0,0,0,255)).save(folder/'RT_IF_BlackSpec.dds')
    return atlas
