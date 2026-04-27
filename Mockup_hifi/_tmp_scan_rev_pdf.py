from pypdf import PdfReader
import re
r=PdfReader('Rev_NonMagang_220711667_SDE_Aloysius.pdf')
keywords=[r'BAB IV',r'Bab IV',r'implementasi',r'wireframe',r'prototype',r'low-fidelity',r'design thinking',r'usability']
for i,pg in enumerate(r.pages,1):
    t=(pg.extract_text() or '').replace('\n',' ')
    ts=' '.join(t.split())
    low=ts.lower()
    if any(k.lower().replace('\\','') in low for k in ['bab iv','implementasi','wireframe','prototype','design thinking','usability']):
        print(f'PAGE {i}: {ts[:420]}')
