"""Render the two actual mesh versions with one camera and lighting setup."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from irrigation_mesh_io import render_glb

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'output/models/irrigated-farm-v3'
fontpath='/System/Library/Fonts/Supplemental/Arial.ttf'
font=ImageFont.truetype(fontpath,23)
small=ImageFont.truetype(fontpath,17)
sheet=Image.new('RGB',(1400,1160),(232,226,210));d=ImageDraw.Draw(sheet)
d.text((26,20),'IRRIGATED FARM  /  TERRAIN AND MATERIAL REVISION',font=font,fill=(49,60,43))
d.text((26,55),'Same renderer, camera and lighting. Source meshes; not screenshots from Civ V.',font=small,fill=(87,91,76))
for row,version in enumerate(('v2','v3')):
    for col,kind in enumerate(('Flat','SteepHill')):
        name=f'RT_IF_{kind}_Wet';path=ROOT/f'output/models/irrigated-farm-{version}'/name/(name+'.glb')
        x,y=col*700,94+row*450
        sheet.paste(render_glb(path,700,410),(x,y+32))
        d.text((x+25,y),f'{version.upper()}  /  {kind}',font=font,fill=(49,60,43))
for col,kind in enumerate(('Flat','SteepHill')):
    x=col*700
    d.text((x+25,1010),'Reduced preview size',font=small,fill=(87,91,76))
    for j,version in enumerate(('v2','v3')):
        name=f'RT_IF_{kind}_Wet';path=ROOT/f'output/models/irrigated-farm-{version}'/name/(name+'.glb')
        sheet.paste(render_glb(path,180,130),(x+240+j*205,1000))
        d.text((x+304+j*205,1135),version.upper(),font=small,fill=(49,60,43))
sheet.save(OUT/'style-comparison.png')
print(OUT/'style-comparison.png')
