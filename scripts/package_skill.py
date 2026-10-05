"""Create a local share ZIP; never upload or overwrite an existing archive."""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path
from validate_skill import validate

def package(root, output):
    root=Path(root).resolve();output=Path(output).resolve()
    if output.exists():raise FileExistsError('Archive exists; select a new output path')
    if output.is_relative_to(root):raise ValueError('Archive must be outside skill root')
    result=validate(root)
    if not result['ok']:raise ValueError(json.dumps(result['errors'],ensure_ascii=False))
    output.parent.mkdir(parents=True,exist_ok=True);names=[]
    with zipfile.ZipFile(output,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for path in sorted(root.rglob('*')):
            rel=path.relative_to(root)
            if not path.is_file() or set(rel.parts)&{'__pycache__','qa','.git','.pytest_cache'} or path.suffix=='.pyc':continue
            if path.is_symlink():raise ValueError('Symlink not allowed in share package')
            name=root.name+'/'+rel.as_posix();z.write(path,name);names.append(name)
    return {'file':output.name,'files':len(names),'bytes':output.stat().st_size,'sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'excluded':['raw qa screenshots/history','Python caches'],'published':False}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);p.add_argument('output',type=Path);a=p.parse_args();print(json.dumps(package(a.root,a.output),ensure_ascii=False,indent=2))
if __name__=='__main__':main()
