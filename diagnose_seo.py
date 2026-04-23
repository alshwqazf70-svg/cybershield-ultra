#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
================================================================================
🔍 SEO DASHBOARD DIAGNOSTIC TOOL - أداة تشخيص منفصلة
================================================================================

هذه الأداة تقوم بتحليل شامل لجميع الصفحات في مجلد templates/
وتحديد المشكلات في الروابط والمحتوى.

لتشغيلها:
    python diagnose_seo.py

أو في PythonAnywhere:
    python3 /home/CyberSecurityPro/cybershield-ultra-main/diagnose_seo.py
================================================================================
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

# ==================================================================================================
# الإعدادات الأساسية
# ==================================================================================================

# تحديد المسارات
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"

print("=" * 80)
print("🔍 SEO DASHBOARD DIAGNOSTIC TOOL v1.0")
print("=" * 80)
print(f"📁 المسار الأساسي: {BASE_DIR}")
print(f"📁 مجلد templates: {TEMPLATES_DIR}")
print(f"📅 وقت التشغيل: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 80)

# ==================================================================================================
# دالة مسح جميع الملفات في templates
# ==================================================================================================

def scan_all_files():
    """مسح جميع ملفات HTML في مجلد templates"""
    files_list = []

    if not TEMPLATES_DIR.exists():
        print(f"❌ خطأ: مجلد templates غير موجود في {TEMPLATES_DIR}")
        return files_list

    for root, dirs, files in os.walk(TEMPLATES_DIR):
        # استبعاد المجلدات المخفية
        dirs[:] = [d for d in dirs if not d.startswith('.')]

        for file in files:
            if file.endswith('.html'):
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, TEMPLATES_DIR)
                rel_path = rel_path.replace('\\', '/')

                files_list.append({
                    'full_path': full_path,
                    'relative_path': rel_path,
                    'file_name': file,
                    'size': os.path.getsize(full_path),
                    'exists': os.path.exists(full_path)
                })

    return files_list

# ==================================================================================================
# دالة تحديد نوع الصفحة وبناء الرابط الصحيح
# ==================================================================================================

def get_page_type_and_url(relative_path, file_name):
    """تحديد نوع الصفحة وبناء الرابط الصحيح"""

    # الصفحات في المجلدات الفرعية
    if 'blog/' in relative_path:
        page_type = 'blog'
        base_name = file_name.replace('.html', '')
        url = f"/blog/{base_name}.html"

    elif 'ai_posts/' in relative_path:
        page_type = 'ai_post'
        base_name = file_name.replace('.html', '')
        url = f"/ai_posts/{base_name}.html"

    elif 'programmatic/' in relative_path:
        page_type = 'programmatic'
        base_name = file_name.replace('.html', '')
        url = f"/programmatic/{base_name}.html"

    elif 'magnet_pages/' in relative_path:
        page_type = 'magnet_page'
        base_name = file_name.replace('.html', '')
        url = f"/magnet_pages/{base_name}.html"

    elif 'legendary_articles/' in relative_path:
        page_type = 'legendary'
        base_name = file_name.replace('.html', '')
        url = f"/legendary_articles/{base_name}.html"

    # الصفحة الرئيسية
    elif file_name == 'index.html':
        page_type = 'home'
        url = "/"

    # الصفحات الثابتة
    elif file_name in ['about.html', 'contact.html', 'privacy.html', 'terms.html', 'tools.html']:
        page_type = 'static'
        base_name = file_name.replace('.html', '')
        url = f"/{base_name}"

    # الصفحات العادية (الأدوات وغيرها)
    else:
        page_type = 'tool'
        base_name = file_name.replace('.html', '')
        url = f"/{base_name}"

    return page_type, url

# ==================================================================================================
# دالة اختبار الوصول إلى الصفحة
# ==================================================================================================

def test_page_access(url, site_url="https://cybersecuritypro.pythonanywhere.com"):
    """اختبار الوصول إلى صفحة معينة باستخدام requests"""
    try:
        import requests
        full_url = f"{site_url}{url}"
        response = requests.get(full_url, timeout=5, allow_redirects=True)

        return {
            'url': full_url,
            'status_code': response.status_code,
            'content_length': len(response.content),
            'success': response.status_code == 200,
            'redirect': response.url != full_url
        }
    except ImportError:
        return {
            'url': f"{site_url}{url}",
            'status_code': 'unknown',
            'content_length': 0,
            'success': False,
            'error': 'requests module not available'
        }
    except Exception as e:
        return {
            'url': f"{site_url}{url}",
            'status_code': 'error',
            'content_length': 0,
            'success': False,
            'error': str(e)[:100]
        }

# ==================================================================================================
# التشخيص الرئيسي
# ==================================================================================================

