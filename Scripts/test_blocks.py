from docxtpl import DocxTemplate
import re

doc = DocxTemplate(r'c:\Users\alberto.serratos\Documents\inova\apptemplate\plantillas\PIPC_MACHOTE_2026.docx')
xml = doc.get_xml()
xml = doc.patch_xml(xml)

# search for all {% ... %}
blocks = re.findall(r'{%(.*?)%}', xml)
for b in blocks:
    print('Found block:', b)

# try get_undeclared_template_variables from the raw doc without our subclass:
try:
    doc.get_undeclared_template_variables()
except Exception as e:
    print('Error message:', str(e))
