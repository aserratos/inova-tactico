from docxtpl import DocxTemplate
import re

class SmartDocxTemplate(DocxTemplate):
    def patch_xml(self, src_xml):
        patched = super().patch_xml(src_xml)
        def replace_spaces(match):
            inner = re.sub(r'\s+', '_', match.group(1).strip())
            return '{{ ' + inner + ' }}'
        patched = re.sub(r'\{\{([^\}]+)\}\}', replace_spaces, patched, flags=re.DOTALL)
        return patched

doc = SmartDocxTemplate(r'c:\Users\alberto.serratos\Documents\inova\apptemplate\plantillas\PIPC_MACHOTE_2026.docx')
try:
    xml = doc.get_patched_xml()
    import jinja2
    env = jinja2.Environment()
    env.from_string(xml)
    print("SUCCESS")
except Exception as e:
    print('ERROR:', e)
    import traceback
    traceback.print_exc()
