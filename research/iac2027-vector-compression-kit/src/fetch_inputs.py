"""Optional regeneration inputs. Supplied fixtures suffice for board testing."""
from pathlib import Path
import json,urllib.request,hashlib,subprocess
P=Path(__file__).resolve().parent;K=P.parent
meta=json.loads((P/'provenance.json').read_text());data=K/'data';data.mkdir(exist_ok=True)
for item in meta['raw_files']:
    dest=data/item['name']
    if not dest.exists():urllib.request.urlretrieve(item['url'],dest)
    if hashlib.sha256(dest.read_bytes()).hexdigest()!=item['sha256']:raise SystemExit('Hash mismatch: '+str(dest))
ref=K/'reference'
if not ref.exists():subprocess.run(['git','clone',meta['reference_source'],str(ref)],check=True)
subprocess.run(['git','checkout',meta['reference_commit']],cwd=ref,check=True)
print('Inputs verified. Install numpy/scipy/bitarray/psutil, then run make_frame.py.')
