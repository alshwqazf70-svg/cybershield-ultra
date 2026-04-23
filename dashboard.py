#!/usr/bin/env python3
# ============================================================
# dashboard.py - لوحة تحكم CyberShield Ultra الاحترافية
# الإصدار 3.0 - مع مزامنة GitHub Actions
# ============================================================

import json
import os
import hashlib
import hmac
from datetime import datetime, timedelta
from flask import Blueprint, render_template, jsonify, request

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/malek-dashboard')
STATS_FILE = "visitor_stats.json"

# ============================================================
# مفتاح الأمان للمزامنة (يُفضل وضعه في متغيرات البيئة)
# ============================================================
SYNC_SECRET = os.environ.get('CYBERSHIELD_SECRET', 'CyberShield_Secret_2026')

# ============================================================
# إحداثيات جميع المواقع الـ 94
# ============================================================
LOCATION_COORDINATES = {
    # العالم العربي
    "الرياض": (24.7136, 46.6753), "جدة": (21.4858, 39.1925),
    "الدمام": (26.4207, 50.0888), "مكة": (21.3891, 39.8579),
    "المدينة": (24.5247, 39.5692), "دبي": (25.2048, 55.2708),
    "أبوظبي": (24.4539, 54.3773), "الشارقة": (25.3463, 55.4209),
    "القاهرة": (30.0444, 31.2357), "الإسكندرية": (31.2001, 29.9187),
    "الجيزة": (30.0131, 31.2089), "الدوحة": (25.2769, 51.5200),
    "المنامة": (26.2285, 50.5860), "مسقط": (23.5880, 58.3829),
    "الكويت": (29.3759, 47.9774), "عمان": (31.9454, 35.9284),
    "بيروت": (33.8938, 35.5018), "الدار البيضاء": (33.5731, -7.5898),
    "الرباط": (34.0209, -6.8416), "تونس": (36.8065, 10.1815),
    "الجزائر": (36.7372, 3.0865), "الخرطوم": (15.5007, 32.5599),
    "طرابلس": (32.8872, 13.1913), "بغداد": (33.3152, 44.3661),
    "دمشق": (33.5138, 36.2765), "صنعاء": (15.3694, 44.1910),
    "غزة": (31.5017, 34.4668), "القدس": (31.7683, 35.2137),
    "رام الله": (31.9078, 35.5354),

    # أمريكا الشمالية
    "نيويورك": (40.7128, -74.0060), "لوس أنجلوس": (34.0522, -118.2437),
    "شيكاغو": (41.8781, -87.6298), "هيوستن": (29.7604, -95.3698),
    "ميامي": (25.7617, -80.1918), "سان فرانسيسكو": (37.7749, -122.4194),
    "سياتل": (47.6062, -122.3321), "بوسطن": (42.3601, -71.0589),
    "تورنتو": (43.6532, -79.3832), "فانكوفر": (49.2827, -123.1207),
    "مونتريال": (45.5017, -73.5673), "مكسيكو سيتي": (19.4326, -99.1332),

    # أوروبا
    "لندن": (51.5074, -0.1278), "مانشستر": (53.4808, -2.2426),
    "برمنغهام": (52.4862, -1.8904), "باريس": (48.8566, 2.3522),
    "مرسيليا": (43.2965, 5.3698), "ليون": (45.7640, 4.8357),
    "برلين": (52.5200, 13.4050), "ميونخ": (48.1351, 11.5820),
    "هامبورغ": (53.5511, 9.9937), "مدريد": (40.4168, -3.7038),
    "برشلونة": (41.3851, 2.1734), "إشبيلية": (37.3891, -5.9845),
    "روما": (41.9028, 12.4964), "ميلانو": (45.4642, 9.1900),
    "نابولي": (40.8518, 14.2681), "أمستردام": (52.3676, 4.9041),
    "روتردام": (51.9244, 4.4777), "بروكسل": (50.8503, 4.3517),
    "زيورخ": (47.3769, 8.5417), "جنيف": (46.2044, 6.1432),
    "فيينا": (48.2082, 16.3738), "ستوكهولم": (59.3293, 18.0686),
    "أوسلو": (59.9139, 10.7522), "كوبنهاغن": (55.6761, 12.5683),
    "وارسو": (52.2297, 21.0122), "براغ": (50.0755, 14.4378),
    "بودابست": (47.4979, 19.0402), "أثينا": (37.9838, 23.7275),
    "إسطنبول": (41.0082, 28.9784), "موسكو": (55.7558, 37.6173),

    # آسيا
    "طوكيو": (35.6895, 139.6917), "أوساكا": (34.6937, 135.5023),
    "يوكوهاما": (35.4437, 139.6380), "سيول": (37.5665, 126.9780),
    "بوسان": (35.1796, 129.0756), "بكين": (39.9042, 116.4074),
    "شنغهاي": (31.2304, 121.4737), "قوانغتشو": (23.1291, 113.2644),
    "هونغ كونغ": (22.3193, 114.1694), "تايبيه": (25.0330, 121.5654),
    "سنغافورة": (1.3521, 103.8198), "كوالالمبور": (3.1390, 101.6869),
    "جاكرتا": (-6.2088, 106.8456), "بانكوك": (13.7563, 100.5018),
    "مانيلا": (14.5995, 120.9842), "هانوي": (21.0285, 105.8542),
    "مومباي": (19.0760, 72.8777), "دلهي": (28.6139, 77.2090),
    "بنغالور": (12.9716, 77.5946), "كراتشي": (24.8607, 67.0011),
    "طهران": (35.6892, 51.3890),

    # أمريكا الجنوبية
    "ساو باولو": (-23.5505, -46.6333), "ريو دي جانيرو": (-22.9068, -43.1729),
    "برازيليا": (-15.7975, -47.8919), "بوينس آيرس": (-34.6037, -58.3816),
    "سانتياغو": (-33.4489, -70.6693), "ليما": (-12.0464, -77.0428),
    "بوغوتا": (4.7110, -74.0721), "كاراكاس": (10.4806, -66.9036),

    # أفريقيا
    "جوهانسبرغ": (-26.2041, 28.0473), "كيب تاون": (-33.9249, 18.4241),
    "لاغوس": (6.5244, 3.3792), "نيروبي": (-1.2921, 36.8219),
    "أديس أبابا": (9.0320, 38.7469), "داكار": (14.7167, -17.4677),
    "أكرا": (5.6037, -0.1870),

    # أوقيانوسيا
    "سيدني": (-33.8688, 151.2093), "ملبورن": (-37.8136, 144.9631),
    "بريزبن": (-27.4698, 153.0251), "بيرث": (-31.9505, 115.8605),
    "أوكلاند": (-36.8485, 174.7633), "ويلينغتون": (-41.2866, 174.7756),
}

