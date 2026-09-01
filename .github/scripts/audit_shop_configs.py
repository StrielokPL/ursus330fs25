from pathlib import Path
import xml.etree.ElementTree as ET

p=Path('c330m.xml')
root=ET.parse(p).getroot()

def walk_mass(e):
    vals=[]
    for x in e.iter():
        if 'massActive' in x.attrib:
            vals.append(x.attrib['massActive'])
    return vals

print('=== TOP LEVEL ORDER / CONFIG AUDIT ===')
for i, child in enumerate(list(root)):
    tag=child.tag
    if tag == 'configurationSets':
        print(f'{i:03d} configurationSets title={child.attrib.get("title")} options={len(list(child))}')
        continue
    if tag.endswith('Configurations'):
        options=[c for c in list(child) if c.tag.endswith('Configuration')]
        print(f'{i:03d} {tag} title={child.attrib.get("title")} options={len(options)}')
        for j,c in enumerate(options,1):
            masses=walk_mass(c)
            print(f'    {j:02d} name={c.attrib.get("name")} price={c.attrib.get("price","0")} saveId={c.attrib.get("saveId")} massActive={",".join(masses) if masses else "-"}')

print('=== ALL MASSACTIVE PATHS ===')
def rec(e,path):
    for idx,c in enumerate(list(e)):
        cp=f'{path}/{c.tag}[{idx}]'
        if 'massActive' in c.attrib:
            print(cp, 'massActive='+c.attrib['massActive'])
        rec(c,cp)
rec(root,root.tag)
