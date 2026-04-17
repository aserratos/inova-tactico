import zipfile
import io
import re
from docxtpl import DocxTemplate

def fix_template(docx_path):
    doc = DocxTemplate(docx_path)
    xml_to_patch = doc.xml_to_patch
    
    zin = zipfile.ZipFile(docx_path, 'r')
    zout_mem = io.BytesIO()
    zout = zipfile.ZipFile(zout_mem, 'w')
    
    def replacer(match):
        content = match.group(1)
        fixed = content.strip().replace(' ', '_').replace(' ', '_')
        return '{{ ' + fixed + ' }}'
        
    for item in zin.infolist():
        buffer = zin.read(item.filename)
        if item.filename in xml_to_patch:
            # Clean runs inside tags using docxtpl
            xml_str = buffer.decode('utf-8')
            patched = doc.patch_xml(xml_str)
            # Fix the spaces inside the cleaned {{ ... }}
            fixed_xml = re.sub(r'\{\{(.*?)\}\}', replacer, patched, flags=re.DOTALL)
            zout.writestr(item, fixed_xml)
        else:
            zout.writestr(item, buffer)
            
    zout.close()
    zin.close()
    
    with open('test_fixed.docx', 'wb') as f:
        f.write(zout_mem.getvalue())
        
    print('Testing new fixed docx...')
    new_doc = DocxTemplate('test_fixed.docx')
    from jinja2.exceptions import TemplateSyntaxError
    try:
        vars = new_doc.get_undeclared_template_variables()
        print('SUCCESS variables:', vars)
    except TemplateSyntaxError as e:
        print('STILL ERROR:', e)

fix_template(r'c:\Users\alberto.serratos\Documents\inova\apptemplate\plantillas\PIPC_MACHOTE_2026.docx')
