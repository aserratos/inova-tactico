import os
import glob

api_ts = """export const apiFetch = async (url: string, options: RequestInit = {}) => {
  let headers: Record<string, string> = { ...(options.headers as any) };
  if ((window as any).Clerk && (window as any).Clerk.session) {
    const token = await (window as any).Clerk.session.getToken();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }
  return fetch(url, { ...options, headers });
};
"""

os.makedirs('frontend-pwa/src/lib', exist_ok=True)
with open('frontend-pwa/src/lib/api.ts', 'w', encoding='utf-8') as f:
    f.write(api_ts)

files = glob.glob('frontend-pwa/src/pages/*.tsx') + glob.glob('frontend-pwa/src/components/*.tsx')

for filepath in files:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    if 'fetch(' in content and filepath != 'frontend-pwa/src/lib/api.ts':
        content = "import { apiFetch } from '../lib/api';\n" + content
        content = content.replace('await fetch(', 'await apiFetch(')
        content = content.replace(' fetch(', ' apiFetch(')
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
