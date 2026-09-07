"""Validate source manifest and the exact scripts shipped by the release workflow."""
import hashlib,json,sys,zipfile
import xml.etree.ElementTree as ET
from pathlib import Path
root=Path(__file__).resolve().parent.parent
cfg=json.loads((root/'.release/release.json').read_text())
mod=ET.parse(root/'modDesc.xml').getroot()
assert mod.findtext('version')==cfg['version']
for node in mod.findall('./extraSourceFiles/sourceFile'):
    assert (root/node.attrib['filename']).is_file(), node.attrib
for path in root.rglob('*.xml'):
    if '.git' not in path.parts: ET.parse(path)
required=['Scripts/C330Runtime.lua','Scripts/C330ExhaustBridge.lua','Scripts/C330TransmissionFix.lua','Scripts/C330TransmissionWorkFix.lua']
if cfg['prerelease']:required.append('Scripts/C330FullDiagnostic.lua')
if '--source-only' not in sys.argv:
    with zipfile.ZipFile(sys.argv[1]) as z:
        assert z.testzip() is None
        assert ET.fromstring(z.read('modDesc.xml')).findtext('version')==cfg['version']
        for name in required:assert z.read(name)==(root/name).read_bytes(),name
        for name in z.namelist():
            assert not any(name.startswith(prefix) for prefix in ['.git/','.github/','.release/','tests/','docs/','debug/','spostrzezenia/']),name
    print('ZIP verified:',hashlib.sha256(Path(sys.argv[1]).read_bytes()).hexdigest())
print('Manifest, XML and package checks passed.')
