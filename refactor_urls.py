import os
import re

TARGET_DIR = r"c:\Users\alberto.serratos\Documents\inova\apptemplate\frontend-pwa\src"

def refactor_urls():
    for root, dirs, files in os.walk(TARGET_DIR):
        for file in files:
            if file.endswith(".tsx") or file.endswith(".ts"):
                filepath = os.path.join(root, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()

                if "http://localhost:8001" in content:
                    # Replace single-quoted urls: 'http://localhost:8001/...' -> `${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/...`
                    # Note we must change the outer quotes to backticks.
                    content = re.sub(
                        r"'http://localhost:8001(.*?)'",
                        r"`${import.meta.env.VITE_API_URL || 'http://localhost:8001'}\1`",
                        content
                    )
                    
                    # Replace double-quoted urls just in case
                    content = re.sub(
                        r'"http://localhost:8001(.*?)"',
                        r"`${import.meta.env.VITE_API_URL || 'http://localhost:8001'}\1`",
                        content
                    )

                    # Replace backticked urls (already string templates): `http://localhost:8001/...`
                    content = re.sub(
                        r"`http://localhost:8001(.*?)`",
                        r"`${import.meta.env.VITE_API_URL || 'http://localhost:8001'}\1`",
                        content
                    )

                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"Refactored: {filepath}")

if __name__ == "__main__":
    refactor_urls()
