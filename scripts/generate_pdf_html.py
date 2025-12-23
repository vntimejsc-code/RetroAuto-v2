import os
import re

# 1. Config
SOURCE_DIR = "docs/user_guide"
OUTPUT_FILE = "docs/RetroAuto_UserGuide_v5.html"
CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Merriweather:ital,wght@0,300;0,400;0,700;1,400&family=JetBrains+Mono:wght@400;600&display=swap');
    
    body {
        font-family: 'Merriweather', serif;
        line-height: 1.6;
        color: #333;
        max-width: 800px;
        margin: 0 auto;
        padding: 40px;
    }
    h1, h2, h3 { font-family: sans-serif; color: #2c3e50; }
    h1 { border-bottom: 2px solid #eee; padding-bottom: 10px; break-before: always; page-break-before: always; }
    h2 { margin-top: 30px; border-bottom: 1px solid #eee; }
    code { font-family: 'JetBrains Mono', monospace; background: #f4f4f4; padding: 2px 5px; border-radius: 3px; font-size: 0.9em; }
    pre { background: #f8f8f8; padding: 15px; border-radius: 5px; overflow-x: auto; border: 1px solid #ddd; }
    pre code { background: none; padding: 0; }
    blockquote { border-left: 4px solid #3498db; margin: 0; padding-left: 15px; color: #555; background: #f1f9ff; padding: 10px; }
    table { border-collapse: collapse; width: 100%; margin: 20px 0; }
    th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
    th { background-color: #f2f2f2; }
    img { max-width: 100%; height: auto; display: block; margin: 20px auto; }
    
    @media print {
        body { max-width: 100%; padding: 0; }
        a { text-decoration: none; color: #333; }
        pre, blockquote { page-break-inside: avoid; }
        h1 { page-break-before: always; }
        h1:first-child { page-break-before: avoid; }
    }
</style>
"""

# 2. Reading Order
FILES = [
    "01_start.md",
    "02_ide_visual.md",
    "03_ide_code.md",
    "04_concepts.md",
    "05_cookbook.md",
    "06_troubleshooting.md",
    "07_reference.md"
]

# 3. Processing
content_html = ""
for fname in FILES:
    path = os.path.join(SOURCE_DIR, fname)
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            md = f.read()
            # Simple Markdown to HTML fallback (since we might not have 'markdown' lib)
            # 1. Headers
            md = re.sub(r'^# (.*)', r'<h1>\1</h1>', md, flags=re.MULTILINE)
            md = re.sub(r'^## (.*)', r'<h2>\1</h2>', md, flags=re.MULTILINE)
            md = re.sub(r'^### (.*)', r'<h3>\1</h3>', md, flags=re.MULTILINE)
            # 2. Bold/Italic
            md = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', md)
            md = re.sub(r'`(.*?)`', r'<code>\1</code>', md)
            # 3. Code Blocks
            md = re.sub(r'```(.*?)```', r'<pre><code>\1</code></pre>', md, flags=re.DOTALL)
            # 4. Images
            md = re.sub(r'!\[(.*?)\]\((.*?)\)', r'<img src="\2" alt="\1">', md)
            
            content_html += f"<section class='chapter'>{md}</section>\n"

# 4. Wrap
final_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>RetroAuto v2 - User Guide v5.0</title>
    {CSS}
</head>
<body>
    <div style="text-align: center; padding: 50px 0; page-break-after: always;">
        <h1 style="font-size: 3em; border: none;">RetroAuto v2</h1>
        <h2 style="font-size: 2em; border: none; color: #555;">The Encyclopedia (v5.0)</h2>
        <p>Generated: 2025-12-23</p>
    </div>
    {content_html}
</body>
</html>
"""

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(final_html)

print(f"✅ Generated: {OUTPUT_FILE}")
