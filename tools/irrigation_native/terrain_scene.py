"""Authored terrain fixtures using unchanged native Civ V textures and farm props.

These fixtures exercise irrigation mesh fitting; they do not reproduce the
closed-source game's terrain compositor or procedural crop-parcel placement.
"""
import math
import struct
import numpy as np

A = 30.
R = A / math.cos(math.pi/6)
ROCK_CENTER = (A, 1.5*R)
HEX = np.array([(R*math.cos(a), R*math.sin(a)) for a in np.arange(6)*math.pi/3+math.pi/6])


def material(texture, opaque=True):
    return {'Name': texture, '_previewAlphaMode': 'OPAQUE' if opaque else 'MASK',
            'Maps': [{'Usage': 'Diffuse', 'Map': {'Texture': {'FromFileName': texture}}}],
            'ExtendedData': {'ShaderSet': 'native texture on authored review terrain'}}


def piece(name, triangles, uv, texture, opaque=True):
    p = np.asarray(triangles, dtype='<f4').reshape(-1, 3, 3)
    normal = np.cross(p[:, 1]-p[:, 0], p[:, 2]-p[:, 0])
    normal /= np.linalg.norm(normal, axis=1)[:, None]
    n = np.repeat(normal, 3, axis=0)
    tangent = np.tile([1., 0., 0.], (len(n), 1))
    tangent -= n*np.sum(n*tangent, axis=1)[:, None]
    bad = np.linalg.norm(tangent, axis=1) < .01
    tangent[bad] = [0, 1, 0]
    tangent /= np.linalg.norm(tangent, axis=1)[:, None]
    uv = np.asarray(uv).reshape(-1, 2)
    return {'name': name, 'arrays': {'Position': p.reshape(-1, 3), 'Normal': n.astype('<f4'),
            'Tangent': tangent.astype('<f4'), 'Binormal': np.cross(n, tangent).astype('<f4'),
            'TextureCoordinates0': np.column_stack((uv, np.zeros(len(uv)))).astype('<f4')},
            'indices': np.arange(len(n), dtype=np.uint32), 'transform': np.eye(4),
            'groups': [{'MaterialIndex': 0, 'TriFirst': 0, 'TriCount': len(p)}],
            'materials': [material(texture, opaque)]}


def ground(name, height, texture='afri_desert_d.dds', center=(0, 0), subdivisions=13):
    triangles, tex = [], []
    for a, b in zip(HEX, np.roll(HEX, -1, axis=0)):
        def point(i, j):
            xy = (a*i+b*j)/subdivisions+center
            return [*xy, height(*xy)]
        for i in range(subdivisions):
            for j in range(subdivisions-i):
                cells = [[point(i, j), point(i+1, j), point(i, j+1)]]
                if i+j < subdivisions-1:
                    cells.append([point(i+1, j), point(i+1, j+1), point(i, j+1)])
                for tri in cells:
                    triangles.append(tri)
                    tex.append([[(v[0]-center[0]+R)/(2*R), (v[1]-center[1]+R)/(2*R)] for v in tri])
    result = piece(name, triangles, tex, texture)
    # Smooth shading belongs only to this authored terrain, never the stock farm.
    positions = result['arrays']['Position']; eps = .12
    normals = np.array([[-(height(x+eps,y)-height(x-eps,y))/(2*eps),
                         -(height(x,y+eps)-height(x,y-eps))/(2*eps), 1.]
                        for x,y,z in positions])
    normals /= np.linalg.norm(normals,axis=1)[:,None]
    tangent = np.tile([1.,0.,0.],(len(normals),1))
    tangent -= normals*np.sum(normals*tangent,axis=1)[:,None]
    tangent /= np.linalg.norm(tangent,axis=1)[:,None]
    result['arrays'].update(Normal=normals.astype('<f4'), Tangent=tangent.astype('<f4'),
                            Binormal=np.cross(normals,tangent).astype('<f4'))
    return result


def translated(scene, offset, prefix=''):
    out = []
    for part in scene:
        q = dict(part, transform=part['transform'].copy(), name=prefix+part['name'])
        q['transform'][:3, 3] += np.asarray(offset)
        out.append(q)
    return out


