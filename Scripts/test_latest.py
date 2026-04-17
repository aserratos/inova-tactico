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

print("Testing the most recent file in plantillas...")
d = r'c:\Users\alberto.serratos\Documents\inova\apptemplate\plantillas'
files = [os.path.join(d, f) for f in os.listdir(d) if f.endswith('.docx')]
latest_file = max(files, key=os.path.getmtime)
print("Latest uploaded file:", latest_file)

try:
    doc = SmartDocxTemplate(latest_file)
    v = doc.get_undeclared_template_variables()
    print("SUCCESS on latest file:", len(v))
except Exception as e:
    print("FAILED on latest file:", e)
