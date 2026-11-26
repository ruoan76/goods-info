from pathlib import Path
import hashlib
import re
import shutil
import sys

src, dest = map(Path, sys.argv[1:])
patches = {
    "index-mG_eqfCM.js": (
        "8dfe2d43584c9d17e70c1575bbca43871bc2e557f49813cf5a7b7a2a51c54984",
        'patch:(e,t,n,s)=>W("PATCH",',
        'patch:(e,t,n,s,version)=>W("PATCH",',
    ),
    "GoodsDetail-C3DgfqC2.js": (
        "2900dfd9074b7246e2d2bef1c7be870ff0f4e10e47aa9c245466cfa547aad133",
        'b.patch(g,r,t,"详情页即点即改")',
        'b.patch(g,r,t,"详情页即点即改",a.value.version)',
    ),
    "FillPrice--txCvQna.js": (
        "4f0ee03c98a63e50bcbd99191196cdb9f8275f92887369af5b95853025a18d34",
        'b.patch(s.barcode,"outprice",t,"价格待补清单批量补价")',
        'b.patch(s.barcode,"outprice",t,"价格待补清单批量补价",s.version)',
    ),
}

def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError(f"Unexpected release structure for {old}")
    return text.replace(old, new)

assert not dest.exists()
for name, (digest, _, _) in patches.items():
    assert hashlib.sha256((src / "assets" / name).read_bytes()).hexdigest() == digest, name
shutil.copytree(src, dest)
assets = dest / "assets"
names = {p.name: f"{p.stem}-goods-version-20261127.js" for p in assets.glob("*.js")}
references = re.compile("|".join(re.escape(name) for name in names))
for path in list(assets.glob("*.js")) + [dest / "index.html"]:
    current = path.read_text()
    if path.name in patches:
        _, old, new = patches[path.name]
        current = replace_once(current, old, new)
    if path.name == "index-mG_eqfCM.js":
        current = replace_once(current, "body:{field:t,new_value:n,reason:s}", "body:{field:t,new_value:n,reason:s,version}")
    current = references.sub(lambda match: names[match.group()], current)
    if path.name in names:
        path = path.rename(assets / names[path.name])
    path.write_text(current)
