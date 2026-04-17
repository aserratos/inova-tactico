from docxtpl import DocxTemplate
import re

class SmartDocxTemplate(DocxTemplate):
    def patch_xml(self, src_xml):
        patched = super().patch_xml(src_xml)
        def replace_spaces(match):
            inner = match.group(1).strip().replace(' ', '_').replace('\xa0', '_')
            return '{{ ' + inner + ' }}'
        patched = re.sub(r'\{\{(.*?)\}\}', replace_spaces, patched, flags=re.DOTALL)
        return patched

doc = SmartDocxTemplate(r'c:\Users\alberto.serratos\Documents\inova\apptemplate\plantillas\PIPC_MACHOTE_2026.docx')
try:
    vars = doc.get_undeclared_template_variables()
    print('SUCCESS! Variables encontradas:', len(vars))
    print(list(vars)[:5])
except Exception as e:
    print('ERROR:', e)
