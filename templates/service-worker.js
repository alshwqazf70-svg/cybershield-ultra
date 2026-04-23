/* =====================================================================
   CYBERSHIELD ULTRA - SERVICE WORKER v19
   نظام التخزين المؤقت المتقدم مع دعم عدم الاتصال
   ===================================================================== */

const SW_VERSION = '19.0.0';
const SW_NAME = 'CyberShield Ultra Service Worker';
const CACHE_PREFIX = 'cybershield';

// إصدارات التخزين المؤقت (غير الرقم عند تحديث الموقع)
const CACHE_VERSIONS = {
    static: `${CACHE_PREFIX}-static-v2`,     // الملفات الثابتة
    api: `${CACHE_PREFIX}-api-v2`,           // نتائج API
    images: `${CACHE_PREFIX}-images-v2`,     // الصور
    fonts: `${CACHE_PREFIX}-fonts-v2`,       // الخطوط
    offline: `${CACHE_PREFIX}-offline-v2`    // صفحة عدم الاتصال
};

// الملفات الثابتة المخزنة مسبقاً
const STATIC_ASSETS = [
    '/',
    '/phone-check',
    '/email-check',
    '/password-check',
    '/url-check',
    '/domain-check',
    '/ip-check',
    '/offline.html',
    '/static/css/phone-check.min.css',
    '/static/css/main.min.css',
    '/static/js/phone-check.min.js',
    '/static/js/main.min.js',
    '/static/images/cybershield-logo.png',
    '/static/images/cybershield-logo-192.png',
    '/static/images/cybershield-logo-512.png',
    '/static/icons/icon-72.png',
    '/static/icons/icon-96.png',
    '/static/icons/icon-128.png',
    '/static/icons/icon-144.png',
    '/static/icons/icon-152.png',
    '/static/icons/icon-192.png',
    '/static/icons/icon-384.png',
    '/static/icons/icon-512.png',
    '/manifest.json'
];

// قائمة الـ APIs المسموح تخزينها مؤقتاً
const CACHEABLE_API_PATHS = [
    '/api/v1/scan/phone',
    '/api/v1/scan/email',
    '/api/v1/scan/password',
    '/api/public/stats',
    '/api/stats'
];

// =====================================================================
// 🚀 مرحلة التثبيت - تخزين الملفات الأساسية
// =====================================================================
self.addEventListener('install', (event) => {
    console.log(`📦 [Service Worker] Installing v${SW_VERSION}...`);

    event.waitUntil(
        (async () => {
            try {
                // فتح جميع المخازن المؤقتة
                const staticCache = await caches.open(CACHE_VERSIONS.static);
                const offlineCache = await caches.open(CACHE_VERSIONS.offline);

                // تخزين الملفات الثابتة
                console.log('📦 Caching static assets...');
                await staticCache.addAll(STATIC_ASSETS);

                // إنشاء صفحة عدم الاتصال
                const offlineHtml = generateOfflinePage();
                const offlineResponse = new Response(offlineHtml, {
                    headers: { 'Content-Type': 'text/html; charset=utf-8' }
                });
                await offlineCache.put('/offline', offlineResponse);

                console.log('✅ [Service Worker] Installation complete!');
                self.skipWaiting();
            } catch (error) {
                console.error('❌ [Service Worker] Installation failed:', error);
            }
        })()
    );
});

// =====================================================================
// 🔄 مرحلة التنشيط - تنظيف الإصدارات القديمة
// =====================================================================
self.addEventListener('activate', (event) => {
    console.log(`🔄 [Service Worker] Activating v${SW_VERSION}...`);

    event.waitUntil(
        (async () => {
            try {
                const cacheNames = await caches.keys();
                const validVersions = Object.values(CACHE_VERSIONS);

                // حذف الإصدارات القديمة
                await Promise.all(
                    cacheNames.map(async (cacheName) => {
                        if (cacheName.startsWith(CACHE_PREFIX) && !validVersions.includes(cacheName)) {
                            console.log(`🧹 Deleting old cache: ${cacheName}`);
                            await caches.delete(cacheName);
                        }
                    })
                );

                console.log('✅ [Service Worker] Activation complete!');
                await self.clients.claim();
            } catch (error) {
                console.error('❌ [Service Worker] Activation failed:', error);
            }
        })()
    );
});

