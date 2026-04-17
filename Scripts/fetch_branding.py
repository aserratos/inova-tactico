import urllib.request
import re

url = "https://inovasecurite.mx"
try:
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    resp = urllib.request.urlopen(req)
    html = resp.read().decode('utf-8')
    
    print("--- LOGOS/IMAGES ---")
    imgs = re.findall(r'<img[^>]+src=["\'](.*?)["\']', html)
    for src in imgs:
        if 'logo' in src.lower() or 'icon' in src.lower() or 'svg' in src.lower() or 'png' in src.lower():
            print(src)

    print("\n--- FONTS (Google Fonts) ---")
    links = re.findall(r'<link[^>]+href=["\'](.*?fonts\.googleapis\.com.*?)["\']', html)
    for link in links:
        print(link)
            
    # Search for common CSS variables or color codes
    colors = re.findall(r'#([0-9a-fA-F]{3,6})', html)
    # Get most common colors
    from collections import Counter
    top_colors = Counter([c.lower() for c in colors]).most_common(20)
    print("\n--- TOP HEX COLORS IN HTML ---")
    for c, count in top_colors:
        if len(c) in (3, 6):
            print(f"#{c}: {count} times")

    print("\n--- INLINE CSS HEX COLORS ---")
    inline_colors = re.findall(r'color:\s*#([0-9a-fA-F]{3,6})|background[-color]*:\s*#([0-9a-fA-F]{3,6})', html)
    top_inline = Counter([c.lower() for t in inline_colors for c in t if c]).most_common(10)
    for c, count in top_inline:
        if len(c) in (3, 6):
            print(f"#{c}: {count} times")

except Exception as e:
    print("Error fetching:", e)
