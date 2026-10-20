#!/usr/bin/env python3
"""Index every saved irrigation study without rebuilding or replacing its assets."""
from pathlib import Path
import argparse
import html
import hashlib
import json
import re
from urllib.parse import quote, unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'output/models/irrigated-farm-native-fit'
BANNER = '<nav id="irrigation-library-link" style="padding:12px 24px;background:#315c5d;color:white;font:14px system-ui"><a href="/index.html" style="color:white">← All irrigated farm assets</a></nav>'
HASH_SCRIPT = '''<script id="irrigation-library-selection">
function selectLibraryAsset(){const key=decodeURIComponent(location.hash.slice(1));if(!key)return;const i=ASSETS.findIndex(a=>a.name===key);if(i>=0){selector.value=String(i);choose(i)}}
selectLibraryAsset();window.addEventListener('hashchange',selectLibraryAsset);
</script>'''


def read(path):
    return json.loads(path.read_text())


def verified_r5_approval(folder):
    """Apply later user approval only to the exact reviewed source exports."""
    record=ROOT/'shared/art/irrigated-farm/v3-civ5-direction/model-approval-r5.json'
    if not record.is_file():return None
    approval=read(record)
    if approval.get('revision')!=5 or approval.get('status')!='source model design approved':return None
    candidates=approval['candidates']
    if {r['name'] for r in candidates}!={r['name'] for r in read(folder/'models.json')['models']}:return None
    expected=[(folder/'RT_IF_Diffuse.png',approval['atlas_sha256'])]
    expected += [(folder/r['name']/(r['name']+'.'+ext),sha) for r in candidates for ext,sha in r['sha256'].items()]
    if any(not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=sha for path,sha in expected):return None
    return approval


def url(prefix, filename=''):
    return '/'+quote('/'.join(s.strip('/') for s in (prefix, filename) if s), safe='/')


def label(name):
    text=name.removeprefix('RT_IF_').replace('Native_','').replace('_',' ')
    for a,b in [('GentleHill','Gentle hill'),('SteepHill','Steep hill'),('RockyFoothill','Rocky foothill'),
                ('MountainIntake','Mountain intake'),('ConnectedDistrict','Connected district'),
                ('DatePalm','Date palm'),('FruitTree','Fruit tree')]:text=text.replace(a,b)
    return text


def mount(destination, source):
    source=source.resolve()
    if not source.is_dir(): raise FileNotFoundError(source)
    if destination.is_symlink():
        if destination.resolve()!=source: raise ValueError('Existing library mount points elsewhere: '+str(destination))
    elif destination.exists(): raise ValueError('Refuse to replace an existing output: '+str(destination))
    else: destination.symlink_to(source, target_is_directory=True)


def viewer(source, destination, prefix):
    """Copy only viewer HTML; original study files and model payloads stay intact."""
    text=source.read_text()
    match=re.search(r'const ASSETS=(.*?);\s*const ATLAS=',text,re.S)
    if not match or 'function choose(' not in text or 'const selector=' not in text:
        raise ValueError('Unsupported saved viewer: '+str(source))
    cards=json.loads(match.group(1))
    text=re.sub(r'<nav id="irrigation-library-link".*?</nav>','',text,flags=re.S)
    text=text.replace('<head>','<head><base href="'+url(prefix)+'/">',1)
    # All saved viewers have the same selector/choose interface. Deep links select
    # actual named buffers already embedded in that original viewer.
    text=text.replace('<body>','<body>'+BANNER,1).replace('</body>',HASH_SCRIPT+'</body>',1)
    destination.write_text(text)
    return {c['name'] for c in cards}


def standard_items(records, folder, prefix, view, names, root_files=False):
    items=[]
    for record in records:
        name=record['name']; files={}
        for ext in ('glb','obj','br2','gr2'):
            relative=name+'.'+ext if root_files and ext in ('glb','gr2') else name+'/'+name+'.'+ext
            if (folder/relative).is_file():files[ext.upper()]=url(prefix,relative)
        items.append({'name':name,'label':label(name),'files':files,
                      'view':view+'#'+quote(name) if name in names else None})
    return items


