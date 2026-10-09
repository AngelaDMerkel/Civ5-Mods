"""Original painted-detail atlas; no game pixels are used in these materials."""
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFilter


def make_atlas(folder):
    from irrigation_mesh_io import MATERIALS, CELL, GRID, GUTTER
    atlas = Image.new('RGB', (CELL*GRID, CELL*GRID))
    rng = np.random.default_rng(20261009)
    def tint(c, f): return tuple(int(np.clip(v*f,0,255)) for v in c)
    for index,(name,color) in enumerate(MATERIALS.items()):
        coarse = Image.fromarray(rng.integers(35,210,(30,30),dtype=np.uint8)).resize((CELL,CELL),Image.Resampling.BICUBIC)
        noise = (np.asarray(coarse,dtype=float)-125)*.13 + rng.normal(0,3,(CELL,CELL))
        base = np.asarray(color)[None,None,:]+noise[:,:,None]
        tile = Image.fromarray(np.uint8(np.clip(base,0,255)));d=ImageDraw.Draw(tile)
        if name in ('barley','vegetables','legumes','stubble','dry_crop'):
            # Each material is a complete small parcel. Fine irregular growth,
            # soft earth borders, furrow occlusion and broken harvest patches.
            soil=(126,109,76); field=Image.new('RGB',(CELL,CELL),soil)
            field.putdata([tuple(p) for p in np.uint8(np.clip(np.array(soil)+noise[:,:,None],0,255)).reshape(-1,3)])
            d=ImageDraw.Draw(field)
            if name!='stubble':
                # Continuous leaf/stem litter under the crowns: native farm parcels
                # read as planted surfaces, not isolated sprouts on bare sand.
                fill=np.uint8(np.clip(np.array(color)*.88+noise[:,:,None]*1.5,0,255))
                interior=Image.fromarray(fill).crop((27,24,CELL-27,CELL-24))
                field.paste(interior,(27,24));d=ImageDraw.Draw(field)
            count=13 if name in ('barley','dry_crop','stubble') else 10
            spacing=(CELL-64)/count
            for row in range(count):
                x=32+row*spacing
                d.line((x+3,24,x+3,CELL-24),fill=(78,75,48),width=5)
                for j in range(150 if name in ('barley','dry_crop','stubble') else 53):
                    y=26+j*(CELL-55)/(150 if name in ('barley','dry_crop','stubble') else 53)+rng.uniform(-3,3)
                    # Sparse failures keep rows from reading as computer stripes.
                    if rng.random()<(.19 if name=='stubble' else .05):continue
                    xx=x+rng.normal(0,2.3)
                    col=tint(color,rng.uniform(.66,1.30))
                    if name in ('barley','dry_crop','stubble'):
                        length=rng.uniform(3,10) if name!='stubble' else rng.uniform(2,5)
                        d.line((xx-5,y+2,xx-2,y-length),fill=col,width=2)
                        d.line((xx-1,y+2,xx+3,y-length*.65),fill=tint(col,1.10),width=2)
                    else:
                        r=rng.uniform(7,12)
                        d.ellipse((xx-r,y-r/2,xx+r,y+r/2),fill=col)
                        d.line((xx-r/2,y,xx+1,y-r/2),fill=tint(col,1.20),width=2)
            # Broken footpaths and straw debris at parcel borders.
            for j in range(550):
                x,y=rng.uniform(15,CELL-15,2)
                if 26<x<CELL-28 and 26<y<CELL-26 and rng.random()<.95:continue
                d.line((x,y,x+rng.uniform(1,5),y+rng.uniform(-3,3)),fill=tint(soil,rng.uniform(.8,1.22)),width=1)
            tile=field
        elif name in ('stone','coping'):
            # Low, uneven sandstone courses; the mesh tiles this at physical scale.
            for row,y in enumerate(range(-8,CELL,48)):
                offset=-(row%2)*45
                for x in range(offset,CELL,90):
                    xx=x+rng.integers(-6,7); yy=y+rng.integers(-3,4)
                    c=tint(color,rng.uniform(.87,1.08))
                    d.rounded_rectangle((xx+2,yy+2,xx+87,yy+46),radius=3,fill=tint(c,.73))
                    d.polygon([(xx+5,yy+4),(xx+83,yy+3),(xx+85,yy+40),(xx+4,yy+42)],fill=c)
                    d.line((xx+6,yy+5,xx+80,yy+5),fill=tint(c,1.1),width=2)
                    for k in range(10):
                        a,b=xx+rng.uniform(7,78),yy+rng.uniform(7,38)
                        d.line((a,b,a+3,b+1),fill=tint(c,rng.uniform(.75,1.1)))
        elif name in ('leaves','leaf_light'):
            # Mottled leaf clusters, with deep inter-leaf shadows rather than stripes.
            for i in range(3200):
                x,y=rng.uniform(0,CELL,2); r=rng.uniform(2,8)
                col=tint(color,rng.uniform(.54,1.38))
                d.ellipse((x-r,y-r*.6,x+r,y+r*.6),fill=col)
                if i%3==0:d.line((x-r*.4,y,x+r*.4,y-r*.2),fill=tint(col,1.12))
        elif name=='wood':
            for y in range(0,CELL,18):
                d.line((0,y,CELL,y+3),fill=tint(color,.65),width=3)
                for x in range(0,CELL,32):d.line((x,y,x+12,y-8),fill=tint(color,1.17),width=2)
        elif name=='plaster':
            for i in range(600):
                x,y=rng.uniform(0,CELL,2);r=rng.uniform(1,7)
                d.ellipse((x,y,x+r,y+r*.55),fill=tint(color,rng.uniform(.79,1.07)))
            for i in range(14):
                x,y=rng.uniform(0,CELL,2)
                d.line((x,y,x+6,y+12,x+3,y+23),fill=tint(color,.78),width=1)
        elif name=='water':
            for i in range(220):
                x,y=rng.uniform(0,CELL,2)
                d.line((x,y,x+rng.uniform(6,35),y+1),fill=tint(color,rng.uniform(.88,1.19)),width=1)
        else:
            for i in range(1800):
                x,y=rng.uniform(0,CELL,2);r=rng.uniform(.6,3)
                d.ellipse((x,y,x+r,y+r*.6),fill=tint(color,rng.uniform(.74,1.18)))
        # Gutter extrusion protects boundaries under bilinear sampling.
        inner=tile.crop((GUTTER,GUTTER,CELL-GUTTER,CELL-GUTTER))
        for x,sx in [(0,0),(CELL-GUTTER,inner.width-1)]:
            tile.paste(inner.crop((sx,0,sx+1,inner.height)).resize((GUTTER,inner.height)),(x,GUTTER))
        for y,sy in [(0,GUTTER),(CELL-GUTTER,CELL-GUTTER-1)]:
            tile.paste(tile.crop((0,sy,CELL,sy+1)).resize((CELL,GUTTER)),(0,y))
        atlas.paste(tile,((index%GRID)*CELL,(index//GRID)*CELL))
    atlas.save(folder/'RT_IF_Diffuse.png');atlas.convert('RGBA').save(folder/'RT_IF_Diffuse.dds')
    Image.new('RGBA',(4,4),(128,128,255,255)).save(folder/'RT_IF_FlatNormal.dds')
    Image.new('RGBA',(4,4),(0,0,0,255)).save(folder/'RT_IF_BlackSpec.dds')
    return atlas
