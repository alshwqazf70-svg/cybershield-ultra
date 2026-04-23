#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
====================================================================================================
|                                                                                                  |
|   🔥 CYBERSHIELD ULTIMATE OPTIMIZER v9.1.1 - ENTERPRISE GRADE 🔥                                 |
|                                                                                                  |
|   =============================================================================================  |
|   ✅ Security Hardened | ✅ Production Ready | ✅ Bug Fixed                                     |
|                                                                                                  |
====================================================================================================
"""

import os
import re
import json
import hashlib
import shutil
import gzip
import argparse
import time
import sys
import logging
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
from contextlib import contextmanager
import threading

# Optional imports with graceful fallback
try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False

try:
    from bs4 import BeautifulSoup
    BS4_AVAILABLE = True
except ImportError:
    BS4_AVAILABLE = False

try:
    import brotli
    BROTLI_AVAILABLE = True
except ImportError:
    BROTLI_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    from jsmin import jsmin
    JSMIN_AVAILABLE = True
except ImportError:
    JSMIN_AVAILABLE = False

try:
    import htmlmin
    HTMLMIN_AVAILABLE = True
except ImportError:
    HTMLMIN_AVAILABLE = False


# ==================================================================================================
# إعدادات التسجيل (Logging)
# ==================================================================================================

class ColoredFormatter(logging.Formatter):
    """منسق ألوان مخصص للـ logging"""
    COLORS = {
        'DEBUG': '\033[36m',
        'INFO': '\033[32m',
        'WARNING': '\033[33m',
        'ERROR': '\033[31m',
        'CRITICAL': '\033[35m',
        'RESET': '\033[0m'
    }

    def format(self, record):
        log_color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        record.levelname = f"{log_color}{record.levelname}{self.COLORS['RESET']}"
        return super().format(record)


def setup_logging(log_file: str = 'optimizer.log', level: int = logging.INFO) -> logging.Logger:
    """إعداد نظام التسجيل المتقدم"""
    logger = logging.getLogger("cybershield")
    logger.setLevel(level)

    if logger.handlers:
        logger.handlers.clear()

    # Handler للملف
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
    )
    file_handler.setFormatter(file_format)

    # Handler للكونسول مع ألوان
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_format = ColoredFormatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_format)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger


logger = setup_logging()


# ==================================================================================================
# إعدادات الأمان - محسّنة
# ==================================================================================================

@dataclass
class OptimizerConfig:
    """إعدادات المحسن"""
    base_dir: Path
    static_dir: Path
    templates_dir: Path
    backup_dir: Path
    optimized_dir: Path
    max_workers: int
    cdn_url: str
    dry_run: bool = False
    enable_avif: bool = True
    max_image_size_mb: int = 20


class PathValidator:
    """مدقق المسارات الأمني - محسّن"""

    # المسارات الممنوعة بشكل قاطع
    FORBIDDEN_PATTERNS = [
        '..', '~', '/etc', '/usr/bin', '/bin', '/sbin',
        '/root', '/boot', '/proc', '/sys', '/dev'
    ]

    def __init__(self, base_dir: Path):
        self.base_dir = base_dir.resolve()
        self.allowed_dirs = [
            self.base_dir,
            self.base_dir / "static",
            self.base_dir / "templates",
            self.base_dir / "optimized",
            self.base_dir / "backup"
        ]

    def is_safe_path(self, path: Union[str, Path]) -> bool:
        """التحقق من أن المسار آمن"""
        try:
            path_str = str(path)

            # التحقق من المسارات الممنوعة
            for forbidden in self.FORBIDDEN_PATTERNS:
                if forbidden in path_str:
                    return False

            # التحقق من أن المسار ضمن المسارات المسموح بها
            resolved = Path(path).resolve()

            # التحقق من أن المسار ضمن base_dir أو مجلداته الفرعية
            try:
                resolved.relative_to(self.base_dir)
                return True
            except ValueError:
                # المسار خارج base_dir، تحقق إضافي
                return any(
                    str(resolved).startswith(str(allowed_dir))
                    for allowed_dir in self.allowed_dirs
                )

        except Exception as e:
            logger.error(f"خطأ في التحقق من المسار {path}: {e}")
            return False

    def validate_file_operation(self, file_path: Union[str, Path], operation: str = 'read') -> bool:
        """التحقق من عملية الملف"""
        path_obj = Path(file_path)

        if not self.is_safe_path(file_path):
            logger.error(f"مسار غير آمن: {file_path}")
            return False

        # للقراءة: التحقق من وجود الملف
        if operation == 'read' and not path_obj.exists():
            logger.error(f"الملف غير موجود: {file_path}")
            return False

        # للكتابة: التحقق من وجود المجلد الأب
        if operation == 'write':
            parent = path_obj.parent
            if not parent.exists():
                try:
                    parent.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    logger.error(f"فشل إنشاء المجلد {parent}: {e}")
                    return False

        return True


# ==================================================================================================
# نظام النسخ الاحتياطي والاستعادة
# ==================================================================================================

class BackupManager:
    """مدير النسخ الاحتياطي"""

    def __init__(self, config: OptimizerConfig, validator: PathValidator):
        self.config = config
        self.validator = validator
        self.backup_manifest: Dict[str, str] = {}

    def create_backup(self) -> Optional[Path]:
        """إنشاء نسخة احتياطية آمنة"""
        if self.config.dry_run:
            logger.info("[DRY-RUN] سيتم إنشاء نسخة احتياطية")
            return None

        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_dir = self.config.base_dir / f"backup_{timestamp}"

            if not self.validator.is_safe_path(backup_dir):
                logger.error("مسار النسخ الاحتياطي غير آمن")
                return None

            backup_dir.mkdir(parents=True, exist_ok=True)

            items_to_backup = ['static', 'templates']

            for item in items_to_backup:
                src = self.config.base_dir / item
                if src.exists():
                    dst = backup_dir / item
                    if src.is_dir():
                        shutil.copytree(src, dst, dirs_exist_ok=True)
                    else:
                        shutil.copy2(src, dst)
                    self.backup_manifest[item] = str(dst)

            # حفظ manifest
            manifest_path = backup_dir / 'backup_manifest.json'
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(self.backup_manifest, f, indent=2)

            logger.info(f"✅ تم إنشاء نسخة احتياطية: {backup_dir}")
            return backup_dir

        except Exception as e:
            logger.error(f"فشل إنشاء النسخة الاحتياطية: {e}")
            return None

    def rollback(self, backup_dir: Path) -> bool:
        """استعادة النسخة الاحتياطية"""
        try:
            if not backup_dir.exists():
                logger.error(f"مجلد النسخة الاحتياطية غير موجود: {backup_dir}")
                return False

            manifest_path = backup_dir / 'backup_manifest.json'
            if manifest_path.exists():
                with open(manifest_path, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)

                for item, src_path in manifest.items():
                    dst = self.config.base_dir / item
                    if Path(src_path).exists():
                        if dst.exists():
                            if dst.is_dir():
                                shutil.rmtree(dst)
                            else:
                                dst.unlink()
                        if Path(src_path).is_dir():
                            shutil.copytree(src_path, dst)
                        else:
                            shutil.copy2(src_path, dst)

            logger.info("✅ تمت الاستعادة بنجاح")
            return True

        except Exception as e:
            logger.error(f"فشل الاستعادة: {e}")
            return False


# ==================================================================================================
# نظام الهاش والـ Cache
# ==================================================================================================

class CacheManager:
    """مدير الذاكرة المؤقتة والهاشات"""

    def __init__(self, cache_file: Path):
        self.cache_file = cache_file
        self.hashes: Dict[str, str] = {}
        self._lock = threading.Lock()
        self.load()

    def load(self):
        """تحميل الهاشات"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.hashes = json.load(f)
            except Exception as e:
                logger.warning(f"فشل تحميل ملف الكاش: {e}")
                self.hashes = {}

    def save(self):
        """حفظ الهاشات"""
        try:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.hashes, f, indent=2)
        except Exception as e:
            logger.error(f"فشل حفظ ملف الكاش: {e}")

    def get_file_hash(self, file_path: Path) -> str:
        """حساب هاش الملف"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"خطأ في حساب الهاش لـ {file_path}: {e}")
            return ""

    def needs_update(self, file_path: Path) -> Tuple[bool, str]:
        """التحقق من الحاجة للتحديث"""
        with self._lock:
            current_hash = self.get_file_hash(file_path)
            if not current_hash:
                return True, ""

            previous_hash = self.hashes.get(str(file_path), "")
            return current_hash != previous_hash, current_hash

    def update_hash(self, file_path: Path, file_hash: str):
        """تحديث الهاش"""
        with self._lock:
            self.hashes[str(file_path)] = file_hash


# ==================================================================================================
# معالجة CSS
# ==================================================================================================

class CSSProcessor:
    """معالج CSS"""

    def __init__(self, config: OptimizerConfig, validator: PathValidator, cache: CacheManager):
        self.config = config
        self.validator = validator
        self.cache = cache

    def minify_css(self, content: str) -> str:
        """ضغط CSS"""
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        content = re.sub(r'\n\s*', ' ', content)
        content = re.sub(r':\s+', ':', content)
        content = re.sub(r'\s+{', '{', content)
        content = re.sub(r'}\s+', '}', content)
        content = re.sub(r';\s+', ';', content)
        content = re.sub(r',\s+', ',', content)
        content = re.sub(r'\s+', ' ', content)
        return content.strip()

    def process_file(self, css_file: Path, cdn_mode: bool = False) -> Optional[Dict]:
        """معالجة ملف CSS واحد"""
        try:
            if not self.validator.validate_file_operation(css_file, 'read'):
                return None

            needs_update, current_hash = self.cache.needs_update(css_file)
            if not needs_update:
                logger.info(f"  ⏭️ {css_file.name} (لم يتغير)")
                return None

            with open(css_file, 'r', encoding='utf-8') as f:
                content = f.read()

            original_size = len(content)

            if cdn_mode and self.config.cdn_url:
                content = re.sub(
                    r'url\([\'"]?/static/',
                    f'url({self.config.cdn_url}/static/',
                    content
                )

            minified = self.minify_css(content)
            new_size = len(minified)

            self.cache.update_hash(css_file, current_hash)

            return {
                'name': css_file.name,
                'content': minified,
                'original_size': original_size,
                'new_size': new_size,
                'hash': current_hash
            }

        except Exception as e:
            logger.error(f"خطأ في معالجة {css_file}: {e}")
            return None

    def process_all(self, cdn_mode: bool = False) -> Dict[str, str]:
        """معالجة جميع ملفات CSS"""
        logger.info("🎨 معالجة ملفات CSS...")

        css_dir = self.config.static_dir / "css"
        if not css_dir.exists():
            logger.warning("⚠️ مجلد CSS غير موجود")
            return {}

        optimized_css_dir = self.config.optimized_dir / "css"
        optimized_css_dir.mkdir(parents=True, exist_ok=True)

        css_files = list(css_dir.glob("*.css"))
        results = {}

        if not css_files:
            logger.info("  ℹ️ لا توجد ملفات CSS")
            return results

        max_workers = min(self.config.max_workers, len(css_files))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {
                executor.submit(self.process_file, css_file, cdn_mode): css_file
                for css_file in css_files
            }

            for future in as_completed(future_to_file):
                result = future.result()
                if result:
                    output_path = optimized_css_dir / result['name']

                    if not self.config.dry_run:
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(result['content'])

                    saving = (1 - result['new_size']/result['original_size']) * 100
                    logger.info(f"  ✅ {result['name']}: {result['original_size']} → {result['new_size']} ({saving:.1f}%)")
                    results[result['name']] = result['name']

        return results


# ==================================================================================================
# معالجة JavaScript
# ==================================================================================================

class JSProcessor:
    """معالج JavaScript"""

    def __init__(self, config: OptimizerConfig, validator: PathValidator, cache: CacheManager):
        self.config = config
        self.validator = validator
        self.cache = cache

    def minify_js(self, content: str) -> str:
        """ضغط JavaScript"""
        if JSMIN_AVAILABLE:
            try:
                return jsmin(content)
            except Exception as e:
                logger.warning(f"jsmin فشل: {e}")

        # Fallback
        content = re.sub(r'(?<!:)//.*?$', '', content, flags=re.MULTILINE)
        content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
        content = re.sub(r'\n\s*', ' ', content)
        content = re.sub(r'\s+', ' ', content)
        return content.strip()

    def process_file(self, js_file: Path, cdn_mode: bool = False) -> Optional[Dict]:
        """معالجة ملف JS واحد"""
        try:
            if not self.validator.validate_file_operation(js_file, 'read'):
                return None

            needs_update, current_hash = self.cache.needs_update(js_file)
            if not needs_update:
                logger.info(f"  ⏭️ {js_file.name} (لم يتغير)")
                return None

            with open(js_file, 'r', encoding='utf-8') as f:
                content = f.read()

            original_size = len(content)
            minified = self.minify_js(content)
            new_size = len(minified)

            self.cache.update_hash(js_file, current_hash)

            return {
                'name': js_file.name,
                'content': minified,
                'original_size': original_size,
                'new_size': new_size,
                'hash': current_hash
            }

        except Exception as e:
            logger.error(f"خطأ في معالجة {js_file}: {e}")
            return None

    def process_all(self, cdn_mode: bool = False) -> Dict[str, str]:
        """معالجة جميع ملفات JS"""
        logger.info("📜 معالجة ملفات JavaScript...")

        js_dir = self.config.static_dir / "js"
        if not js_dir.exists():
            logger.warning("⚠️ مجلد JS غير موجود")
            return {}

        optimized_js_dir = self.config.optimized_dir / "js"
        optimized_js_dir.mkdir(parents=True, exist_ok=True)

        js_files = list(js_dir.glob("*.js"))
        results = {}

        if not js_files:
            logger.info("  ℹ️ لا توجد ملفات JS")
            return results

        max_workers = min(self.config.max_workers, len(js_files))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_file = {
                executor.submit(self.process_file, js_file, cdn_mode): js_file
                for js_file in js_files
            }

            for future in as_completed(future_to_file):
                result = future.result()
                if result:
                    output_path = optimized_js_dir / result['name']

                    if not self.config.dry_run:
                        with open(output_path, 'w', encoding='utf-8') as f:
                            f.write(result['content'])

                    saving = (1 - result['new_size']/result['original_size']) * 100
                    logger.info(f"  ✅ {result['name']}: {result['original_size']} → {result['new_size']} ({saving:.1f}%)")
                    results[result['name']] = result['name']

        return results


# ==================================================================================================
# معالجة الصور
# ==================================================================================================

class ImageProcessor:
    """معالج الصور"""

    SIZE_MAP = {"sm": 300, "md": 600, "lg": 1200, "xl": 1920}

    def __init__(self, config: OptimizerConfig, validator: PathValidator, cache: CacheManager):
        self.config = config
        self.validator = validator
        self.cache = cache

    def convert_to_webp(self, img_path: Path, output_dir: Path) -> Optional[Dict]:
        """تحويل صورة إلى WebP"""
        if not PIL_AVAILABLE:
            return None

        try:
            needs_update, current_hash = self.cache.needs_update(img_path)
            if not needs_update:
                logger.info(f"  ⏭️ {img_path.name} (لم يتغير)")
                return None

            results = []

            with Image.open(img_path) as img:
                # تحويل RGBA إلى RGB
                if img.mode in ('RGBA', 'LA', 'P'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background

                original_size = img_path.stat().st_size

                # WebP أصلي
                webp_path = output_dir / f"{img_path.stem}.webp"
                img.save(webp_path, 'WEBP', quality=85, optimize=True, method=6)
                webp_size = webp_path.stat().st_size
                results.append(('original', webp_path.name, 'webp'))

                # AVIF (اختياري)
                if self.config.enable_avif:
                    try:
                        avif_path = output_dir / f"{img_path.stem}.avif"
                        img.save(avif_path, 'AVIF', quality=80)
                        results.append(('original', avif_path.name, 'avif'))
                    except Exception as e:
                        logger.debug(f"AVIF غير مدعوم: {e}")

                # أحجام متعددة
                for size_name, size_width in self.SIZE_MAP.items():
                    if img.width > size_width:
                        ratio = size_width / img.width
                        new_height = int(img.height * ratio)

                        resized = img.resize((size_width, new_height), Image.LANCZOS)

                        # WebP resized
                        webp_resized = output_dir / f"{img_path.stem}-{size_name}.webp"
                        resized.save(webp_resized, 'WEBP', quality=85, optimize=True)
                        results.append((size_name, webp_resized.name, 'webp'))

                        # AVIF resized
                        if self.config.enable_avif:
                            try:
                                avif_resized = output_dir / f"{img_path.stem}-{size_name}.avif"
                                resized.save(avif_resized, 'AVIF', quality=80)
                                results.append((size_name, avif_resized.name, 'avif'))
                            except:
                                pass

                        resized.close()

                self.cache.update_hash(img_path, current_hash)

                saving = (1 - webp_size/original_size) * 100

                return {
                    'original': img_path.name,
                    'webp': webp_path.name,
                    'sizes': results,
                    'saving': saving,
                    'success': True
                }

        except Exception as e:
            logger.error(f"خطأ في تحويل {img_path}: {e}")
            return {'original': img_path.name, 'error': str(e), 'success': False}

    def process_all(self) -> List[Dict]:
        """معالجة جميع الصور"""
        logger.info("🖼️ معالجة الصور...")

        if not PIL_AVAILABLE:
            logger.warning("⚠️ PIL غير مثبت")
            return []

        images_dir = self.config.static_dir / "images"
        if not images_dir.exists():
            logger.warning("⚠️ مجلد الصور غير موجود")
            return []

        optimized_images_dir = self.config.optimized_dir / "images"
        optimized_images_dir.mkdir(parents=True, exist_ok=True)

        image_paths = []
        for ext in ['*.jpg', '*.jpeg', '*.png']:
            image_paths.extend(images_dir.glob(ext))

        if not image_paths:
            logger.info("  ℹ️ لا توجد صور للمعالجة")
            return []

        logger.info(f"  📊 {len(image_paths)} صورة للمعالجة")

        results = []
        max_workers = min(self.config.max_workers, len(image_paths))

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_path = {
                executor.submit(self.convert_to_webp, img_path, optimized_images_dir): img_path
                for img_path in image_paths
            }

            for future in as_completed(future_to_path):
                result = future.result()
                if result:
                    if result.get('success'):
                        logger.info(f"  ✅ {result['original']}: {result['saving']:.1f}% تحسين")
                        results.append(result)
                    else:
                        logger.warning(f"  ⚠️ فشل {result['original']}: {result.get('error', 'خطأ')}")

        return results


# ==================================================================================================
# معالجة HTML
# ==================================================================================================

class HTMLProcessor:
    """معالج HTML"""

    SIZE_MAP = {"sm": 300, "md": 600, "lg": 1200, "xl": 1920}

    def __init__(self, config: OptimizerConfig, validator: PathValidator, cache: CacheManager):
        self.config = config
        self.validator = validator
        self.cache = cache

    def is_jinja_template(self, content: str) -> bool:
        """التحقق من وجود Jinja syntax"""
        return '{%' in content or '{{' in content or '{#' in content

    def minify_html_safe(self, content: str) -> str:
        """ضغط HTML بأمان"""
        if self.is_jinja_template(content):
            content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
            content = re.sub(r'\n\s*\n', '\n', content)
            return content

        if HTMLMIN_AVAILABLE:
            try:
                return htmlmin.minify(content, remove_comments=True, remove_empty_space=True)
            except Exception as e:
                logger.warning(f"htmlmin فشل: {e}")

        content = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        content = re.sub(r'>\s+<', '><', content)
        content = re.sub(r'\s+', ' ', content)
        return content.strip()

    def detect_lcp_image(self, soup) -> Optional:
        """اكتشاف صورة LCP"""
        if not BS4_AVAILABLE:
            return None

        try:
            images = soup.find_all('img')
            if not images:
                return None

            for img in images:
                classes = img.get('class', [])
                src = img.get('src', '')

                if any(keyword in str(classes).lower() for keyword in ['hero', 'banner', 'main', 'featured']):
                    return img

                if any(keyword in src.lower() for keyword in ['hero', 'banner', 'logo']):
                    return img

            body = soup.find('body')
            if body:
                first_img = body.find('img')
                if first_img:
                    return first_img

            return images[0] if images else None

        except Exception as e:
            logger.warning(f"خطأ في اكتشاف LCP: {e}")
            return None

    def process_file(self, html_file: Path, cache_map: Dict[str, str],
                     webp_results: List[Dict], cdn_mode: bool = False) -> Optional[Dict]:
        """معالجة ملف HTML واحد"""
        try:
            if not self.validator.validate_file_operation(html_file, 'read'):
                return None

            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()

            content_hash = hashlib.md5(content.encode()).hexdigest()
            needs_update, _ = self.cache.needs_update(html_file)

            if not needs_update:
                logger.info(f"  ⏭️ {html_file.name} (لم يتغير)")
                return None

            is_jinja = self.is_jinja_template(content)

            if is_jinja:
                logger.info(f"  📝 {html_file.name} (Jinja)")

            modified = False

            if BS4_AVAILABLE and not is_jinja:
                soup = BeautifulSoup(content, 'lxml')

                # تحديث CSS
                for link in soup.find_all('link', rel='stylesheet'):
                    href = link.get('href', '')
                    if href:
                        filename = Path(href).name
                        if filename in cache_map:
                            new_href = href.replace(filename, cache_map[filename])
                            if cdn_mode and self.config.cdn_url:
                                new_href = new_href.replace('/static/', f'{self.config.cdn_url}/static/')
                            link['href'] = new_href
                            modified = True

                # تحديث JS
                for script in soup.find_all('script', src=True):
                    src = script.get('src', '')
                    if src:
                        filename = Path(src).name
                        if filename in cache_map:
                            new_src = src.replace(filename, cache_map[filename])
                            if cdn_mode and self.config.cdn_url:
                                new_src = new_src.replace('/static/', f'{self.config.cdn_url}/static/')
                            script['src'] = new_src
                            modified = True

                        if not script.get('defer') and not script.get('async'):
                            script['defer'] = True
                            modified = True

                # تحويل الصور
                webp_lookup = {w['original']: w for w in webp_results}

                for img in soup.find_all('img'):
                    src = img.get('src', '')
                    if not src:
                        continue

                    img_name = Path(src).name
                    if img_name in webp_lookup:
                        webp_info = webp_lookup[img_name]
                        picture = soup.new_tag('picture')

                        # AVIF sources
                        for size_name, size_file, fmt in webp_info.get('sizes', []):
                            if fmt == 'avif' and size_name in self.SIZE_MAP:
                                source = soup.new_tag('source')
                                source['srcset'] = src.replace(img_name, size_file)
                                source['media'] = f"(max-width: {self.SIZE_MAP[size_name]}px)"
                                source['type'] = 'image/avif'
                                picture.append(source)

                        # WebP sources
                        for size_name, size_file, fmt in webp_info.get('sizes', []):
                            if fmt == 'webp' and size_name in self.SIZE_MAP:
                                source = soup.new_tag('source')
                                source['srcset'] = src.replace(img_name, size_file)
                                source['media'] = f"(max-width: {self.SIZE_MAP[size_name]}px)"
                                source['type'] = 'image/webp'
                                picture.append(source)

                        # Default WebP
                        source = soup.new_tag('source')
                        source['srcset'] = src.replace(img_name, webp_info['webp'])
                        source['type'] = 'image/webp'
                        picture.append(source)

                        # Original img
                        img_copy = soup.new_tag('img')
                        for attr, value in img.attrs.items():
                            img_copy[attr] = value
                        picture.append(img_copy)

                        img.replace_with(picture)
                        modified = True

                # LCP Detection & Lazy Loading
                lcp_img = self.detect_lcp_image(soup)
                images = soup.find_all('img')

                for i, img in enumerate(images):
                    if lcp_img and img == lcp_img:
                        img['fetchpriority'] = 'high'
                        img['loading'] = 'eager'
                    else:
                        img['loading'] = 'lazy'

                    if not img.get('decoding'):
                        img['decoding'] = 'async'
                    modified = True

                # Preload LCP
                if lcp_img and lcp_img.get('src'):
                    preload = soup.new_tag('link', rel='preload', as_='image',
                                          href=lcp_img['src'], fetchpriority='high')
                    if soup.head:
                        soup.head.insert(0, preload)
                        modified = True

                if modified:
                    content = str(soup)

            minified = self.minify_html_safe(content)

            self.cache.update_hash(html_file, content_hash)

            return {
                'name': html_file.name,
                'content': minified,
                'modified': modified,
                'is_jinja': is_jinja
            }

        except Exception as e:
            logger.error(f"خطأ في معالجة {html_file}: {e}")
            return None

    def process_all(self, cache_map: Dict[str, str], webp_results: List[Dict],
                  cdn_mode: bool = False) -> Dict[str, str]:
        """معالجة جميع ملفات HTML"""
        logger.info("🌐 معالجة ملفات HTML...")

        templates_dir = self.config.templates_dir
        if not templates_dir.exists():
            logger.warning("⚠️ مجلد templates غير موجود")
            return {}

        optimized_templates_dir = self.config.optimized_dir / "templates"
        optimized_templates_dir.mkdir(parents=True, exist_ok=True)

        html_files = list(templates_dir.glob("*.html"))
        results = {}

        if not html_files:
            logger.info("  ℹ️ لا توجد ملفات HTML")
            return results

        for html_file in html_files:
            result = self.process_file(html_file, cache_map, webp_results, cdn_mode)
            if result:
                output_path = optimized_templates_dir / result['name']

                if not self.config.dry_run:
                    with open(output_path, 'w', encoding='utf-8') as f:
                        f.write(result['content'])

                status = "📝 Jinja" if result['is_jinja'] else ("✅" if result['modified'] else "⏭️")
                logger.info(f"  {status} {result['name']}")
                results[result['name']] = result['name']

        return results


# ==================================================================================================
# Cache Busting
# ==================================================================================================

class CacheBustingManager:
    """مدير Cache Busting"""

    def __init__(self, config: OptimizerConfig, validator: PathValidator):
        self.config = config
        self.validator = validator

    def add_cache_busting(self, css_map: Dict[str, str], js_map: Dict[str, str]) -> Dict[str, str]:
        """إضافة Cache Busting"""
        logger.info("🔗 إضافة Cache Busting...")

        cache_map = {}
        cache_map.update(css_map)
        cache_map.update(js_map)

        new_hashes = {}

        for old_name in list(cache_map.keys()):
            try:
                if old_name in css_map:
                    file_path = self.config.optimized_dir / "css" / old_name
                else:
                    file_path = self.config.optimized_dir / "js" / old_name

                if not file_path.exists():
                    continue

                with open(file_path, 'rb') as f:
                    content = f.read()

                file_hash = hashlib.md5(content).hexdigest()[:8]
                hashed_name = f"{Path(old_name).stem}.{file_hash}{Path(old_name).suffix}"
                new_path = file_path.parent / hashed_name

                if not self.config.dry_run:
                    shutil.move(file_path, new_path)

                cache_map[old_name] = hashed_name
                new_hashes[hashed_name] = file_hash

                logger.info(f"  ✅ {old_name} → {hashed_name}")

            except Exception as e:
                logger.error(f"خطأ في Cache Busting لـ {old_name}: {e}")
                continue

        manifest = {
            'version': datetime.now().isoformat(),
            'files': cache_map,
            'hashes': new_hashes,
            'cdn_url': self.config.cdn_url if self.config.cdn_url else None
        }

        manifest_path = self.config.optimized_dir / "manifest.json"
        if not self.config.dry_run:
            with open(manifest_path, 'w', encoding='utf-8') as f:
                json.dump(manifest, f, indent=2, ensure_ascii=False)

        logger.info(f"  ✅ Manifest محفوظ")
        return cache_map


# ==================================================================================================
# ضغط الملفات
# ==================================================================================================

class CompressionManager:
    """مدير الضغط"""

    def __init__(self, config: OptimizerConfig):
        self.config = config

    def compress_file(self, file_path: Path, output_dir: Path) -> bool:
        """ضغط ملف واحد"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()

            if BROTLI_AVAILABLE:
                try:
                    brotli_content = brotli.compress(content, quality=11)
                    brotli_path = output_dir / f"{file_path.name}.br"
                    if not self.config.dry_run:
                        with open(brotli_path, 'wb') as f:
                            f.write(brotli_content)
                except Exception as e:
                    logger.warning(f"فشل Brotli: {e}")

            try:
                gzip_content = gzip.compress(content, compresslevel=9)
                gzip_path = output_dir / f"{file_path.name}.gz"
                if not self.config.dry_run:
                    with open(gzip_path, 'wb') as f:
                        f.write(gzip_content)
            except Exception as e:
                logger.warning(f"فشل Gzip: {e}")

            return True

        except Exception as e:
            logger.error(f"خطأ في ضغط {file_path}: {e}")
            return False

    def compress_all(self):
        """ضغط جميع الملفات"""
        logger.info("🗜️ ضغط الملفات (Brotli/Gzip)...")

        compressed_dir = self.config.optimized_dir / "compressed"
        compressed_dir.mkdir(exist_ok=True)

        files_to_compress = []
        for ext in ['*.css', '*.js']:
            for folder in ['css', 'js']:
                files_to_compress.extend(self.config.optimized_dir.glob(f"{folder}/{ext}"))

        if not files_to_compress:
            logger.info("  ℹ️ لا توجد ملفات للضغط")
            return

        success_count = 0
        for file_path in files_to_compress:
            if self.compress_file(file_path, compressed_dir):
                success_count += 1
                logger.info(f"  ✅ {file_path.name}")

        logger.info(f"  📊 {success_count}/{len(files_to_compress)} ملف مضغوط")