# ============================================================
# دوال مساعدة محسنة
# ============================================================
def load_stats():
    """تحميل الإحصائيات من الملف مع معالجة الأخطاء"""
    default = {
        "total_runs": 0, "total_sessions": 0, "total_pages": 0,
        "total_tests": 0, "tools_tested": {}, "locations_visited": {},
        "history": []
    }

    if not os.path.exists(STATS_FILE):
        return default

    try:
        with open(STATS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for key in default:
                if key not in data:
                    data[key] = default[key]
            return data
    except (json.JSONDecodeError, IOError) as e:
        print(f"خطأ في قراءة الإحصائيات: {e}")
        return default
    except Exception as e:
        print(f"خطأ غير متوقع: {e}")
        return default

def save_stats_atomic(data):
    """حفظ الإحصائيات بشكل ذري (Atomic Write)"""
    temp_file = STATS_FILE + '.tmp'
    try:
        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.replace(temp_file, STATS_FILE)
        return True
    except Exception as e:
        print(f"خطأ في حفظ الإحصائيات: {e}")
        return False

def get_location_coordinates(location_name):
    """استخراج الإحداثيات من اسم الموقع (كامل)"""
    for key, coords in LOCATION_COORDINATES.items():
        if key in location_name:
            return coords
    parts = location_name.split('،')[0].strip()
    if parts in LOCATION_COORDINATES:
        return LOCATION_COORDINATES[parts]
    return (0, 0)

def get_date_range(request_args):
    """استخراج نطاق التاريخ من طلب API"""
    from_date = request_args.get('from')
    to_date = request_args.get('to')

    try:
        if from_date:
            from_date = datetime.strptime(from_date, '%Y-%m-%d').date()
        else:
            from_date = datetime.now().date() - timedelta(days=30)

        if to_date:
            to_date = datetime.strptime(to_date, '%Y-%m-%d').date()
        else:
            to_date = datetime.now().date()

        return from_date, to_date
    except ValueError:
        return datetime.now().date() - timedelta(days=30), datetime.now().date()

def verify_signature(data, signature):
    """التحقق من توقيع البيانات (اختياري للأمان الإضافي)"""
    if not signature:
        return False
    expected = hmac.new(
        SYNC_SECRET.encode(),
        json.dumps(data, sort_keys=True).encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)

# ============================================================
# المسارات
# ============================================================
@dashboard_bp.route('/')
@dashboard_bp.route('')
def index():
    """الصفحة الرئيسية للوحة التحكم"""
    stats = load_stats()

    # إحصائيات اليوم
    today = datetime.now().date()
    today_sessions = 0
    today_pages = 0
    today_tests = 0

    for run in stats.get("history", []):
        try:
            run_date = datetime.fromisoformat(run["timestamp"]).date()
            if run_date == today:
                for session in run.get("sessions", []):
                    if session.get("success"):
                        today_sessions += 1
                        today_pages += session.get("pages_visited", 0)
                        today_tests += session.get("tests_performed", 0)
        except (ValueError, KeyError):
            continue

    return render_template('dashboard.html',
                          stats=stats,
                          today_sessions=today_sessions,
                          today_pages=today_pages,
                          today_tests=today_tests)

@dashboard_bp.route('/api/stats')
def api_stats():
    """API للإحصائيات (للرسوم البيانية) مع دعم التصفية"""
    stats = load_stats()

    from_date, to_date = get_date_range(request.args)

    dates = []
    sessions = []
    pages = []
    tests = []

    delta = (to_date - from_date).days
    if delta > 90:
        from_date = to_date - timedelta(days=90)
        delta = 90

    for i in range(delta, -1, -1):
        date = to_date - timedelta(days=i)
        dates.append(date.strftime("%Y-%m-%d"))

        day_sessions = 0
        day_pages = 0
        day_tests = 0

        for run in stats.get("history", []):
            try:
                run_date = datetime.fromisoformat(run["timestamp"]).date()
                if run_date == date:
                    for session in run.get("sessions", []):
                        if session.get("success"):
                            day_sessions += 1
                            day_pages += session.get("pages_visited", 0)
                            day_tests += session.get("tests_performed", 0)
            except (ValueError, KeyError):
                continue

        sessions.append(day_sessions)
        pages.append(day_pages)
        tests.append(day_tests)

    top_tools = sorted(stats.get("tools_tested", {}).items(),
                       key=lambda x: x[1], reverse=True)[:10]

    top_locations = sorted(stats.get("locations_visited", {}).items(),
                           key=lambda x: x[1], reverse=True)[:15]

    map_data = []
    for loc, count in stats.get("locations_visited", {}).items():
        lat, lon = get_location_coordinates(loc)
        if lat != 0 or lon != 0:
            map_data.append({
                "name": loc,
                "lat": lat,
                "lon": lon,
                "count": count
            })

    recent_sessions = []
    for run in reversed(stats.get("history", [])):
        for session in run.get("sessions", []):
            if session.get("success"):
                recent_sessions.append({
                    "timestamp": run["timestamp"],
                    "location": session.get("location", "Unknown"),
                    "region": session.get("region", "unknown"),
                    "device": session.get("device", "Unknown"),
                    "pages": session.get("pages_visited", 0),
                    "tests": session.get("tests_performed", 0),
                    "duration": session.get("duration_sec", 0),
                    "tools": session.get("tools_tested", [])
                })
            if len(recent_sessions) >= 20:
                break
        if len(recent_sessions) >= 20:
            break

    return jsonify({
        "dates": dates,
        "sessions": sessions,
        "pages": pages,
        "tests": tests,
        "top_tools": top_tools,
        "top_locations": top_locations,
        "map_data": map_data,
        "recent_sessions": recent_sessions,
        "date_range": {
            "from": from_date.strftime("%Y-%m-%d"),
            "to": to_date.strftime("%Y-%m-%d")
        },
        "total_stats": {
            "runs": stats.get("total_runs", 0),
            "sessions": stats.get("total_sessions", 0),
            "pages": stats.get("total_pages", 0),
            "tests": stats.get("total_tests", 0),
            "tools_count": len(stats.get("tools_tested", {})),
            "locations_count": len(stats.get("locations_visited", {}))
        }
    })

@dashboard_bp.route('/api/refresh', methods=['POST'])
def refresh_stats():
    """تحديث الإحصائيات - إعادة تحميل الملف"""
    stats = load_stats()
    return jsonify({
        "status": "success",
        "message": "Stats refreshed",
        "total_sessions": stats.get("total_sessions", 0)
    })

@dashboard_bp.route('/api/locations')
def api_locations():
    """API للمواقع الجغرافية فقط"""
    stats = load_stats()
    locations = []
    for loc, count in stats.get("locations_visited", {}).items():
        lat, lon = get_location_coordinates(loc)
        if lat != 0 or lon != 0:
            locations.append({
                "name": loc,
                "lat": lat,
                "lon": lon,
                "count": count
            })
    return jsonify(locations)

@dashboard_bp.route('/api/tools')
def api_tools():
    """API للأدوات فقط"""
    stats = load_stats()
    tools = [{"name": name, "count": count}
             for name, count in stats.get("tools_tested", {}).items()]
    tools.sort(key=lambda x: x["count"], reverse=True)
    return jsonify(tools)

# ============================================================
# مزامنة الإحصائيات من GitHub Actions
# ============================================================
@dashboard_bp.route('/api/sync-stats', methods=['POST'])
def sync_stats():
    """
    استقبال الإحصائيات من GitHub Actions
    يستخدم هذا الـ endpoint لمزامنة البيانات من التشغيلات المتعددة
    """
    try:
        # التحقق من كلمة مرور بسيطة (للأمان)
        secret = request.headers.get('X-API-Key')
        if not secret or secret != SYNC_SECRET:
            return jsonify({"status": "error", "message": "Unauthorized"}), 401

        # الحصول على البيانات
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400

        # التحقق من صحة البيانات (وجود المفاتيح الأساسية)
        required_keys = ['total_runs', 'total_sessions', 'total_pages', 'total_tests', 'history']
        for key in required_keys:
            if key not in data:
                return jsonify({"status": "error", "message": f"Missing required key: {key}"}), 400

        # تحميل الإحصائيات الحالية
        current_stats = load_stats()

        # دمج البيانات (sync) بدلاً من الاستبدال الكامل
        # نضيف التشغيلات الجديدة فقط (حسب الطابع الزمني)
        new_history = data.get('history', [])
        existing_history = current_stats.get('history', [])

        # إنشاء مجموعة من التواقيت الموجودة
        existing_timestamps = {run.get('timestamp') for run in existing_history if run.get('timestamp')}

        # إضافة التشغيلات الجديدة فقط
        for run in new_history:
            if run.get('timestamp') not in existing_timestamps:
                existing_history.append(run)

        # ترتيب حسب التاريخ (الأحدث أولاً)
        existing_history.sort(key=lambda x: x.get('timestamp', ''), reverse=True)

        # الاحتفاظ بآخر 50 تشغيلة فقط
        if len(existing_history) > 50:
            existing_history = existing_history[:50]

        # دمج الإحصائيات الإجمالية
        merged_stats = {
            "total_runs": current_stats.get('total_runs', 0) + data.get('total_runs', 0),
            "total_sessions": current_stats.get('total_sessions', 0) + data.get('total_sessions', 0),
            "total_pages": current_stats.get('total_pages', 0) + data.get('total_pages', 0),
            "total_tests": current_stats.get('total_tests', 0) + data.get('total_tests', 0),
            "tools_tested": current_stats.get('tools_tested', {}).copy(),
            "locations_visited": current_stats.get('locations_visited', {}).copy(),
            "history": existing_history
        }

        # دمج الأدوات
        for tool, count in data.get('tools_tested', {}).items():
            merged_stats['tools_tested'][tool] = merged_stats['tools_tested'].get(tool, 0) + count

        # دمج المواقع
        for location, count in data.get('locations_visited', {}).items():
            merged_stats['locations_visited'][location] = merged_stats['locations_visited'].get(location, 0) + count

        # حفظ الإحصائيات المدمجة بشكل ذري
        if save_stats_atomic(merged_stats):
            return jsonify({
                "status": "success",
                "message": "Stats synced successfully",
                "merged": {
                    "total_sessions": merged_stats['total_sessions'],
                    "total_runs": merged_stats['total_runs'],
                    "new_sessions": data.get('total_sessions', 0)
                }
            })
        else:
            return jsonify({"status": "error", "message": "Failed to save stats"}), 500

    except json.JSONDecodeError as e:
        return jsonify({"status": "error", "message": f"Invalid JSON: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ============================================================
# Endpoint إضافي للحصول على حالة المزامنة
# ============================================================
@dashboard_bp.route('/api/sync-status', methods=['GET'])
def sync_status():
    """التحقق من حالة المزامنة وآخر تحديث"""
    stats = load_stats()
    last_sync = None

    # آخر تشغيلة في التاريخ
    history = stats.get('history', [])
    if history:
        last_run = history[0] if history else None
        if last_run:
            last_sync = last_run.get('timestamp')

    return jsonify({
        "status": "active",
        "secret_configured": bool(SYNC_SECRET and SYNC_SECRET != 'CyberShield_Secret_2026'),
        "total_sessions": stats.get('total_sessions', 0),
        "last_sync": last_sync,
        "history_count": len(history),
        "endpoints": {
            "sync": "/malek-dashboard/api/sync-stats (POST)",
            "stats": "/malek-dashboard/api/stats (GET)",
            "locations": "/malek-dashboard/api/locations (GET)",
            "tools": "/malek-dashboard/api/tools (GET)"
        }
    })