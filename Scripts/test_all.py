import os
import io
import re
from docxtpl import DocxTemplate
import logging

class SmartDocxTemplate(DocxTemplate):
    def patch_xml(self, src_xml):
        patched = super().patch_xml(src_xml)
        def replace_spaces(match):
            inner_content = match.group(1).strip()
            fixed = re.sub(r'\s+', '_', inner_content)
            return '{{ ' + fixed + ' }}'
        patched = re.sub(r'\{\{(.*?)\}\}', replace_spaces, patched, flags=re.DOTALL)
        return patched

print("Testing ALL files in plantillas...")
d = r'c:\Users\alberto.serratos\Documents\inova\apptemplate\plantillas'
files = [os.path.join(d, f) for f in os.listdir(d) if f.endswith('.docx')]
for f in files:
    try:
        doc = SmartDocxTemplate(f)
        v = doc.get_undeclared_template_variables()
        print("SUCCESS on:", os.path.basename(f), len(v))
    except Exception as e:
        print("FAILED on:", os.path.basename(f), e)