# ==================================================================================================
# Watch Mode
# ==================================================================================================

class WatchModeManager:
    """مدير وضع المراقبة"""

    def __init__(self, optimize_func, config: OptimizerConfig):
        self.optimize_func = optimize_func
        self.config = config
        self.last_run = 0
        self.cooldown = 3
        self._lock = threading.Lock()

    def on_modified(self, event):
        """معالجة تعديل الملف"""
        if event.is_directory:
            return

        if "optimized" in event.src_path or "backup" in event.src_path:
            return

        if not any(event.src_path.endswith(ext) for ext in ['.css', '.js', '.html', '.jpg', '.png']):
            return

        with self._lock:
            now = time.time()
            if now - self.last_run < self.cooldown:
                return
            self.last_run = now

        logger.info(f"\n📁 تغيير: {event.src_path}")
        logger.info("🔄 إعادة التحسين...")

        try:
            self.optimize_func()
        except Exception as e:
            logger.error(f"خطأ في إعادة التحسين: {e}")

    def start(self):
        """بدء المراقبة"""
        if not WATCHDOG_AVAILABLE:
            logger.error("❌ مكتبة watchdog غير مثبتة")
            return

        logger.info("👁️ وضع المراقبة مفعل...")

        from watchdog.observers import Observer
        from watchdog.events import FileSystemEventHandler

        class EventHandler(FileSystemEventHandler):
            def __init__(self, callback):
                self.callback = callback

            def on_modified(self, event):
                self.callback(event)

        event_handler = EventHandler(self.on_modified)
        observer = Observer()

        observer.schedule(event_handler, str(self.config.static_dir), recursive=True)
        observer.schedule(event_handler, str(self.config.templates_dir), recursive=True)

        observer.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            observer.stop()
            logger.info("\n👋 تم إيقاف وضع المراقبة")

        observer.join()