def main():
    print("\n📂 جاري مسح مجلد templates...")
    files = scan_all_files()

    if not files:
        print("❌ لا توجد ملفات HTML في مجلد templates")
        return

    print(f"✅ تم العثور على {len(files)} ملف HTML\n")

    # تصنيف الملفات
    categories = {
        'blog': [],
        'ai_post': [],
        'programmatic': [],
        'magnet_page': [],
        'legendary': [],
        'home': [],
        'static': [],
        'tool': []
    }

    url_mapping = []

    for f in files:
        page_type, url = get_page_type_and_url(f['relative_path'], f['file_name'])
        categories[page_type].append({
            'file': f['relative_path'],
            'url': url,
            'size': f['size']
        })
        url_mapping.append({
            'file': f['relative_path'],
            'url': url,
            'size': f['size'],
            'type': page_type
        })

    # عرض الإحصائيات
    print("=" * 80)
    print("📊 إحصائيات الملفات حسب النوع:")
    print("=" * 80)

    for cat, items in categories.items():
        if items:
            print(f"  • {cat}: {len(items)} ملف(ات)")

    print("\n" + "=" * 80)
    print("🔗 تفاصيل الروابط (أول 10 ملفات من كل نوع):")
    print("=" * 80)

    for cat, items in categories.items():
        if items:
            print(f"\n📁 {cat.upper()} ({len(items)} ملف):")
            for i, item in enumerate(items[:10]):
                size_kb = item['size'] / 1024
                print(f"    {i+1}. {item['file']}")
                print(f"       الرابط: {item['url']}")
                print(f"       الحجم: {size_kb:.1f} KB")

    # تحليل الملفات الصغيرة (محتوى فارغ محتمل)
    print("\n" + "=" * 80)
    print("⚠️  الملفات ذات الحجم الصغير (أقل من 5KB - قد تكون فارغة):")
    print("=" * 80)

    small_files = [f for f in url_mapping if f['size'] < 5120]
    if small_files:
        for f in small_files:
            size_kb = f['size'] / 1024
            print(f"  • {f['file']} -> {f['url']} ({size_kb:.1f} KB)")
    else:
        print("  ✅ لا توجد ملفات صغيرة الحجم")

    # تحليل الروابط التي تحتوي على templates/ في المسار
    print("\n" + "=" * 80)
    print("🔴 ملفات تحتوي على 'templates/' في الرابط (مشكلة محتملة):")
    print("=" * 80)

    bad_links = [f for f in url_mapping if 'templates/' in f['url']]
    if bad_links:
        for f in bad_links:
            print(f"  ❌ {f['file']} -> {f['url']}")
    else:
        print("  ✅ لا توجد روابط تحتوي على templates/")

    # ==============================================================================================
    # اختبار الوصول الفعلي (اختياري)
    # ==============================================================================================

    print("\n" + "=" * 80)
    print("🌐 اختبار الوصول الفعلي للصفحات (سيتم اختبار أول 20 صفحة):")
    print("=" * 80)

    # سؤال المستخدم
    response = input("\nهل تريد اختبار الوصول الفعلي للصفحات؟ (y/n): ")

    if response.lower() == 'y':
        test_results = {
            'working': [],
            'broken': [],
            'empty': []
        }

        for i, f in enumerate(url_mapping[:20]):
            print(f"\n[{i+1}/20] اختبار: {f['url']}")
            result = test_page_access(f['url'])

            if result['success']:
                if result['content_length'] < 1000:
                    test_results['empty'].append({
                        'url': f['url'],
                        'file': f['file'],
                        'size': f['size'],
                        'content_length': result['content_length']
                    })
                    print(f"    ⚠️  محتوى فارغ أو صغير جداً (حجم المحتوى: {result['content_length']} bytes)")
                else:
                    test_results['working'].append({
                        'url': f['url'],
                        'file': f['file'],
                        'size': f['size'],
                        'content_length': result['content_length']
                    })
                    print(f"    ✅ يعمل (حجم المحتوى: {result['content_length']} bytes)")
            else:
                test_results['broken'].append({
                    'url': f['url'],
                    'file': f['file'],
                    'status': result.get('status_code', 'error'),
                    'error': result.get('error', 'unknown')
                })
                print(f"    ❌ لا يعمل - {result.get('status_code', 'error')}")

        # عرض نتائج الاختبار
        print("\n" + "=" * 80)
        print("📋 نتائج اختبار الوصول:")
        print("=" * 80)

        print(f"\n✅ صفحات تعمل: {len(test_results['working'])}")
        for r in test_results['working']:
            print(f"    • {r['url']}")

        print(f"\n⚠️  صفحات محتوى فارغ: {len(test_results['empty'])}")
        for r in test_results['empty']:
            print(f"    • {r['url']} (حجم الملف: {r['size']} bytes, محتوى: {r['content_length']} bytes)")

        print(f"\n❌ صفحات لا تعمل (404): {len(test_results['broken'])}")
        for r in test_results['broken']:
            print(f"    • {r['url']} - {r.get('status', 'unknown')}")

    # حفظ النتائج في ملف JSON
    print("\n" + "=" * 80)
    print("💾 حفظ النتائج في ملف report.json")
    print("=" * 80)

    report = {
        'timestamp': datetime.now().isoformat(),
        'total_files': len(files),
        'categories': {k: len(v) for k, v in categories.items()},
        'url_mapping': url_mapping,
        'small_files': small_files,
        'bad_links': bad_links
    }

    report_path = BASE_DIR / 'seo_diagnostic_report.json'
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2, default=str)

    print(f"✅ تم حفظ التقرير في: {report_path}")

    print("\n" + "=" * 80)
    print("🔍 انتهى التشخيص!")
    print("=" * 80)
    print("\nيمكنك الآن فتح ملف seo_diagnostic_report.json لرؤية التفاصيل الكاملة")
    print("أو مشاركة النتائج معي لتحليلها")

if __name__ == "__main__":
    main()