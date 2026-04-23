#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
from pathlib import Path
from typing import Dict, Any

class ConfigLoader:
    """تحميل وإدارة الإعدادات من config.json"""

    def __init__(self, config_path: Path = None):
        if config_path is None:
            config_path = Path(__file__).parent / "config.json"

        self.config_path = config_path
        self.config = self._load_config()
        self._validate_config()

    def _load_config(self) -> Dict[str, Any]:
        """تحميل الإعدادات من الملف"""
        if not self.config_path.exists():
            print(f"⚠️ ملف {self.config_path} غير موجود، استخدام الإعدادات الافتراضية")
            return self._get_default_config()

        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ خطأ في تحميل الإعدادات: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """الإعدادات الافتراضية"""
        return {
            "site": {
                "base_url": "https://cybersecuritypro.pythonanywhere.com",
                "name_ar": "درع الأمن السيبراني الأسطوري"
            },
            "apis": {
                "serpapi": {"enabled": False, "api_key": ""},
                "google_indexing": {"enabled": True}
            },
            "scheduling": {
                "daily_publish": {"enabled": True, "time": "08:00"},
                "weekly_optimization": {"enabled": True, "day": "sunday", "time": "03:00"}
            },
            "content": {
                "target_word_count": 2500,
                "min_word_count": 1800,
                "max_word_count": 3500
            },
            "seo": {
                "competitor_analysis": {"enabled": True},
                "internal_links": {"max_links": 8}
            }
        }

    def _validate_config(self):
        """التحقق من صحة الإعدادات"""
        # التحقق من وجود SerpAPI key
        if self.config.get('apis', {}).get('serpapi', {}).get('enabled', False):
            api_key = self.config['apis']['serpapi'].get('api_key', '')
            if not api_key or api_key == "":
                print("⚠️ تحذير: SerpAPI مفعل ولكن لا يوجد مفتاح API")
                print("   أضف مفتاح API في config.json تحت apis.serpapi.api_key")
                print("   احصل على مفتاح من: https://serpapi.com")

        # التحقق من وجود Google Credentials
        if self.config.get('apis', {}).get('google_indexing', {}).get('enabled', False):
            cred_file = self.config['apis']['google_indexing'].get('service_account_file', 'google_credentials.json')
            cred_path = Path(__file__).parent / cred_file
            if not cred_path.exists():
                print(f"⚠️ تحذير: Google Indexing مفعل ولكن ملف {cred_file} غير موجود")

    def get_serpapi_key(self) -> str:
        """الحصول على مفتاح SerpAPI"""
        return self.config.get('apis', {}).get('serpapi', {}).get('api_key', '')

    def is_serpapi_enabled(self) -> bool:
        """هل SerpAPI مفعل؟"""
        return self.config.get('apis', {}).get('serpapi', {}).get('enabled', False)

    def get_site_url(self) -> str:
        """الحصول على رابط الموقع"""
        return self.config.get('site', {}).get('base_url', 'https://cybersecuritypro.pythonanywhere.com')

    def get_publish_time(self) -> str:
        """وقت النشر اليومي"""
        return self.config.get('scheduling', {}).get('daily_publish', {}).get('time', '08:00')

    def get_target_word_count(self) -> int:
        """عدد الكلمات المستهدف"""
        return self.config.get('content', {}).get('target_word_count', 2500)

    def is_competitor_analysis_enabled(self) -> bool:
        """هل تحليل المنافسين مفعل؟"""
        return self.config.get('seo', {}).get('competitor_analysis', {}).get('enabled', True)

    def get_max_internal_links(self) -> int:
        """الحد الأقصى للروابط الداخلية"""
        return self.config.get('seo', {}).get('internal_links', {}).get('max_links', 8)

    def get_site_name_ar(self) -> str:
        """اسم الموقع بالعربية"""
        return self.config.get('site', {}).get('name_ar', 'درع الأمن السيبراني الأسطوري')


# إنشاء كائن الإعدادات العالمي
config = ConfigLoader()