# ==================================================================================================
# نظام التحقق من التكامل (Integrity Checker)
# ==================================================================================================

class IntegrityChecker:
    """التحقق من سلامة الملفات بعد التحسين"""

    def __init__(self, config: OptimizerConfig):
        self.config = config
        self.integrity_file = config.optimized_dir / "integrity.json"

    def generate_integrity_hashes(self) -> Dict[str, str]:
        """إنشاء هاشات التحقق من التكامل"""
        logger.info("🔒 إنشاء هاشات التحقق من التكامل...")

        integrity_data = {}

        for dir_name in ['css', 'js', 'images', 'templates']:
            search_dir = self.config.optimized_dir / dir_name
            if not search_dir.exists():
                continue

            for file_path in search_dir.rglob("*"):
                if file_path.is_file():
                    try:
                        with open(file_path, 'rb') as f:
                            file_hash = hashlib.sha256(f.read()).hexdigest()

                        rel_path = file_path.relative_to(self.config.optimized_dir)
                        integrity_data[str(rel_path)] = {
                            'hash': file_hash,
                            'size': file_path.stat().st_size,
                            'modified': datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                        }
                    except Exception as e:
                        logger.error(f"خطأ في حساب هاش {file_path}: {e}")

        # حفظ ملف التكامل
        if not self.config.dry_run:
            with open(self.integrity_file, 'w', encoding='utf-8') as f:
                json.dump(integrity_data, f, indent=2, ensure_ascii=False)

        logger.info(f"✅ تم إنشاء هاشات لـ {len(integrity_data)} ملف")
        return integrity_data

    def verify_integrity(self) -> bool:
        """التحقق من سلامة الملفات"""
        if not self.integrity_file.exists():
            logger.warning("⚠️ لا يوجد ملف تكامل للتحقق")
            return False

        try:
            with open(self.integrity_file, 'r', encoding='utf-8') as f:
                expected_hashes = json.load(f)

            all_valid = True

            for rel_path, expected_data in expected_hashes.items():
                file_path = self.config.optimized_dir / rel_path

                if not file_path.exists():
                    logger.error(f"❌ ملف مفقود: {rel_path}")
                    all_valid = False
                    continue

                with open(file_path, 'rb') as f:
                    current_hash = hashlib.sha256(f.read()).hexdigest()

                if current_hash != expected_data['hash']:
                    logger.error(f"❌ هاش غير متطابق: {rel_path}")
                    all_valid = False

            if all_valid:
                logger.info("✅ جميع الملفات سليمة")
            else:
                logger.warning("⚠️ تم اكتشاف مشاكل في التكامل")

            return all_valid

        except Exception as e:
            logger.error(f"خطأ في التحقق من التكامل: {e}")
            return False