def build(out, history_root):
    library=out/'library'; assets=library/'assets';assets.mkdir(parents=True,exist_ok=True)
    groups=[]; viewers={}
    def add_view(key, folder, prefix):
        names=viewer(folder/'index.html',library/(key+'.html'),prefix)
        path=url('library',key+'.html');viewers[path]=sorted(names)
        return path,names
    def group(key,title,status,description,items,image=None,view=None,review=None):
        groups.append(dict(key=key,title=title,status=status,description=description,items=items,image=image,view=view,review=review))

    revision=out/'concept-models-r2'
    revised=(revision/'revision-validation.json').is_file()
    if revised:
        av,an=add_view('concept-r2',revision,'concept-models-r2')
        group('concept-r2','Revised canals, terrace walls & aqueducts','Revision 2 · unapproved models',
              'Long plot-aligned canals, three broad terrace benches and continuous walls. Shallow aqueducts ease into separate receiving chutes. Editable offline meshes only; native conversion and game integration remain on hold.',
              standard_items(read(revision/'models.json')['models'],revision,'concept-models-r2',av,an),
              url('concept-models-r2','connected-district-preview.png'),av,url('concept-models-r2','review.html'))
        # Keep the user's open review URL useful, preserving the previous page
        # and all candidate geometry. Relative previews resolve in the revision.
        previous=out/'concept-models/previous-review.html'
        if not previous.exists():previous.write_text(Path(__file__).with_name('concept_model_review.html').read_text())
        current=(revision/'review.html').read_text().replace('<head>','<head><base href="/concept-models-r2/">',1)
        (out/'concept-models/review.html').write_text(current)

    parcels=out/'concept-models-r3'
    if (parcels/'parcel-validation.json').is_file():
        av,an=add_view('concept-r3',parcels,'concept-models-r3')
        group('concept-r3','Straight gentle terraces & channels between plots','Revision 3 · unapproved models',
              'Three staggered straight terraces with a planted upper bench. Flat crop plots and irrigation ditches share exact boundary coordinates. The previous revisions remain available for comparison; native integration stays on hold.',
              standard_items(read(parcels/'models.json')['models'],parcels,'concept-models-r3',av,an),
              url('concept-models-r3','GentleHill-preview.png'),av,url('concept-models-r3','review.html'))
        current=(parcels/'review.html').read_text().replace('<head>','<head><base href="/concept-models-r3/">',1)
        (out/'concept-models/review.html').write_text(current)

    cascades=out/'concept-models-r4'
    if (cascades/'cascade-validation.json').is_file():
        av,an=add_view('concept-r4',cascades,'concept-models-r4')
        group('concept-r4','Angular tiers & cascading irrigation','Revision 4 · unapproved models',
              'All hill forms use straight trapezoidal tiers, fitted crop plots and central stepped cascades through retaining-wall openings. Flat geometry stays at revision 3. Native integration remains on hold.',
              standard_items(read(cascades/'models.json')['models'],cascades,'concept-models-r4',av,an),
              url('concept-models-r4','SteepHill-preview.png'),av,url('concept-models-r4','review.html'))
        current=(cascades/'review.html').read_text().replace('<head>','<head><base href="/concept-models-r4/">',1)
        (out/'concept-models/review.html').write_text(current)

    hillsides=out/'concept-models-r5'
    if (hillsides/'hillside-validation.json').is_file():
        approval=verified_r5_approval(hillsides)
        status='Revision 5 · source design approved' if approval else 'Revision 5 · unapproved models'
        # Approval is presentation metadata; preserve every reviewed mesh byte.
        page=Path(__file__).with_name('concept_hillside_review.html').read_text()
        source_view=(hillsides/'index.html').read_text().replace('Revision 5 · source design approved','Revision 5 · unapproved models').replace('Approved source design. Native conversion and game validation remain pending.','Offline mesh review. Native conversion, game testing and integration remain on hold.')
        if approval:
            (hillsides/'model-approval.json').write_text(json.dumps(approval,indent=2)+'\n')
            page=page.replace('Unapproved models · awaiting your review','Source model design approved · 20 October 2026')
            page=page.replace('The concept and design approach were selected; these new models have not been approved. Further conversion, native testing and integration are on hold.','You approved this R5 source-model design. Native conversion, terrain fit, dynamic placement and in-game validation remain pending.')
            page=page.replace('<a href="hillside-validation.json">Export and water-route checks</a>','<a href="model-approval.json">Recorded model approval</a> · <a href="hillside-validation.json">Export and water-route checks</a>')
            source_view=source_view.replace('Revision 5 · unapproved models',status).replace('Offline mesh review. Native conversion, game testing and integration remain on hold.','Approved source design. Native conversion and game validation remain pending.')
        (hillsides/'review.html').write_text(page)
        (hillsides/'index.html').write_text(source_view)
        av,an=add_view('concept-r5',hillsides,'concept-models-r5')
        group('concept-r5','Unequal hillside terraces & offset water drops',status,
              'Lower angular benches, unequal fitted parcels, finer native masonry and channels closer to the soil. Drops move between parcel boundaries instead of lining up on a central axis. Flat geometry stays at revision 3.',
              standard_items(read(hillsides/'models.json')['models'],hillsides,'concept-models-r5',av,an),
              url('concept-models-r5','GentleHill-preview.png'),av,url('concept-models-r5','review.html'))
        current=(hillsides/'review.html').read_text().replace('<head>','<head><base href="/concept-models-r5/">',1)
        (out/'concept-models/review.html').write_text(current)

    concept=out/'concept-models'
    if (concept/'models.json').is_file():
        av,an=add_view('concept',concept,'concept-models')
        concept_items=standard_items(read(concept/'models.json')['models'],concept,'concept-models',av,an)
        for item in concept_items:
            name=item['name']
            if (concept/name/(name+'.fxsxml')).is_file():
                item['files']['FXSXML']=url('concept-models',name+'/'+name+'.fxsxml')
        group('concept','Previous concept-model candidates' if revised else 'Selected concept → actual models','Unapproved models · retained for comparison' if revised else 'Unapproved models · awaiting your review',
              'These new meshes have not been approved. Review the shapes, materials and irrigation treatment before further conversion, native testing or integration. The collection contains four terrain forms, wet/dry and lower-detail variants, components and a connected district.',
              concept_items,
              url('concept-models','connected-district-preview.png'),av,
              url('concept-models','previous-review.html' if revised else 'review.html'))

    terrain=out/'terrain-review';tv,_=add_view('terrain',terrain,'terrain-review')
    cases=read(terrain/'terrain-cases.json')['cases']; items=[]
    for c in cases:
        for state in ('record','dry_record'):
            r=c[state];name=r['name']
            items.append(dict(name=name,label=c['label']+(' · dry' if state=='dry_record' else ' · wet'),
                              view=tv+'#'+c['key'] if state=='record' else None,
                              files={'GLB overlay':url('terrain-review',name+'.glb'),
                                     'GR2 overlay':url('terrain-review',name+'.gr2')}))
    group('terrain','Terraces, floodplains & transitions','Fitting studies',
          'Seven cases: terraced hill, flat desert, grassland, floodplain, terrace → flat, floodplain → desert, and mountain → terrace. The surrounding terrain and flat parcels are authored diagnostics.',
          items,url('terrain-review','mountain_terrace-preview.png'),tv+'#mountain_terrace')

    regular=out/'regular-farm-review';rv,rn=add_view('regular',regular,'regular-farm-review')
    group('regular','Regular farm buildings','Native candidates',
          'The narrow collection you were viewing: Farm1/2/3 in both eras, wet and dry. Actual buildings and farmstead decals; the game-generated surrounding fields are absent.',
          standard_items(read(regular/'regular-farms.json')['models'],regular,'regular-farm-review',rv,rn,True),
          url('regular-farm-review','medieval_farm1-preview.png'),rv)

    fit=out/'irrigation-fit';fv,_=add_view('first-fit',fit,'irrigation-fit')
    fitted=standard_items(read(fit/'fit-validation.json')['models'],fit,'irrigation-fit',fv,set(),True)
    # First-fit GLBs carry the -native suffix, unlike subsequent candidates.
    for item in fitted:item['files']['GLB overlay']=url('irrigation-fit',item['name']+'-native.glb')
    group('fit','First native terrace fitting','Native source comparison',
          'The original terrace mesh with its fitted upper carrier and aqueduct. Compare source, combined model, and irrigation alone.',
          fitted,url('irrigation-fit','native-fit-preview.png'),fv+'#combined')

    overlay=out.parent/'irrigated-farm-native-overlay';mount(assets/'components',overlay)
    cp='library/assets/components';cv,cn=add_view('components',overlay,cp)
    group('components','Channels, aqueducts & edge pieces','Component kit',
          'Earth and stone channels; wet/dry open joints and closed ends; terrace headers; short, long and mountain aqueducts; mountain intake and lower-detail variants.',
          standard_items(read(overlay/'models.json')['models'],overlay,cp,cv,cn),
          url(cp,'RT_IF_Native_Flat_Stone-preview.png'),cv+'#RT_IF_Aqueduct_Mountain')

    for version in (3,2,1):
        folder=history_root/'output/models'/('irrigated-farm-v'+str(version))
        mount(assets/('v'+str(version)),folder);prefix='library/assets/v'+str(version)
        hv,hn=add_view('v'+str(version),folder,prefix)
        group('v'+str(version),('Selected structural study · v3' if version==3 else 'Earlier mesh study · v'+str(version)),('Selected approach · Civ V refinement required' if version==3 else 'Historical designs'),
              'Complete connected district, four terrain families, wet/dry/construction/pillaged states, channels, aqueducts, palms, fruit trees and lower-detail variants. '+('Selected as the structural approach on 20 October; materials and buildings must follow Civ V and the selected concept.' if version==3 else 'Retained as design history.'),
              standard_items(read(folder/'models.json')['models'],folder,prefix,hv,hn),
              url(prefix,'connected-district-preview.png'),hv+'#RT_IF_ConnectedDistrict')

    art=ROOT/'shared/art/irrigated-farm';mount(assets/'concepts',art);ap='library/assets/concepts'
    concepts=[('Preferred native-art approach','native-overlay-study/native-farm-irrigation-study.png','Selected direction · illustration'),
              ('Flat ground','plot-channel-samples-v1/flat.png','Illustrative plot-channel sample'),
              ('Gentle hill','plot-channel-samples-v1/gentle-hill.png','Illustrative plot-channel sample'),
              ('Steep hill','plot-channel-samples-v1/steep-hill.png','Illustrative plot-channel sample'),
              ('Rocky foothill','plot-channel-samples-v1/rocky-foothill.png','Illustrative plot-channel sample'),
              ('Earlier v6 adjacency concept','irrigated-farm-adjacency-v6.png','Earlier approved concept · retained history')]
    sheets=[dict(title=t,image=url(ap,f),status=s) for t,f,s in concepts]
    native=[]
    for r in read(out/'native-import.json')['models']:
        name=r['name'];native.append(dict(name=name,label=label(name),view=None,
            files={'Source GLB':url(r['glb']),'Source GR2':url(name,name+'-uncompressed.gr2')}))
    group('sources','Original Civ V source imports','Local reference assets',
          'Eleven imported source files, including the regular Farm variants and Terrace Farm construction states. The two unsuffixed Farm references are the earlier wheat-resource props.',native)
    groups.sort(key=lambda g: {'concept-r5':0,'concept-r4':1,'concept-r3':2,'concept-r2':3,'concept':4,'v3':5}.get(g['key'],6))
    data={'groups':groups,'concepts':sheets,'viewer_models':viewers,
          'native_game_acceptance':False,'scope':'Saved irrigation work; revisions and states are separate entries, not unique completed game assets.'}
    (library/'catalog.json').write_text(json.dumps(data,indent=2)+'\n')
    render(out,data)
    # Add a prominent way out of the old narrow entry point. The source generator
    # also emits this link, so later regular-farm builds keep it.
    old=regular/'index.html';text=old.read_text()
    if 'id="irrigation-library-link"' not in text:old.write_text(text.replace('<body>','<body>'+BANNER,1))
    return data


