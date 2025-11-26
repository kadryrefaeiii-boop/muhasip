#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Language Manager
Dynamic language switching and RTL support
"""

import logging
import json
import os
from typing import Dict, Any, Optional
import locale
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class LanguageManager:
    """Dynamic language switching and RTL support"""

    def __init__(self):
        """Initialize Language Manager"""
        self.current_language = "ar"
        self.translations = {}
        self.fallback_language = "en"
        self.supported_languages = {
            "ar": {"name": "العربية", "direction": "rtl", "display_name": "Arabic"},
            "en": {"name": "English", "direction": "ltr", "display_name": "English"}
        }
        self.language_dir = "lang"

        # Load default language
        self.load_language(self.current_language)

        logger.info(f"Language Manager initialized with language: {self.current_language}")

    def load_language(self, language_code: str) -> bool:
        """
        Load language translations from JSON file

        Args:
            language_code: Language code (ar, en)

        Returns:
            True if language loaded successfully
        """
        try:
            if language_code not in self.supported_languages:
                logger.error(f"Unsupported language: {language_code}")
                return False

            language_file = os.path.join(self.language_dir, f"{language_code}.json")

            if not os.path.exists(language_file):
                logger.warning(f"Language file not found: {language_file}")
                # Create default language file
                self._create_default_language_file(language_code)
                return self.load_language(language_code)

            with open(language_file, 'r', encoding='utf-8') as f:
                self.translations[language_code] = json.load(f)

            logger.info(f"Language '{language_code}' loaded successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to load language '{language_code}': {e}")
            return False

    def _create_default_language_file(self, language_code: str):
        """Create default language file with basic translations"""

        try:
            os.makedirs(self.language_dir, exist_ok=True)

            if language_code == "ar":
                default_translations = {
                    "app": {
                        "title": "محاسبة احترافية",
                        "welcome": "مرحباً بك في نظام المحاسبة الاحترافي"
                    },
                    "menu": {
                        "dashboard": "لوحة التحكم",
                        "accounts": "الحسابات",
                        "journal": "القيود اليومية",
                        "reports": "التقارير",
                        "settings": "الإعدادات",
                        "logout": "تسجيل الخروج"
                    },
                    "login": {
                        "title": "تسجيل الدخول",
                        "username": "اسم المستخدم",
                        "password": "كلمة المرور",
                        "login_button": "دخول",
                        "forgot_password": "نسيت كلمة المرور؟",
                        "invalid_credentials": "اسم المستخدم أو كلمة المرور غير صحيحة"
                    },
                    "accounts": {
                        "title": "شجرة الحسابات",
                        "add_account": "إضافة حساب",
                        "edit_account": "تعديل حساب",
                        "delete_account": "حذف حساب",
                        "account_code": "كود الحساب",
                        "account_name_ar": "اسم الحساب عربي",
                        "account_name_en": "اسم الحساب إنجليزي",
                        "account_type": "نوع الحساب",
                        "account_category": "فئة الحساب",
                        "parent_account": "الحساب الأب",
                        "opening_balance": "الرصيد الافتتاحي",
                        "search_placeholder": "بحث في الحسابات...",
                        "no_accounts_found": "لم يتم العثور على حسابات"
                    },
                    "journal": {
                        "title": "القيود اليومية",
                        "new_entry": "قيد جديد",
                        "edit_entry": "تعديل القيد",
                        "delete_entry": "حذف القيد",
                        "entry_number": "رقم القيد",
                        "entry_date": "تاريخ القيد",
                        "description": "البيان",
                        "total_debit": "إجمالي المدين",
                        "total_credit": "إجمالي الدائن",
                        "account": "الحساب",
                        "debit": "مدين",
                        "credit": "دائن",
                        "add_line": "إضافة سطر",
                        "delete_line": "حذف السطر",
                        "save_entry": "حفظ القيد",
                        "post_entry": "ترحيل القيد",
                        "approve_entry": "اعتماد القيد",
                        "status_draft": "مسودة",
                        "status_posted": "مرحل",
                        "status_approved": "معتمد"
                    },
                    "reports": {
                        "title": "التقارير",
                        "general_ledger": "دفتر الأستاذ العام",
                        "trial_balance": "ميزان المراجعة",
                        "cost_accounts": "حسابات التكاليف",
                        "balance_sheet": "قائمة المركز المالي",
                        "income_statement": "قائمة الدخل",
                        "cash_flow": "قائمة التدفقات النقدية",
                        "export_excel": "تصدير إلى Excel",
                        "export_pdf": "تصدير إلى PDF",
                        "date_from": "من تاريخ",
                        "date_to": "إلى تاريخ",
                        "generate_report": "توليد التقرير"
                    },
                    "common": {
                        "save": "حفظ",
                        "cancel": "إلغاء",
                        "delete": "حذف",
                        "edit": "تعديل",
                        "add": "إضافة",
                        "search": "بحث",
                        "filter": "فلترة",
                        "export": "تصدير",
                        "print": "طباعة",
                        "close": "إغلاق",
                        "yes": "نعم",
                        "no": "لا",
                        "ok": "موافق",
                        "error": "خطأ",
                        "warning": "تحذير",
                        "info": "معلومات",
                        "success": "نجح",
                        "loading": "جاري التحميل...",
                        "no_data": "لا توجد بيانات",
                        "confirm_delete": "هل أنت متأكد من الحذف؟",
                        "operation_success": "تمت العملية بنجاح",
                        "operation_failed": "فشلت العملية",
                        "required_field": "هذا الحقل مطلوب",
                        "invalid_input": "إدخال غير صحيح",
                        "network_error": "خطأ في الاتصال"
                    },
                    "settings": {
                        "title": "الإعدادات",
                        "general": "عام",
                        "language": "اللغة",
                        "theme": "المظهر",
                        "light_theme": "فاتح",
                        "dark_theme": "داكن",
                        "system_theme": "نظام التشغيل",
                        "currency": "العملة",
                        "decimal_places": "الأماكن العشرية",
                        "date_format": "تنسيق التاريخ",
                        "backup": "نسخ احتياطي",
                        "auto_backup": "نسخ احتياطي تلقائي",
                        "backup_frequency": "تكرار النسخ",
                        "users": "المستخدمون",
                        "add_user": "إضافة مستخدم",
                        "edit_user": "تعديل مستخدم",
                        "delete_user": "حذف مستخدم",
                        "user_role": "دور المستخدم",
                        "admin": "مدير",
                        "accountant": "محاسب",
                        "viewer": "مشاهد"
                    }
                }
            else:
                default_translations = {
                    "app": {
                        "title": "Professional Accounting",
                        "welcome": "Welcome to Professional Accounting System"
                    },
                    "menu": {
                        "dashboard": "Dashboard",
                        "accounts": "Accounts",
                        "journal": "Journal",
                        "reports": "Reports",
                        "settings": "Settings",
                        "logout": "Logout"
                    },
                    "login": {
                        "title": "Login",
                        "username": "Username",
                        "password": "Password",
                        "login_button": "Login",
                        "forgot_password": "Forgot Password?",
                        "invalid_credentials": "Invalid username or password"
                    },
                    "accounts": {
                        "title": "Chart of Accounts",
                        "add_account": "Add Account",
                        "edit_account": "Edit Account",
                        "delete_account": "Delete Account",
                        "account_code": "Account Code",
                        "account_name_ar": "Account Name (AR)",
                        "account_name_en": "Account Name (EN)",
                        "account_type": "Account Type",
                        "account_category": "Account Category",
                        "parent_account": "Parent Account",
                        "opening_balance": "Opening Balance",
                        "search_placeholder": "Search accounts...",
                        "no_accounts_found": "No accounts found"
                    },
                    "journal": {
                        "title": "Journal Entries",
                        "new_entry": "New Entry",
                        "edit_entry": "Edit Entry",
                        "delete_entry": "Delete Entry",
                        "entry_number": "Entry Number",
                        "entry_date": "Entry Date",
                        "description": "Description",
                        "total_debit": "Total Debit",
                        "total_credit": "Total Credit",
                        "account": "Account",
                        "debit": "Debit",
                        "credit": "Credit",
                        "add_line": "Add Line",
                        "delete_line": "Delete Line",
                        "save_entry": "Save Entry",
                        "post_entry": "Post Entry",
                        "approve_entry": "Approve Entry",
                        "status_draft": "Draft",
                        "status_posted": "Posted",
                        "status_approved": "Approved"
                    },
                    "reports": {
                        "title": "Reports",
                        "general_ledger": "General Ledger",
                        "trial_balance": "Trial Balance",
                        "cost_accounts": "Cost Accounts",
                        "balance_sheet": "Balance Sheet",
                        "income_statement": "Income Statement",
                        "cash_flow": "Cash Flow",
                        "export_excel": "Export to Excel",
                        "export_pdf": "Export to PDF",
                        "date_from": "From Date",
                        "date_to": "To Date",
                        "generate_report": "Generate Report"
                    },
                    "common": {
                        "save": "Save",
                        "cancel": "Cancel",
                        "delete": "Delete",
                        "edit": "Edit",
                        "add": "Add",
                        "search": "Search",
                        "filter": "Filter",
                        "export": "Export",
                        "print": "Print",
                        "close": "Close",
                        "yes": "Yes",
                        "no": "No",
                        "ok": "OK",
                        "error": "Error",
                        "warning": "Warning",
                        "info": "Information",
                        "success": "Success",
                        "loading": "Loading...",
                        "no_data": "No Data",
                        "confirm_delete": "Are you sure you want to delete?",
                        "operation_success": "Operation completed successfully",
                        "operation_failed": "Operation failed",
                        "required_field": "This field is required",
                        "invalid_input": "Invalid input",
                        "network_error": "Network error"
                    },
                    "settings": {
                        "title": "Settings",
                        "general": "General",
                        "language": "Language",
                        "theme": "Theme",
                        "light_theme": "Light",
                        "dark_theme": "Dark",
                        "system_theme": "System",
                        "currency": "Currency",
                        "decimal_places": "Decimal Places",
                        "date_format": "Date Format",
                        "backup": "Backup",
                        "auto_backup": "Auto Backup",
                        "backup_frequency": "Backup Frequency",
                        "users": "Users",
                        "add_user": "Add User",
                        "edit_user": "Edit User",
                        "delete_user": "Delete User",
                        "user_role": "User Role",
                        "admin": "Admin",
                        "accountant": "Accountant",
                        "viewer": "Viewer"
                    }
                }

            with open(language_file, 'w', encoding='utf-8') as f:
                json.dump(default_translations, f, ensure_ascii=False, indent=2)

            logger.info(f"Default language file created: {language_file}")

        except Exception as e:
            logger.error(f"Failed to create default language file: {e}")

    def get_text(self, key: str, params: Optional[Dict[str, Any]] = None, language_code: Optional[str] = None) -> str:
        """
        Get translated text by key

        Args:
            key: Translation key (e.g., "menu.dashboard")
            params: Parameters for string formatting
            language_code: Language code (defaults to current language)

        Returns:
            Translated text
        """
        try:
            lang = language_code or self.current_language

            if lang not in self.translations:
                logger.warning(f"Language '{lang}' not loaded, using fallback")
                lang = self.fallback_language

            # Navigate through nested keys
            keys = key.split('.')
            text = self.translations.get(lang, {})

            for k in keys:
                if isinstance(text, dict) and k in text:
                    text = text[k]
                else:
                    # Key not found, try fallback language
                    if lang != self.fallback_language:
                        fallback_text = self.get_text(key, params, self.fallback_language)
                        if fallback_text != key:  # Only return fallback if not the key itself
                            return fallback_text

                    logger.warning(f"Translation key not found: {key}")
                    return key  # Return key as fallback

            # Apply parameter formatting
            if params and isinstance(text, str):
                try:
                    return text.format(**params)
                except (KeyError, ValueError) as e:
                    logger.warning(f"Parameter formatting failed for key '{key}': {e}")

            return text if isinstance(text, str) else str(text)

        except Exception as e:
            logger.error(f"Failed to get text for key '{key}': {e}")
            return key

    def set_language(self, language_code: str) -> bool:
        """
        Set current language

        Args:
            language_code: Language code to set

        Returns:
            True if language set successfully
        """
        try:
            if language_code not in self.supported_languages:
                logger.error(f"Unsupported language: {language_code}")
                return False

            # Load language if not already loaded
            if language_code not in self.translations:
                if not self.load_language(language_code):
                    return False

            self.current_language = language_code
            logger.info(f"Language set to: {language_code}")
            return True

        except Exception as e:
            logger.error(f"Failed to set language: {e}")
            return False

    def get_current_language(self) -> str:
        """Get current language code"""
        return self.current_language

    def get_rtl_direction(self) -> str:
        """Get text direction for current language"""
        return self.supported_languages.get(self.current_language, {}).get("direction", "ltr")

    def get_available_languages(self) -> Dict[str, Dict[str, str]]:
        """Get list of available languages"""
        return self.supported_languages

    def is_rtl(self) -> bool:
        """Check if current language is RTL"""
        return self.get_rtl_direction() == "rtl"

    def format_number(self, number: float, language: Optional[str] = None) -> str:
        """
        Format number according to language conventions

        Args:
            number: Number to format
            language: Language code (defaults to current)

        Returns:
            Formatted number string
        """
        try:
            lang = language or self.current_language

            # Get decimal places from settings (default to 2)
            decimal_places = 2

            if lang == "ar":
                # Arabic number formatting
                formatted = f"{number:,.{decimal_places}f}".replace(",", "٬").replace(".", "٫")

                # Convert digits to Arabic-Indic if needed
                arabic_digits = "٠١٢٣٤٥٦٧٨٩"
                western_digits = "0123456789"

                result = ""
                for char in formatted:
                    if char in western_digits:
                        result += arabic_digits[western_digits.index(char)]
                    else:
                        result += char

                return result
            else:
                # English/standard formatting
                return f"{number:,.{decimal_places}f}"

        except Exception as e:
            logger.error(f"Failed to format number: {e}")
            return str(number)

    def format_date(self, date_obj, language: Optional[str] = None) -> str:
        """
        Format date according to language conventions

        Args:
            date_obj: Date object or string
            language: Language code (defaults to current)

        Returns:
            Formatted date string
        """
        try:
            lang = language or self.current_language

            if isinstance(date_obj, str):
                date_obj = datetime.strptime(date_obj, "%Y-%m-%d")

            if lang == "ar":
                # Arabic date format
                months_ar = [
                    "يناير", "فبراير", "مارس", "إبريل", "مايو", "يونيو",
                    "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"
                ]
                return f"{date_obj.day} {months_ar[date_obj.month - 1]} {date_obj.year}"
            else:
                # English date format
                return date_obj.strftime("%d %B %Y")

        except Exception as e:
            logger.error(f"Failed to format date: {e}")
            return str(date_obj)

    def format_currency(self, amount: float, currency_symbol: str = "ر.س", language: Optional[str] = None) -> str:
        """
        Format currency amount according to language conventions

        Args:
            amount: Amount to format
            currency_symbol: Currency symbol
            language: Language code (defaults to current)

        Returns:
            Formatted currency string
        """
        try:
            lang = language or self.current_language
            formatted_number = self.format_number(amount, lang)

            if lang == "ar":
                return f"{formatted_number} {currency_symbol}"
            else:
                return f"{currency_symbol} {formatted_number}"

        except Exception as e:
            logger.error(f"Failed to format currency: {e}")
            return str(amount)

    def get_account_type_translation(self, account_type: str, language: Optional[str] = None) -> str:
        """Get translated account type"""

        lang = language or self.current_language

        translations = {
            "ar": {
                "general": "عام",
                "assistant": "مساعد",
                "analytic": "تحليلي"
            },
            "en": {
                "general": "General",
                "assistant": "Assistant",
                "analytic": "Analytic"
            }
        }

        return translations.get(lang, {}).get(account_type, account_type)

    def get_account_category_translation(self, category: str, language: Optional[str] = None) -> str:
        """Get translated account category"""

        lang = language or self.current_language

        translations = {
            "ar": {
                "asset": "أصل",
                "liability": "خصم",
                "expense": "مصروف",
                "revenue": "إيراد",
                "equity": "حقوق ملكية"
            },
            "en": {
                "asset": "Asset",
                "liability": "Liability",
                "expense": "Expense",
                "revenue": "Revenue",
                "equity": "Equity"
            }
        }

        return translations.get(lang, {}).get(category, category)

    def get_journal_status_translation(self, status: str, language: Optional[str] = None) -> str:
        """Get translated journal entry status"""

        lang = language or self.current_language

        translations = {
            "ar": {
                "draft": "مسودة",
                "posted": "مرحل",
                "approved": "معتمد"
            },
            "en": {
                "draft": "Draft",
                "posted": "Posted",
                "approved": "Approved"
            }
        }

        return translations.get(lang, {}).get(status, status)

    def validate_arabic_text(self, text: str) -> bool:
        """Validate if text contains Arabic characters"""
        try:
            arabic_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]')
            return bool(arabic_pattern.search(text))
        except:
            return False

    def get_text_alignment(self, language: Optional[str] = None) -> str:
        """Get text alignment for language"""
        return "right" if self.is_rtl() else "left"

    def get_widget_alignment(self, language: Optional[str] = None) -> str:
        """Get widget alignment for language"""
        return "e" if self.is_rtl() else "w"  # East for RTL, West for LTR

    def translate_month_name(self, month_number: int, language: Optional[str] = None) -> str:
        """Translate month name"""

        lang = language or self.current_language

        months = {
            "ar": ["يناير", "فبراير", "مارس", "إبريل", "مايو", "يونيو",
                   "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"],
            "en": ["January", "February", "March", "April", "May", "June",
                   "July", "August", "September", "October", "November", "December"]
        }

        return months.get(lang, [])[month_number - 1] or str(month_number)

    def get_language_info(self, language_code: Optional[str] = None) -> Dict[str, str]:
        """Get language information"""
        lang = language_code or self.current_language
        return self.supported_languages.get(lang, {})