# ==================================================================================================
# نظام التقارير والتحليلات
# ==================================================================================================

class ReportGenerator:
    """إنشاء تقارير التحسين"""

    def __init__(self, config: OptimizerConfig):
        self.config = config

    def generate_report(self, results: Dict) -> Path:
        """إنشاء تقرير مفصل"""
        report_dir = self.config.optimized_dir / "reports"
        report_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = report_dir / f"optimization_report_{timestamp}.html"

        total_savings = results.get('total_savings', 0)
        total_files = results.get('total_files', 0)

        html_content = f"""<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تقرير تحسين CyberShield</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 20px;
            color: #333;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }}
        .header h1 {{ font-size: 2.5em; margin-bottom: 10px; }}
        .header .date {{ opacity: 0.9; font-size: 0.9em; }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 40px;
            background: #f8f9fa;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
            margin: 10px 0;
        }}
        .stat-label {{ color: #666; font-size: 0.9em; }}
        .content {{ padding: 40px; }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 20px;
        }}
        th, td {{
            padding: 12px;
            text-align: right;
            border-bottom: 1px solid #ddd;
        }}
        th {{
            background: #667eea;
            color: white;
        }}
        tr:hover {{ background: #f5f5f5; }}
        .success {{ color: #28a745; font-weight: bold; }}
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔥 CyberShield Optimization Report</h1>
            <p class="date">تم الإنشاء: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-label">إجمالي الملفات</div>
                <div class="stat-number">{total_files}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">إجمالي التوفير</div>
                <div class="stat-number">{total_savings:.1f}%</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">حالة CDN</div>
                <div class="stat-number">{'مفعل' if self.config.cdn_url else 'غير مفعل'}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">وضع الإنتاج</div>
                <div class="stat-number">{'نشط' if hasattr(self.config, 'prod_mode') and self.config.prod_mode else 'غير نشط'}</div>
            </div>
        </div>

        <div class="content">
            <h2>📊 تفاصيل التحسين</h2>
            <table>
                <thead>
                    <tr><th>نوع الملف</th><th>عدد الملفات</th><th>حجم قبل (KB)</th><th>حجم بعد (KB)</th><th>نسبة التحسين</th></tr>
                </thead>
                <tbody>
                    {self._generate_table_rows(results)}
                </tbody>
            </table>
        </div>

        <div class="footer">
            <p>CyberShield Ultimate Optimizer v9.1.1 | Enterprise Grade Security</p>
        </div>
    </div>
</body>
</html>"""

        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(html_content)

        logger.info(f"📊 تم إنشاء التقرير: {report_file}")
        return report_file

    def _generate_table_rows(self, results: Dict) -> str:
        """إنشاء صفوف الجدول"""
        rows = ""
        for file_type, data in results.get('details', {}).items():
            rows += f"""
            <tr>
                <td>{file_type.upper()}</td>
                <td>{data.get('count', 0)}</td>
                <td>{data.get('original_size', 0):.2f}</td>
                <td>{data.get('new_size', 0):.2f}</td>
                <td class="success">{data.get('saving', 0):.1f}%</td>
            </tr>"""
        return rows


