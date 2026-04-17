import sys
from docxtpl import DocxTemplate
import re

doc = DocxTemplate(r'c:\Users\alberto.serratos\Documents\inova\apptemplate\plantillas\PIPC_MACHOTE_2026.docx')
try:
    doc.get_undeclared_template_variables()
except Exception as e:
    print('Failed:', e)