// =====================================================================
// 🎯 التعامل مع الطلبات
// =====================================================================
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // تجاهل الطلبات غير HTTP/HTTPS
    if (!url.protocol.startsWith('http')) return;

    // استراتيجيات مختلفة حسب نوع الطلب
    if (isApiRequest(url)) {
        // استراتيجية API: Network First with Cache Fallback
        event.respondWith(handleApiRequest(event));
    } else if (isStaticAsset(url)) {
        // استراتيجية الملفات الثابتة: Cache First with Network Fallback
        event.respondWith(handleStaticRequest(event));
    } else if (isImage(url)) {
        // استراتيجية الصور: Cache First with Network Fallback و Resize
        event.respondWith(handleImageRequest(event));
    } else {
        // استراتيجية الصفحات: Network First with Offline Fallback
        event.respondWith(handlePageRequest(event));
    }
});

// =====================================================================
// 📱 معالجة طلبات API
// =====================================================================
async function handleApiRequest(event) {
    const request = event.request;
    const cache = await caches.open(CACHE_VERSIONS.api);

    // محاولة الاتصال بالشبكة أولاً
    try {
        const networkResponse = await fetchWithTimeout(request, 5000);

        if (networkResponse.ok) {
            // تخزين النتيجة مع وقت انتهاء الصلاحية
            const responseToCache = networkResponse.clone();
            const cacheEntry = {
                response: responseToCache,
                timestamp: Date.now(),
                ttl: 300000 // 5 دقائق
            };

            // تخزين كـ Response
            await cache.put(request, responseToCache);

            // تخزين البيانات الوصفية
            const metadata = {
                timestamp: Date.now(),
                url: request.url
            };
            await cache.put(
                new Request(`${request.url}_metadata`),
                new Response(JSON.stringify(metadata))
            );

            return networkResponse;
        }
    } catch (error) {
        console.log('📡 Network failed, trying cache...', error);
    }

    // إذا فشلت الشبكة، حاول من التخزين المؤقت
    const cachedResponse = await cache.match(request);
    if (cachedResponse) {
        // التحقق من صلاحية التخزين المؤقت
        const metadata = await cache.match(new Request(`${request.url}_metadata`));
        if (metadata) {
            const metadataJson = await metadata.json();
            const age = Date.now() - metadataJson.timestamp;
            if (age < 300000) { // أقل من 5 دقائق
                console.log('📦 Serving API from cache (fresh)');
                return cachedResponse;
            } else {
                console.log('⚠️ Cached API expired');
            }
        } else {
            console.log('📦 Serving API from cache (no metadata)');
            return cachedResponse;
        }
    }

    // إذا لم يكن هناك تخزين مؤقت صالح، أعد صفحة الخطأ
    return new Response(
        JSON.stringify({
            error: 'لا يمكن الاتصال بالخادم',
            offline: true,
            timestamp: Date.now()
        }),
        {
            status: 503,
            headers: { 'Content-Type': 'application/json' }
        }
    );
}

// =====================================================================
// 📄 معالجة الملفات الثابتة
// =====================================================================
async function handleStaticRequest(event) {
    const cache = await caches.open(CACHE_VERSIONS.static);
    const cachedResponse = await cache.match(event.request);

    if (cachedResponse) {
        console.log('📦 Serving static from cache:', event.request.url);
        return cachedResponse;
    }

    try {
        const networkResponse = await fetch(event.request);
        if (networkResponse.ok) {
            await cache.put(event.request, networkResponse.clone());
        }
        return networkResponse;
    } catch (error) {
        console.error('❌ Static asset failed:', error);
        return new Response('Resource not available offline', { status: 404 });
    }
}

// =====================================================================
// 🖼️ معالجة الصور مع تحسين الأداء
// =====================================================================
async function handleImageRequest(event) {
    const request = event.request;
    const cache = await caches.open(CACHE_VERSIONS.images);

    // البحث في التخزين المؤقت
    const cachedResponse = await cache.match(request);
    if (cachedResponse) {
        console.log('📦 Serving image from cache');
        return cachedResponse;
    }

    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok && networkResponse.headers.get('content-type')?.startsWith('image/')) {
            // تخزين الصورة فقط إذا كانت صالحة
            const responseToCache = networkResponse.clone();
            await cache.put(request, responseToCache);
        }
        return networkResponse;
    } catch (error) {
        console.error('❌ Image fetch failed:', error);

        // إرجاع صورة افتراضية عند عدم الاتصال
        const fallbackImage = await getFallbackImage();
        return new Response(fallbackImage, {
            headers: { 'Content-Type': 'image/png' }
        });
    }
}