# ==================================================================================================
# التطبيق الرئيسي
# ==================================================================================================

class CyberShieldOptimizer:
    """التطبيق الرئيسي للمحسن"""

    def __init__(self, args):
        self.args = args
        self.config = self._setup_config()
        self.validator = PathValidator(self.config.base_dir)
        self.cache = CacheManager(self.config.optimized_dir / "file_hashes.json")
        self.backup_manager = BackupManager(self.config, self.validator)

        # Processors
        self.css_processor = CSSProcessor(self.config, self.validator, self.cache)
        self.js_processor = JSProcessor(self.config, self.validator, self.cache)
        self.image_processor = ImageProcessor(self.config, self.validator, self.cache)
        self.html_processor = HTMLProcessor(self.config, self.validator, self.cache)
        self.cache_busting = CacheBustingManager(self.config, self.validator)
        self.compression = CompressionManager(self.config)

        # Integrity and Reporting
        self.integrity_checker = IntegrityChecker(self.config)
        self.report_generator = ReportGenerator(self.config)

    def _setup_config(self) -> OptimizerConfig:
        """إعداد الإعدادات"""
        base_dir = Path("/home/CyberSecurityPro/cybershield-ultra-main")

        cpu_count = os.cpu_count() or 2
        max_workers = min(8, max(1, int(cpu_count * 0.75)))

        # إضافة prod_mode إلى config
        config = OptimizerConfig(
            base_dir=base_dir,
            static_dir=base_dir / "static",
            templates_dir=base_dir / "templates",
            backup_dir=base_dir / f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            optimized_dir=base_dir / "optimized",
            max_workers=max_workers,
            cdn_url=os.environ.get("CDN_URL", ""),
            dry_run=self.args.dry_run,
            enable_avif=not self.args.no_avif,
            max_image_size_mb=20
        )

        # إضافة prod_mode كـ attribute إضافي
        config.prod_mode = self.args.prod

        return config

    def _collect_results(self) -> Dict:
        """جمع نتائج التحسين"""
        results = {
            'total_files': 0,
            'total_savings': 0,
            'details': {}
        }

        # جمع إحصائيات من المجلدات المحسنة
        for dir_name in ['css', 'js', 'images', 'templates']:
            dir_path = self.config.optimized_dir / dir_name
            if dir_path.exists():
                files = list(dir_path.glob("*"))
                results['details'][dir_name] = {
                    'count': len(files),
                    'original_size': 0,
                    'new_size': 0,
                    'saving': 0
                }
                results['total_files'] += len(files)

        return results

    def run(self):
        """تشغيل المحسن"""
        logger.info("=" * 60)
        logger.info("🔥 CYBERSHIELD ULTIMATE OPTIMIZER v9.1.1 🔥")
        logger.info("✅ Enterprise Grade | Security Hardened | Production Ready")

        if self.config.dry_run:
            logger.info("🧪 DRY-RUN MODE: لا سيتم تطبيق أي تغييرات")

        logger.info("=" * 60)

        try:
            # نسخ احتياطي
            if not self.args.no_backup and not self.config.dry_run:
                backup_dir = self.backup_manager.create_backup()
                if not backup_dir and not self.args.force:
                    logger.error("❌ فشل إنشاء النسخة الاحتياطية")
                    return

            # معالجة الملفات
            css_map = self.css_processor.process_all(self.args.cdn)
            js_map = self.js_processor.process_all(self.args.cdn)
            webp_results = self.image_processor.process_all()

            # Cache Busting
            cache_map = self.cache_busting.add_cache_busting(css_map, js_map)

            # معالجة HTML
            html_map = self.html_processor.process_all(cache_map, webp_results, self.args.cdn)

            # ضغط الملفات
            if self.args.prod:
                self.compression.compress_all()

            # حفظ الكاش
            self.cache.save()

            # تطبيق التحسينات
            if self.args.apply:
                self._apply_optimizations()

            logger.info("\n" + "=" * 60)
            logger.info("✅ تم الانتهاء بنجاح!")
            logger.info(f"📁 الملفات المحسنة: {self.config.optimized_dir}")

            if self.config.dry_run:
                logger.info("🧪 كان هذا تشغيل تجريبي (dry-run)")

        except Exception as e:
            logger.error(f"❌ خطأ: {e}")
            logger.exception("تفاصيل:")

    def _apply_optimizations(self):
        """تطبيق التحسينات"""
        logger.info("🚀 تطبيق التحسينات...")

        if self.config.dry_run:
            logger.info("[DRY-RUN] سيتم تطبيق التحسينات التالية:")
            logger.info(f"  - نسخ الملفات من {self.config.optimized_dir} إلى {self.config.base_dir}")
            return

        try:
            # نسخ الملفات المحسنة إلى المجلدات الأصلية
            optimized_dirs = ['css', 'js', 'images', 'templates']

            for dir_name in optimized_dirs:
                source_dir = self.config.optimized_dir / dir_name
                if not source_dir.exists():
                    continue

                # تحديد المجلد الهدف
                if dir_name == 'templates':
                    target_dir = self.config.templates_dir
                else:
                    target_dir = self.config.static_dir / dir_name

                # إنشاء نسخة احتياطية سريعة قبل الاستبدال
                backup_subdir = self.config.backup_dir / f"pre_apply_{dir_name}"
                if target_dir.exists():
                    shutil.copytree(target_dir, backup_subdir, dirs_exist_ok=True)
                    logger.info(f"  📦 نسخ احتياطي لـ {dir_name} إلى {backup_subdir}")

                # نسخ الملفات الجديدة
                for file_path in source_dir.glob("*"):
                    if file_path.is_file():
                        shutil.copy2(file_path, target_dir / file_path.name)
                        logger.info(f"  ✅ تم تحديث: {file_path.name}")

            # تحديث ملف manifest في المجلد الرئيسي
            manifest_src = self.config.optimized_dir / "manifest.json"
            if manifest_src.exists():
                shutil.copy2(manifest_src, self.config.base_dir / "manifest.json")
                logger.info("  ✅ تم تحديث manifest.json")

            logger.info("✅ تم تطبيق جميع التحسينات بنجاح!")

        except Exception as e:
            logger.error(f"❌ فشل تطبيق التحسينات: {e}")
            logger.info("🔄 محاولة الاستعادة من النسخة الاحتياطية...")

            # محاولة الاستعادة من آخر نسخة احتياطية
            backups = sorted(self.config.base_dir.glob("backup_*"))
            if backups:
                latest_backup = backups[-1]
                if self.backup_manager.rollback(latest_backup):
                    logger.info("✅ تمت الاستعادة بنجاح")
                else:
                    logger.error("❌ فشلت الاستعادة - الرجاء التدخل يدوياً")
            else:
                logger.error("❌ لا توجد نسخة احتياطية للاستعادة")

    def run_with_integrity(self):
        """تشغيل المحسن مع التحقق من التكامل"""
        self.run()

        # التحقق من التكامل بعد التحسين
        if not self.config.dry_run:
            self.integrity_checker.generate_integrity_hashes()

            if self.args.verify:
                self.integrity_checker.verify_integrity()

        # إنشاء التقرير
        results = self._collect_results()
        self.report_generator.generate_report(results)


