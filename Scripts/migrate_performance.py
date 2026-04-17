import sqlite3
import os
import json
from docxtpl import DocxTemplate
import re

# Same SmartDocxTemplate logic for patches
class SmartDocxTemplate(DocxTemplate):
    def patch_xml(self, src_xml):
        patched = super().patch_xml(src_xml)
        def replace_spaces(match):
            inner_content = match.group(1).strip().lower()
            fixed_content = re.sub(r'\W+', '_', inner_content).strip('_')
            fixed_content = re.sub(r'_+', '_', fixed_content)
            return '{{ ' + fixed_content + ' }}'
        patched = re.sub(r'\{\{(.*?)\}\}', replace_spaces, patched, flags=re.DOTALL)
        return patched

db_path = os.path.join('instance', 'app.db')
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    try:
        # 1. Add Column
        try:
            cur.execute("ALTER TABLE template ADD COLUMN variables_json TEXT DEFAULT '[]'")
        except: pass

        # 2. Pre-populate for each template
        cur.execute("SELECT id, ruta_archivo_docx FROM template")
        templates = cur.fetchall()
        for t_id, path in templates:
            if os.path.exists(path):
                try:
                    doc = SmartDocxTemplate(path)
                    vars = list(doc.get_undeclared_template_variables())
                    cur.execute("UPDATE template SET variables_json = ? WHERE id = ?", (json.dumps(vars), t_id))
                    print(f"Template {t_id} optimized.")
                except Exception as e:
                    print(f"Error on template {t_id}: {e}")
        
        conn.commit()
        print("Performance migration completed.")
    except Exception as e:
        print("Error:", e)
    finally:
        conn.close()
else:
    print("Database instance not found.")
