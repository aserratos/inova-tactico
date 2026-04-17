from docxtpl import DocxTemplate, InlineImage
from docx.shared import Mm
import os

# Mocking a template with an image tag
print("Checking docxtpl InlineImage signature...")
import inspect
print(inspect.signature(InlineImage.__init__))
