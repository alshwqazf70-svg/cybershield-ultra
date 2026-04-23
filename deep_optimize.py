import os
import re
import hashlib
from pathlib import Path

BASE = Path("/home/cybersecuritypro/mysite")
STATIC = BASE / "static"

def minify_css(content):
    # إزالة التعليقات
    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
    # إزالة المسافات
    content = re.sub(r'\s+', ' ', content)
    # تحسين الخصائص
    content = re.sub(r':\s+', ':', content)
    content = re.sub(r',\s+', ',', content)
    content = re.sub(r';\s+', ';', content)
    content = re.sub(r'\s*\{\s*', '{', content)
    content = re.sub(r'\s*\}\s*', '}', content)
    return content.strip()

def add_hash(file_path):
    with open(file_path, 'rb') as f:
        content = f.read()
    file_hash = hashlib.md5(content).hexdigest()[:8]
    new_name = f"{file_path.stem}.{file_hash}{file_path.suffix}"
    new_path = file_path.parent / new_name
    os.rename(file_path, new_path)
    return new_name

# تحسين CSS
for f in STATIC.glob("css/*.css"):
    with open(f, 'r') as file:
        original = file.read()
    minified = minify_css(original)
    with open(f, 'w') as file:
        file.write(minified)
    print(f"✅ CSS: {f.name} ({len(original)} → {len(minified)} bytes)")

# إضافة هاش للملفات
print("\n🔗 إضافة Cache Busting...")
for f in STATIC.glob("css/*.css"):
    new = add_hash(f)
    print(f"   {f.name} → {new}")
for f in STATIC.glob("js/*.js"):
    new = add_hash(f)
    print(f"   {f.name} → {new}")

print("\n🎉 اكتمل! الآن اذهب إلى Web → Reload")