def esc(text):return html.escape(text,quote=True)


def render(out,data):
    sections=[]
    for g in data['groups']:
        entries=[]
        for item in g['items']:
            actions=[]
            if item['view']: actions.append('<a href="'+esc(item['view'])+'">View in 3D</a>')
            actions += ['<a href="'+esc(v)+'" download>'+esc(k)+'</a>' for k,v in item['files'].items()]
            entries.append('<li><span>'+esc(item['label'])+'</span><span class="formats">'+' '.join(actions)+'</span></li>')
        thumbnail=('<a class="preview" href="'+esc(g['view'])+'"><img loading="lazy" src="'+esc(g['image'])+'" alt="'+esc(g['title'])+' saved mesh preview"></a>') if g['image'] else ''
        button='<a class="open" href="'+esc(g['view'])+'">Open 3D collection ↗</a>' if g['view'] else ''
        if g.get('review'):button += '<p><a href="'+esc(g['review'])+'">Close-up, map-scale &amp; source comparisons ↗</a></p>'
        sections.append('<section class="collection" id="'+g['key']+'">'+thumbnail+'<div class="description"><p class="status">'+esc(g['status'])+'</p><h2>'+esc(g['title'])+'</h2><p>'+esc(g['description'])+'</p>'+button+'<details><summary>Browse all '+str(len(g['items']))+' saved exports</summary><ul class="inventory">'+''.join(entries)+'</ul></details></div></section>')
    sheets=''.join('<figure><a href="'+esc(s['image'])+'"><img loading="lazy" src="'+esc(s['image'])+'" alt="'+esc(s['title'])+'"></a><figcaption><strong>'+esc(s['title'])+'</strong><span>'+esc(s['status'])+'</span></figcaption></figure>' for s in data['concepts'])
    template=(Path(__file__).with_name('review_library.html')).read_text()
    (out/'index.html').write_text(template.replace('__COLLECTIONS__','\n'.join(sections)).replace('__CONCEPTS__',sheets))


