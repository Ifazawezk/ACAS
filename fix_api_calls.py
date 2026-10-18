import re

# Read the file
with open(r'c:\Users\mohan\OneDrive\Desktop\ACAS\advanced_comment_analysis\frontend\static_index.html', 'r', encoding='utf-8') as f:
    content = f.read()

# API endpoints that need trailing slashes (have prefix in APIRouter)
replacements = [
    (r"api\('/comments\?", r"api('/comments/?"),
    (r"api\('/admin/rules", r"api('/admin/rules/"),
    (r"api\('/admin/sentics", r"api('/admin/sentics/"),
    (r"api\('/admin/config", r"api('/admin/config/"),
    (r"api\('/admin/api-configs", r"api('/admin/api-configs/"),
    (r"api\('/ai/analyze", r"api('/ai/analyze/"),
    (r"api\('/ai/scrape-url", r"api('/ai/scrape-url/"),
]

for pattern, replacement in replacements:
    before = content
    content = re.sub(pattern, replacement, content)
    if before != content:
        print(f"✓ Updated: {pattern}")

# Write back
with open(r'c:\Users\mohan\OneDrive\Desktop\ACAS\advanced_comment_analysis\frontend\static_index.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Done!")
