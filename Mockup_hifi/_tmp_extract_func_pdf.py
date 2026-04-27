from pypdf import PdfReader
r=PdfReader('List Fungsionalitas Website Crembo Media.pdf')
for i,pg in enumerate(r.pages,1):
    t=(pg.extract_text() or '').replace('\n',' ')
    t=' '.join(t.split())
    print(f'PAGE {i}: {t[:280]}')