# ==================================================================================================
# واجهة سطر الأوامر الرئيسية
# ==================================================================================================

def parse_arguments():
    """تحليل معاملات سطر الأوامر"""
    parser = argparse.ArgumentParser(
        description="CyberShield Ultimate Optimizer - تحسين أداء وأمان التطبيقات",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
أمثلة الاستخدام:
  %(prog)s                     # تشغيل عادي
  %(prog)s --dry-run          # وضع تجريبي بدون تطبيق تغييرات
  %(prog)s --cdn              # تفعيل وضع CDN
  %(prog)s --prod             # وضع الإنتاج (تفعيل الضغط)
  %(prog)s --apply            # تطبيق التحسينات تلقائياً
  %(prog)s --watch            # مراقبة التغييرات وتحسين تلقائي
  %(prog)s --verify           # التحقق من تكامل الملفات
  %(prog)s --no-avif          # تعطيل تنسيق AVIF
  %(prog)s --no-backup        # تعطيل النسخ الاحتياطي
        """
    )

    parser.add_argument('--dry-run', action='store_true', help='وضع التجربة (لا تطبيق تغييرات)')
    parser.add_argument('--cdn', action='store_true', help='تفعيل وضع CDN')
    parser.add_argument('--prod', action='store_true', help='وضع الإنتاج (تفعيل الضغط)')
    parser.add_argument('--apply', action='store_true', help='تطبيق التحسينات تلقائياً')
    parser.add_argument('--watch', action='store_true', help='مراقبة التغييرات')
    parser.add_argument('--verify', action='store_true', help='التحقق من تكامل الملفات')
    parser.add_argument('--no-avif', action='store_true', help='تعطيل تنسيق AVIF')
    parser.add_argument('--no-backup', action='store_true', help='تعطيل النسخ الاحتياطي')
    parser.add_argument('--force', action='store_true', help='تجاوز التحذيرات')

    return parser.parse_args()


def main():
    """الدالة الرئيسية"""
    args = parse_arguments()

    # عرض معلومات النظام
    logger.info("🖥️ معلومات النظام:")
    logger.info(f"  - Python: {sys.version}")
    logger.info(f"  - CPU Cores: {os.cpu_count()}")
    logger.info(f"  - Platform: {sys.platform}")

    # إنشاء وتشغيل المحسن
    optimizer = CyberShieldOptimizer(args)

    if args.watch:
        # وضع المراقبة
        watch_manager = WatchModeManager(optimizer.run, optimizer.config)
        watch_manager.start()
    else:
        # التشغيل العادي مع التحقق من التكامل
        optimizer.run()


if __name__ == "__main__":
        main()
