"""Download the outcome-independent processed-data pilot, retaining provenance."""
from pathlib import Path
import urllib.request,json,hashlib,os
R=Path(__file__).resolve().parent
D=Path(os.environ.get('LANDSAT_DATA_DIR',str(R.parent.parent/'data/landsat')));D.mkdir(exist_ok=True,parents=True)
selection=json.loads((R/'evidence/landsat8-selection.json').read_text());records=[]
for item in selection['selected']:
    path=D/item['filename'];url=f"https://dataverse.csuc.cat/api/access/datafile/{item['id']}"
    if not path.exists():
        temporary=path.with_suffix('.download')
        with urllib.request.urlopen(url,timeout=60) as source,temporary.open('wb') as target:
            typ=source.headers.get('Content-Type','');first=source.read(65536)
            if b'<html' in first[:500].lower() or b'not a bot' in first[:1000]:raise RuntimeError('Download challenge returned; do not bypass it.')
            target.write(first)
            while block:=source.read(2**20):target.write(block)
        assert temporary.stat().st_size==7*4096*4096*2,'Size mismatch: preserve download and investigate'
        temporary.replace(path)
    md5=hashlib.md5();sha=hashlib.sha256()
    with path.open('rb') as stream:
        while block:=stream.read(2**20):md5.update(block);sha.update(block)
    record=dict(item,url=url,bytes=path.stat().st_size,md5=md5.hexdigest(),sha256=sha.hexdigest(),processing='L1-calibrated, not raw focal-plane',storage='u16 little-endian BSQ',full_bands=7)
    records.append(record);(R/'evidence/landsat8-downloads.json').write_text(json.dumps(records,indent=2)+'\n')
    print(json.dumps(record),flush=True)
