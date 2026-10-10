#!/usr/bin/env python3
"""Validate local regular-farm candidates without claiming native rendering."""
from pathlib import Path
import argparse
import copy
import json
import struct
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
from native_gr2 import Reader
from native_scene import parts, world_arrays, regular_farm_states
from import_native_farms import OUT, semantic, digest
from validate_native_import import glb
from build_regular_farms import building, constructed, ART, DIFF, SREF
from irrigation_mesh_io import read_glb


def validate(out):
    folder=out/'regular-farm-review'; manifest=json.loads((folder/'regular-farms.json').read_text())
    source_manifest=json.loads((out/'native-import.json').read_text())
    for item in source_manifest['extracted_assets']:
        assert digest(out/'native-local'/Path(item['entry']).name)==item['sha256']
    assert len(manifest['models'])==12
    results=[]
    for record in manifest['models']:
        name=record['name']; source_name=record['source']
        source=Reader(out/source_name/(source_name+'-uncompressed.gr2')).root()
        actual=Reader(folder/(name+'.gr2')).root()
        assert digest(folder/(name+'.gr2'))==record['candidate_sha256']
        assert regular_farm_states(source)==regular_farm_states(actual)==record['construction_states']
        _,base=building(source);_,candidate=building(actual)
        count=len(base['PrimaryVertexData']['Vertices']); count_ix=len(base['PrimaryTopology']['Indices16'])
        assert len(candidate['PrimaryVertexData']['Vertices'])==count+record['triangles']*3
        # Remove only the appended material group. Every original graph field,
        # including HB/PL, stencil, bones, shader parameters and UVs, must match.
        restored=copy.deepcopy(actual);_,mesh=building(restored)
        mesh['PrimaryVertexData']['Vertices']=mesh['PrimaryVertexData']['Vertices'][:count]
        mesh['PrimaryTopology']['Indices16']=mesh['PrimaryTopology']['Indices16'][:count_ix]
        mesh['PrimaryTopology']['Groups']=mesh['PrimaryTopology']['Groups'][:-1]
        mesh['MaterialBindings']=mesh['MaterialBindings'][:-1]
        restored['Materials']=restored['Materials'][:-1]
        assert semantic(restored)==semantic(source), (name,'stock graph changed')
        scene=parts(constructed(actual)); doc,acc=glb(folder/(name+'.glb'))
        for part,gltf,node in zip(scene,doc['meshes'],doc['nodes']):
            np.testing.assert_allclose(np.array(node['matrix']).reshape(4,4).T,part['transform'],atol=1e-7)
            for group,primitive in zip(part['groups'],gltf['primitives']):
                attrs=primitive['attributes']
                for gl,src in [('POSITION','Position'),('NORMAL','Normal'),('_CIV5_TEXCOORD0','TextureCoordinates0')]:
                    np.testing.assert_array_equal(acc(attrs[gl]),part['arrays'][src])
                np.testing.assert_array_equal(acc(primitive['indices']),part['indices'][group['TriFirst']*3:(group['TriFirst']+group['TriCount'])*3])
        part=next(p for p in scene if p['name']==candidate['Name']); positions,normals=world_arrays(part)
        positions=positions[count:];normals=normals[count:]
        _,(overlay_p,overlay_n,overlay_uv),_=read_glb(folder/name/(name+'.glb'))
        np.testing.assert_allclose(positions,overlay_p,atol=2e-6)
        np.testing.assert_allclose(normals,overlay_n,atol=2e-6)
        np.testing.assert_allclose(part['arrays']['TextureCoordinates0'][count:,:2],overlay_uv,atol=1e-7)
        assert np.isfinite(positions).all()
        np.testing.assert_allclose(np.linalg.norm(normals,axis=1),1,atol=1e-6)
        triangles=positions.reshape(-1,3,3)
        assert np.linalg.norm(np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]),axis=1).min()>1e-9
        routes={r['name']:r for r in record['routes']}
        assert len(routes)==2
        main=np.array(routes['regular_carrier']['points']);branch=np.array(routes['regular_branch']['points'])
        assert routes['regular_branch']['upstream']=='regular_carrier'
        assert np.linalg.norm(main-branch[0],axis=1).min()<1e-7
        np.testing.assert_allclose(record['source_socket'],main[0])
        assert record['source_socket_connected'] is False
        for r in routes.values():
            assert np.diff(np.array(r['points'])[:,2]).max()<=1e-7
            assert r['end']=='closed_field_outlet'
            assert any(g['name']==r['name']+'_terminal' for g in record['groups'])
        water=[g for g in record['groups'] if g['name'].endswith('_water')]
        assert bool(water)==record['wet']
        # Clearance is to actual building geometry in the undeformed source;
        # crops and game terrain are intentionally not invented for this check.
        basepart=next(p for p in parts(constructed(source)) if p['name']==base['Name'])
        bp,_=world_arrays(basepart);lo,hi=bp[:,:2].min(0),bp[:,:2].max(0)
        for g in record['groups']:
            samples=positions[g['first']:g['first']+g['count'],:2]
            assert not ((samples>=lo-.3)&(samples<=hi+.3)).all(axis=1).any(), (name,'building collision')
        wrapper=ET.parse(folder/(name+'.fxsxml')).getroot()
        assert wrapper.find('Mesh').attrib['file']==name+'.gr2'
        stock=ET.parse(out/'native-local'/(source_name+'.fxsxml')).getroot()
        expected=[t.attrib for t in stock.findall('Texture')]
        assert [t.attrib for t in wrapper.findall('Texture')[:-2]]==expected
        assert [t.attrib['file'] for t in wrapper.findall('Texture')[-2:]]==[DIFF,SREF]
        results.append({'name':name,'irrigation_triangles':record['triangles'],'stock_graph_retained':True,
                        'gr2_glb_overlay_parity':True,'building_clearance':True,'descending_routes_and_closed_outlets':True})
    rows=ET.parse(folder/'RT_IF_RegularCandidate.xml').findall('ArtDefine_Landmarks/Row')
    assert len(rows)==6
    assert {r.findtext('Era') for r in rows}=={'Ancient','Industrial'}
    for row in rows:
        assert row.findtext('ImprovementType')==ART
        assert row.findtext('LayoutHandler')=='FARM'
        assert row.findtext('TerrainContour')=='1'
        assert row.findtext('State')=='Any'
        assert row.findtext('Scale')=='1.0'
        assert row.findtext('ResourceType')=='ART_DEF_RESOURCE_NONE'
        assert (folder/row.findtext('Model')).is_file()
    for name,size in [(DIFF,2048),(SREF,64)]:
        raw=(folder/name).read_bytes()
        assert raw[:4]==b'DDS ' and raw[84:88]==b'DXT1'
        assert Image.open(folder/name).size==(size,size)
        assert struct.unpack_from('<I',raw,28)[0]==int(np.log2(size))+1
    assert not (folder/'farm_types.xml').exists()
    assert not list(folder.glob('crops_*.dds'))
    return {'models':results,'stock_crop_overrides':False,'stock_farm_layout_bindings':True,
            'native_engine_test':False,'crop_parcel_fit_verified':False,'runtime_source_connection':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=OUT)
    args=parser.parse_args();result=validate(args.output.resolve())
    (args.output/'regular-farm-review/validation.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