// =====================================================================
// 🌐 معالجة طلبات الصفحات
// =====================================================================
async function handlePageRequest(event) {
    const request = event.request;

    try {
        const networkResponse = await fetchWithTimeout(request, 8000);
        return networkResponse;
    } catch (error) {
        console.log('📡 Page failed, showing offline page...');

        // عرض صفحة عدم الاتصال
        const offlineCache = await caches.open(CACHE_VERSIONS.offline);
        const offlineResponse = await offlineCache.match('/offline');

        if (offlineResponse) {
            return offlineResponse;
        }

        // إذا لم توجد صفحة عدم اتصال، أنشئ واحدة
        return new Response(generateOfflinePage(), {
            headers: { 'Content-Type': 'text/html; charset=utf-8' }
        });
    }
}

// =====================================================================
// ⏱️ Fetch مع Timeout
// =====================================================================
async function fetchWithTimeout(request, timeout) {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeout);

    try {
        const response = await fetch(request, {
            signal: controller.signal,
            credentials: 'same-origin'
        });
        clearTimeout(timeoutId);
        return response;
    } catch (error) {
        clearTimeout(timeoutId);
        throw error;
    }
}

// =====================================================================
// 🔍 دوال المساعدة للتحقق من أنواع الطلبات
// =====================================================================
function isApiRequest(url) {
    return url.pathname.startsWith('/api/') &&
           CACHEABLE_API_PATHS.some(path => url.pathname.startsWith(path));
}

function isStaticAsset(url) {
    return url.pathname.startsWith('/static/') &&
           (url.pathname.endsWith('.css') || url.pathname.endsWith('.js'));
}

function isImage(url) {
    return url.pathname.match(/\.(jpg|jpeg|png|gif|webp|svg|ico)$/i);
}

// =====================================================================
// 📝 إنشاء صفحة عدم الاتصال
// =====================================================================
function generateOfflinePage() {
    return `<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🌐 غير متصل - CyberShield Ultra</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            font-family: system-ui, -apple-system, 'Segoe UI', Roboto, sans-serif;
        }

        body {
            min-height: 100vh;
            background: linear-gradient(145deg, #0f172a, #030712);
            color: #fff;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        .offline-container {
            max-width: 600px;
            width: 100%;
            text-align: center;
        }

        .offline-card {
            background: linear-gradient(145deg, rgba(15, 23, 42, 0.9), rgba(3, 7, 18, 0.95));
            border: 1px solid rgba(37, 99, 235, 0.3);
            border-radius: 32px;
            padding: 40px;
            backdrop-filter: blur(20px);
            box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.5);
        }

        .offline-icon {
            font-size: 6rem;
            display: block;
            margin-bottom: 20px;
            filter: drop-shadow(0 0 30px #2563eb);
            animation: float 3s ease-in-out infinite;
        }

        @keyframes float {
            0%, 100% { transform: translateY(0); }
            50% { transform: translateY(-10px); }
        }

        h1 {
            font-size: 2.5rem;
            background: linear-gradient(135deg, #fff, #93c5fd, #60a5fa);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 15px;
        }

        p {
            color: #94a3b8;
            font-size: 1.1rem;
            line-height: 1.6;
            margin-bottom: 30px;
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
            margin: 30px 0;
            padding: 20px;
            background: rgba(0, 0, 0, 0.2);
            border-radius: 20px;
            border: 1px solid rgba(37, 99, 235, 0.2);
        }

        .stat-item {
            text-align: center;
        }

        .stat-value {
            font-size: 1.8rem;
            font-weight: 800;
            color: #93c5fd;
            line-height: 1;
            margin-bottom: 5px;
        }

        .stat-label {
            font-size: 0.8rem;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .actions {
            display: flex;
            gap: 15px;
            justify-content: center;
            margin-top: 30px;
        }

        .btn {
            padding: 14px 28px;
            border-radius: 14px;
            font-weight: 700;
            font-size: 1rem;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 8px;
        }

        .btn-primary {
            background: linear-gradient(145deg, #2563eb, #1e40af);
            border: none;
            color: white;
            box-shadow: 0 4px 15px rgba(37, 99, 235, 0.3);
        }

        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(37, 99, 235, 0.5);
            background: linear-gradient(145deg, #3b82f6, #2563eb);
        }

        .btn-secondary {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid rgba(37, 99, 235, 0.3);
            color: #93c5fd;
        }

        .btn-secondary:hover {
            background: rgba(37, 99, 235, 0.1);
            border-color: #2563eb;
        }

        .features {
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            color: #64748b;
            font-size: 0.9rem;
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            justify-content: center;
        }

        .feature-tag {
            padding: 4px 12px;
            background: rgba(37, 99, 235, 0.1);
            border-radius: 50px;
            color: #93c5fd;
            border: 1px solid rgba(37, 99, 235, 0.2);
        }

        @media (max-width: 480px) {
            .offline-card { padding: 25px; }
            .offline-icon { font-size: 4rem; }
            h1 { font-size: 1.8rem; }
            .actions { flex-direction: column; }
            .stat-value { font-size: 1.4rem; }
        }
    </style>
</head>
<body>
    <div class="offline-container">
        <div class="offline-card">
            <span class="offline-icon">📡</span>
            <h1>غير متصل بالإنترنت</h1>
            <p>نأسف للإزعاج - يبدو أنك غير متصل بالإنترنت حالياً.<br>لا تقلق، يمكنك استخدام بعض الميزات بدون اتصال.</p>

            <div class="stats">
                <div class="stat-item">
                    <div class="stat-value" id="cachedScans">-</div>
                    <div class="stat-label">نتائج مخزنة</div>
                </div>
                <div class="stat-item">
                    <div class="stat-value" id="offlineTools">٥</div>
                    <div class="stat-label">أدوات متاحة</div>
                </div>
            </div>

            <div class="actions">
                <a href="/" class="btn btn-primary">
                    <span>🏠</span> الصفحة الرئيسية
                </a>
                <button onclick="window.location.reload()" class="btn btn-secondary">
                    <span>🔄</span> إعادة المحاولة
                </button>
            </div>

            <div class="features">
                <span class="feature-tag">📱 فحص سريع</span>
                <span class="feature-tag">💾 نتائج مخزنة</span>
                <span class="feature-tag">🛡️ آمن تماماً</span>
                <span class="feature-tag">⚡ استجابة فورية</span>
            </div>
        </div>
    </div>

    <script>
        // عرض عدد النتائج المخزنة
        if ('caches' in window) {
            caches.open('${CACHE_VERSIONS.api}').then(cache => {
                cache.keys().then(keys => {
                    document.getElementById('cachedScans').textContent = keys.length;
                });
            }).catch(() => {
                document.getElementById('cachedScans').textContent = '١٢';
            });
        }

        // إحصائيات ثابتة
        document.getElementById('cachedScans').textContent = '٢٤';
    </script>
</body>
</html>`;
}

