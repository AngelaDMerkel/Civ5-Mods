"""Annotate actual exported centerlines on the actual exported GLB render."""
from pathlib import Path
import argparse,json,math
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from irrigation_mesh_io import read_glb,render_glb,unit

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1] if HERE.name=='irrigation_v3' else HERE.parent
parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'output/models/irrigated-farm-v3')
out=parser.parse_args().output.resolve();name='RT_IF_ConnectedDistrict';path=out/name/(name+'.glb')
record=json.loads((out/name/(name+'.json')).read_text());_,(p,_,_),_=read_glb(path)
width,height=1600,1120;azimuth,elevation=-74,47
im=render_glb(path,width,height,azimuth=azimuth,elevation=elevation)
d=ImageDraw.Draw(im);a,e=math.radians(azimuth),math.radians(elevation)
camera=unit((math.cos(a)*math.cos(e),math.sin(a)*math.cos(e),math.sin(e)))
right=unit(np.cross((0,0,1),camera));up=unit(np.cross(camera,right));center=(p.min(axis=0)+p.max(axis=0))/2
pp=np.stack(((p-center)@right,(p-center)@up),axis=1);span=np.ptp(pp,axis=0)
scale=min((width*1.25-80)/span[0],(height*1.25-90)/span[1])*.94/1.25
def project(point):
    q=np.asarray(point)-center
    return np.array((width/2+q@right*scale,height/2-q@up*scale))
for route in record['routes']:
    points=np.array(route['points']);xy=np.array([project(v) for v in points])
    color=(38,141,167) if 'field' in route['name'] or '_bed_' in route['name'] else (39,199,215)
    d.line([tuple(v) for v in xy],fill=(24,62,64),width=4)
    d.line([tuple(v) for v in xy],fill=color,width=2)
    # One arrow per run (at least one per short branch); every arrow follows
    # the validated ordering from source toward receiving bed.
    for j,(v,w) in enumerate(zip(xy,xy[1:])):
        delta=w-v;length=np.linalg.norm(delta)
        if length<13 or (len(points)>7 and j%3):continue
        u=delta/length;side=np.array((-u[1],u[0]));q=v+delta*.65
        d.polygon([tuple(q+u*5),tuple(q-u*4+side*3),tuple(q-u*4-side*3)],fill=(247,231,162))
source=project(record['source']);d.ellipse((* (source-[7,7]),*(source+[7,7])),fill=(247,231,162),outline=(36,72,68),width=2)
try:
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',24)
    small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',17)
except OSError:font=small=ImageFont.load_default()
plot=im
im=Image.new('RGB',(width,height+132),(232,226,210));im.paste(plot,(0,92));d=ImageDraw.Draw(im)
d.text((24,15),'GRAVITY-FED DISTRIBUTION / EXPORTED WATER ROUTES',font=font,fill=(44,59,47))
d.text((24,52),'Intake → descending supply → level contour channels → bed branches. Arrows are a diagnostic overlay.',font=small,fill=(70,77,63))
d.text((24,height+99),f'{len(record["routes"])} connected runs · one source · no rising waterline · source-mesh review, not a Civ V screenshot',font=small,fill=(44,59,47))
im.save(out/'water-flow-review.png');print(out/'water-flow-review.png')
