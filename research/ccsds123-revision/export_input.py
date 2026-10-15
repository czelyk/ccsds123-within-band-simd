"""Reorder a delivered u16le BSQ product without changing sample values."""
from pathlib import Path
import argparse,json,hashlib
import numpy as np
p=argparse.ArgumentParser();p.add_argument('input',type=Path);p.add_argument('output',type=Path);p.add_argument('--width',type=int,default=4096);p.add_argument('--height',type=int,default=4096);p.add_argument('--bands',type=int,default=7);p.add_argument('--layout',choices=['BIP','BIL'],default='BIP');a=p.parse_args()
if a.output.exists():raise SystemExit('Output exists; choose a new path to preserve evidence')
assert a.input.stat().st_size==a.width*a.height*a.bands*2
x=np.memmap(a.input,mode='r',dtype='<u2',shape=(a.bands,a.height,a.width))
y=np.ascontiguousarray(x.transpose(1,2,0) if a.layout=='BIP' else x.transpose(1,0,2))
y.tofile(a.output)
def digest(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  while b:=f.read(2**20):h.update(b)
 return h.hexdigest()
record={'input':str(a.input.resolve()),'output':str(a.output.resolve()),'input_storage':'u16le BSQ','output_storage':'u16le '+a.layout,'width':a.width,'height':a.height,'bands':a.bands,'sample_values_changed':False,'input_sha256':digest(a.input),'output_sha256':digest(a.output),'processing_level':'preserved from source; reordering does not create raw focal-plane data'}
a.output.with_suffix(a.output.suffix+'.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record,indent=2))