def validate(out,data):
    links=[]
    for group in data['groups']:
        if group.get('review'):links.append(group['review'])
        if group['image']:links.append(group['image'])
        if group['view']:links.append(group['view'])
        for item in group['items']:
            if not item['files']:raise ValueError('No exports found: '+item['name'])
            links.extend(item['files'].values())
            if item['view']:links.append(item['view'])
    links.extend(c['image'] for c in data['concepts'])
    for link in links:
        parsed=urlsplit(link);path=out/unquote(parsed.path.lstrip('/'))
        if not path.is_file():raise FileNotFoundError(path)
        if parsed.fragment and unquote(parsed.fragment) not in data['viewer_models'].get(parsed.path,[]):
            raise ValueError('Viewer lacks linked model: '+link)
    report={'collections':len(data['groups']),'exports':sum(len(g['items']) for g in data['groups']),
            'concept_sheets':len(data['concepts']),'checked_links':len(links),
            'mesh_files_changed':False,'browser_visual_verification':False,
            'group_counts':{g['key']:len(g['items']) for g in data['groups']}}
    (out/'library/validation.json').write_text(json.dumps(report,indent=2)+'\n')
    return report


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=OUT)
    parser.add_argument('--history-root',type=Path,default=ROOT,help='Checkout containing the earlier v1-v3 output folders')
    args=parser.parse_args();out=args.output.resolve()
    print(json.dumps(validate(out,build(out,args.history_root.resolve())),indent=2))
