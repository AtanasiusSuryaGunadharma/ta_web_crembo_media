from pypdf import PdfReader
from pathlib import Path

files=["Rev_NonMagang_220711667_SDE_Aloysius.pdf","List Fungsionalitas Website Crembo Media.pdf"]
for name in files:
    print(f"\n=== {name} ===")
    p=Path(name)
    if not p.exists():
        print("not found")
        continue
    r=PdfReader(str(p))
    print("pages:",len(r.pages))
    for i,pg in enumerate(r.pages[:5],1):
        t=(pg.extract_text() or "").replace("\n"," ")
        t=" ".join(t.split())
        print(f"--page {i}--")
        print(t[:900] if t else "<empty>")
