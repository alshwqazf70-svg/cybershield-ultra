#!/usr/bin/env python3
# check_env.py - التحقق من متغيرات البيئة

import os
from pathlib import Path
from dotenv import load_dotenv

# تحميل المتغيرات
load_dotenv()

print("\n" + "="*60)
print("🔍 التحقق من متغيرات البيئة")
print("="*60)

# قائمة المتغيرات المطلوبة
required_vars = [
    'SERPAPI_KEY',
    'UNSPLASH_API_KEY',
    'YOUTUBE_API_KEY',
    'BLOGGER_BLOG_ID',
    'BLOGGER_CLIENT_SECRET',
    'GOOGLE_CREDENTIALS_FILE'
]

# التحقق من كل متغير
for var in required_vars:
    value = os.environ.get(var, '')
    
    if value:
        if var in ['BLOGGER_CLIENT_SECRET', 'GOOGLE_CREDENTIALS_FILE']:
            if Path(value).exists():
                print(f"✅ {var}: {value} (الملف موجود)")
            else:
                print(f"❌ {var}: {value} (⚠️ الملف غير موجود!)")
        else:
            masked = value[:8] + "..." + value[-4:] if len(value) > 12 else "***"
            print(f"✅ {var}: {masked}")
    else:
        print(f"⚠️ {var}: غير مضبوط")

print("\n" + "="*60)
print("💡 نصيحة: قم بتعبئة المفاتيح في ملف .env")
print("   يمكنك تحرير الملف باستخدام: nano .env")
print("="*60)

if __name__ == "__main__":
    print("\n📌 ملاحظة: الكود يقرأ من os.environ تلقائياً")
    print("   لا حاجة لتعديل أي كلاس!")