def crops(center=(0, 0)):
    # Gaps follow the deliberately authored carrier/branch paths. Native crop
    # pixels stay unchanged. No claim of capturing Civ V's engine parcel layout.
    plots = [
        ([(-26, 7), (-11, 7.5), (-10.5, 26), (-18, 26)], 1),
        ([(-9, 7.5), (4.2, 8), (3.5, 30), (-6, 29)], 4),
        ([(7, 8), (25, 7), (24, 17), (9, 29)], 2),
        ([(-27, 2.5), (1.5, 3), (-2, -10), (-24, -13)], 3),
        ([(-23, -15), (-2, -13), (-1.5, -28), (-10, -26)], 5),
        ([(7.3, 3.5), (24, 2), (23, -16), (3.5, -11)], 4),
        ([(2.5, -14), (22, -18), (10, -29), (3, -28)], 6)]
    out = []
    for i, (polygon, variant) in enumerate(plots):
        p = np.array(polygon, dtype=float)
        if np.cross(p[1]-p[0], p[2]-p[0]) < 0:
            p = p[::-1]
        triangles, uv = [], []
        for ix in ((0, 1, 2), (0, 2, 3)):
            triangles.append([[*(p[j]+center), .025] for j in ix])
            uv.append([[(p[j, 0]-p[:, 0].min())/np.ptp(p[:, 0]),
                        (p[j, 1]-p[:, 1].min())/np.ptp(p[:, 1])] for j in ix])
        out.append(piece('authored_crop_parcel_'+str(i), triangles, uv, f'crops_africa_{variant:02d}_d.dds'))
    return out


def ribbon(name, points, half_width, texture, opaque=True):
    points = np.asarray(points); triangles, uv = [], []
    delta = np.diff(points[:,:2],axis=0)
    normals = np.column_stack((-delta[:,1],delta[:,0],np.zeros(len(delta))))
    normals /= np.linalg.norm(normals,axis=1)[:,None]
    sides = [normals[0]]
    for a,b in zip(normals,normals[1:]):
        side = (a+b)/np.linalg.norm(a+b)
        sides.append(side/max(.65,np.dot(side,b)))
    sides.append(normals[-1])
    for i, (a, b) in enumerate(zip(points, points[1:])):
        sa,sb = sides[i:i+2]
        corners = [a-sa*half_width, b-sb*half_width, b+sb*half_width, a+sa*half_width]
        coords = [[i/(len(points)-1), 0], [(i+1)/(len(points)-1), 0],
                  [(i+1)/(len(points)-1), 1], [i/(len(points)-1), 1]]
        for ids in ((0, 1, 2), (0, 2, 3)):
            triangles.append([corners[j] for j in ids]); uv.append([coords[j] for j in ids])
    return piece(name, triangles, uv, texture, opaque)


def floodplain():
    # A cropped river-edge fixture. Endpoints continue beyond the review tile.
    y = np.linspace(-17, 17, 40)
    x = 27.4+1.6*np.sin((y-5)/10)
    water = np.column_stack((x, y, np.full(len(y), .44)))
    bank = water.copy(); bank[:, 0] -= 3.1; bank[:, 2] = .04
    return [ribbon('native_floodplain_bank_decal', bank, 3.8, 'floodplains_d.dds', False),
            ribbon('native_river_source', water, 2.65, 'river_diffuse.dds')]


def hill_height(surface, x, y):
    # A continuous, low shoulder buries part of the native wall skirts without
    # clipping it to each individual farm triangle (which creates jagged cuts).
    # The supplied native surface remains the authority for irrigation fitting.
    r = math.hypot(x, y)
    return 12. * max(0., math.cos(math.pi*min(r, 30.)/60))**.65 if r < 30 else 0.


_ROCK = None


def load_rock_height(path):
    """Read the native grayscale A16B16G16R16 mountain height field.

    The fixture normalizes its vertical range to 24 authoring units. Native
    height samples are preserved; the game's compositor scale is not claimed.
    """
    global _ROCK
    raw = path.read_bytes()
    h,w = struct.unpack_from('<II',raw,12)
    if raw[:4] != b'DDS ' or struct.unpack_from('<I',raw,84)[0] != 36:
        raise ValueError('Expected native 16-bit RGBA mountain height DDS')
    data = np.frombuffer(raw,dtype='<u2',count=w*h*4,offset=128).reshape(h,w,4)
    if not np.array_equal(data[:,:,0],data[:,:,1]):
        raise ValueError('Expected grayscale height channels')
    heights = data[:,:,0].astype(float)
    _ROCK = (heights-heights.min())/np.ptp(heights)


def rock_height(x,y):
    if _ROCK is None:
        raise ValueError('Load the native mountain heightmap before building this fixture')
    u,v = (x-ROCK_CENTER[0])/60+.5, .5-(y-ROCK_CENTER[1])/60
    if not (0 <= u <= 1 and 0 <= v <= 1):return 0.
    xx,yy = u*(_ROCK.shape[1]-1),v*(_ROCK.shape[0]-1)
    x0,y0 = int(xx),int(yy);x1=min(x0+1,_ROCK.shape[1]-1);y1=min(y0+1,_ROCK.shape[0]-1)
    fx,fy = xx-x0,yy-y0
    return float(24*((1-fx)*(1-fy)*_ROCK[y0,x0]+fx*(1-fy)*_ROCK[y0,x1]+(1-fx)*fy*_ROCK[y1,x0]+fx*fy*_ROCK[y1,x1]))
