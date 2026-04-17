import inspect
from docxtpl import DocxTemplate
print("get_undeclared_template_variables:")
print(inspect.getsource(DocxTemplate.get_undeclared_template_variables))
print("get_patched_xml:")
try:
    print(inspect.getsource(DocxTemplate.get_patched_xml))
except:
    print("No get_patched_xml method?")
    
print("get_xml:")
try:
    print(inspect.getsource(DocxTemplate.get_xml))
except:
    pass
    
print("render:")
try:
    print(inspect.getsource(DocxTemplate.render))
except:
    pass