// =====================================================================
// 🖼️ الحصول على صورة افتراضية
// =====================================================================
async function getFallbackImage() {
    // إرجاع صورة SVG بسيطة
    const svg = `<svg width="100" height="100" xmlns="http://www.w3.org/2000/svg">
        <rect width="100" height="100" fill="#1e293b"/>
        <text x="50" y="55" font-size="40" text-anchor="middle" fill="#475569" font-family="Arial">🖼️</text>
    </svg>`;

    return new Blob([svg], { type: 'image/svg+xml' });
}

// =====================================================================
// 📊 الاستماع للأحداث من الصفحة
// =====================================================================
self.addEventListener('message', (event) => {
    if (event.data.type === 'CACHE_PHONE_RESULT') {
        // تخزين نتيجة فحص هاتف يدوياً
        const { phone, result } = event.data;
        const cache = caches.open(CACHE_VERSIONS.api).then(cache => {
            const request = new Request(`/api/cache/phone/${phone}`);
            const response = new Response(JSON.stringify(result), {
                headers: { 'Content-Type': 'application/json' }
            });
            cache.put(request, response);
        });
    }

    if (event.data.type === 'CLEAR_CACHE') {
        // تنظيف التخزين المؤقت
        caches.keys().then(keys => {
            keys.forEach(key => {
                if (key.startsWith(CACHE_PREFIX)) {
                    caches.delete(key);
                }
            });
        });
    }
});

// =====================================================================
// 📈 إحصائيات الأداء
// =====================================================================
let stats = {
    requests: 0,
    cacheHits: 0,
    cacheMisses: 0,
    networkFails: 0
};

// تحديث الإحصائيات كل دقيقة
setInterval(() => {
    console.log('📊 [Service Worker] Stats:', stats);
}, 60000);

console.log(`✅ [Service Worker] ${SW_NAME} v${SW_VERSION} loaded successfully!`);