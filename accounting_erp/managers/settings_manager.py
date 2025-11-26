#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Settings Manager
Application settings and preferences management
"""

import logging
import json
import os
from typing import Dict, Any, Optional, Union
from datetime import datetime

logger = logging.getLogger(__name__)

class SettingsManager:
    """Application settings and preferences management"""

    def __init__(self, db_manager):
        """
        Initialize Settings Manager

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self._cache = {}
        self._cache_loaded = False

        # Load settings into cache
        self._load_settings_cache()

        logger.info("Settings Manager initialized")

    def _load_settings_cache(self):
        """Load all settings into memory cache"""
        try:
            query = "SELECT key, value, data_type FROM settings"
            settings = self.db_manager.execute_query(query, fetch_all=True)

            self._cache = {}
            for setting in settings or []:
                self._cache[setting['key']] = {
                    'value': setting['value'],
                    'data_type': setting['data_type']
                }

            self._cache_loaded = True
            logger.debug(f"Loaded {len(self._cache)} settings into cache")

        except Exception as e:
            logger.error(f"Failed to load settings cache: {e}")
            self._cache = {}

    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get setting value by key

        Args:
            key: Setting key
            default: Default value if key not found

        Returns:
            Setting value or default
        """
        try:
            # Check cache first
            if key in self._cache:
                cached_value = self._cache[key]
                return self._parse_setting_value(cached_value['value'], cached_value['data_type'])

            # Query database
            query = "SELECT value, data_type FROM settings WHERE key = ?"
            result = self.db_manager.execute_query(query, (key,), fetch_one=True)

            if result:
                value = self._parse_setting_value(result['value'], result['data_type'])
                # Update cache
                self._cache[key] = {
                    'value': result['value'],
                    'data_type': result['data_type']
                }
                return value

            return default

        except Exception as e:
            logger.error(f"Failed to get setting '{key}': {e}")
            return default

    def _parse_setting_value(self, value: str, data_type: str) -> Any:
        """Parse setting value based on data type"""

        try:
            if data_type == 'boolean':
                return value.lower() in ('true', '1', 'yes', 'on')
            elif data_type == 'integer':
                return int(value)
            elif data_type == 'float':
                return float(value)
            elif data_type == 'json':
                return json.loads(value)
            else:  # string
                return value

        except Exception as e:
            logger.warning(f"Failed to parse setting value: {e}")
            return value

    def set_setting(self, key: str, value: Any, data_type: Optional[str] = None,
                   description: Optional[str] = None, is_system: bool = False,
                   updated_by: Optional[int] = None) -> bool:
        """
        Set setting value

        Args:
            key: Setting key
            value: Setting value
            data_type: Data type (auto-detected if not provided)
            description: Setting description
            is_system: System setting (cannot be changed by users)
            updated_by: User ID updating the setting

        Returns:
            True if setting updated successfully
        """
        try:
            # Auto-detect data type if not provided
            if data_type is None:
                data_type = self._detect_data_type(value)

            # Convert value to string for storage
            string_value = self._convert_value_to_string(value, data_type)

            # Check if setting exists
            existing = self.db_manager.execute_query(
                "SELECT key FROM settings WHERE key = ?",
                (key,),
                fetch_one=True
            )

            if existing:
                # Update existing setting
                update_data = {
                    'value': string_value,
                    'data_type': data_type,
                    'updated_at': datetime.now()
                }

                if description:
                    update_data['description'] = description

                if updated_by:
                    update_data['updated_by'] = updated_by

                affected_rows = self.db_manager.update_record(
                    "settings",
                    update_data,
                    "key = ?",
                    (key,)
                )

            else:
                # Insert new setting
                setting_data = {
                    'key': key,
                    'value': string_value,
                    'data_type': data_type,
                    'description': description,
                    'is_system': is_system,
                    'updated_by': updated_by
                }

                self.db_manager.insert_record("settings", setting_data)
                affected_rows = 1

            # Update cache
            self._cache[key] = {
                'value': string_value,
                'data_type': data_type
            }

            if affected_rows > 0:
                logger.debug(f"Setting '{key}' updated successfully")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to set setting '{key}': {e}")
            return False

    def _detect_data_type(self, value: Any) -> str:
        """Auto-detect data type of value"""

        if isinstance(value, bool):
            return 'boolean'
        elif isinstance(value, int):
            return 'integer'
        elif isinstance(value, float):
            return 'float'
        elif isinstance(value, (dict, list)):
            return 'json'
        else:
            return 'string'

    def _convert_value_to_string(self, value: Any, data_type: str) -> str:
        """Convert value to string for storage"""

        try:
            if data_type == 'boolean':
                return str(value).lower()
            elif data_type == 'json':
                return json.dumps(value, ensure_ascii=False)
            else:
                return str(value)

        except Exception as e:
            logger.error(f"Failed to convert value to string: {e}")
            return str(value)

    def get_language(self) -> str:
        """Get current language setting"""
        return self.get_setting("language", "ar")

    def set_language(self, language: str, updated_by: Optional[int] = None) -> bool:
        """Set language setting"""
        return self.set_setting("language", language, updated_by=updated_by)

    def get_theme(self) -> str:
        """Get current theme setting"""
        return self.get_setting("theme", "light")

    def set_theme(self, theme: str, updated_by: Optional[int] = None) -> bool:
        """Set theme setting"""
        return self.set_setting("theme", theme, updated_by=updated_by)

    def get_color_theme(self) -> str:
        """Get color theme setting"""
        return self.get_setting("color_theme", "blue")

    def set_color_theme(self, color_theme: str, updated_by: Optional[int] = None) -> bool:
        """Set color theme setting"""
        return self.set_setting("color_theme", color_theme, updated_by=updated_by)

    def get_currency_symbol(self) -> str:
        """Get currency symbol"""
        return self.get_setting("currency_symbol", "ر.س")

    def get_decimal_places(self) -> int:
        """Get decimal places setting"""
        return self.get_setting("decimal_places", 2)

    def get_date_format(self) -> str:
        """Get date format setting"""
        return self.get_setting("date_format", "dd/MM/yyyy")

    def get_rtl_support(self) -> bool:
        """Get RTL support setting"""
        return self.get_setting("rtl_support", True)

    def get_auto_backup(self) -> bool:
        """Get auto backup setting"""
        return self.get_setting("auto_backup", True)

    def get_backup_retention_days(self) -> int:
        """Get backup retention days"""
        return self.get_setting("backup_retention_days", 30)

    def get_session_timeout(self) -> int:
        """Get session timeout in minutes"""
        return self.get_setting("session_timeout", 480)

    def get_max_login_attempts(self) -> int:
        """Get max login attempts"""
        return self.get_setting("max_login_attempts", 5)

    def get_require_approval(self) -> bool:
        """Get journal entry approval requirement"""
        return self.get_setting("require_approval", False)

    def get_all_settings(self, include_system: bool = True) -> Dict[str, Dict[str, Any]]:
        """
        Get all settings

        Args:
            include_system: Include system settings

        Returns:
            Dictionary of all settings
        """
        try:
            query = "SELECT * FROM settings"
            if not include_system:
                query += " WHERE is_system = 0"

            settings = self.db_manager.execute_query(query, fetch_all=True)

            result = {}
            for setting in settings or []:
                result[setting['key']] = {
                    'value': self._parse_setting_value(setting['value'], setting['data_type']),
                    'data_type': setting['data_type'],
                    'description': setting['description'],
                    'is_system': setting['is_system'],
                    'updated_at': setting['updated_at']
                }

            return result

        except Exception as e:
            logger.error(f"Failed to get all settings: {e}")
            return {}

    def delete_setting(self, key: str) -> bool:
        """
        Delete setting

        Args:
            key: Setting key to delete

        Returns:
            True if deleted successfully
        """
        try:
            # Check if it's a system setting
            setting = self.db_manager.execute_query(
                "SELECT is_system FROM settings WHERE key = ?",
                (key,),
                fetch_one=True
            )

            if setting and setting['is_system']:
                logger.warning(f"Cannot delete system setting: {key}")
                return False

            # Delete setting
            affected_rows = self.db_manager.delete_record("settings", "key = ?", (key,))

            if affected_rows > 0:
                # Remove from cache
                if key in self._cache:
                    del self._cache[key]

                logger.info(f"Setting '{key}' deleted successfully")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to delete setting '{key}': {e}")
            return False

    def export_settings(self, file_path: str) -> bool:
        """
        Export settings to JSON file

        Args:
            file_path: Path to export file

        Returns:
            True if export successful
        """
        try:
            settings = self.get_all_settings(include_system=False)

            # Prepare export data
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'app_version': '1.0.0',
                'settings': {}
            }

            for key, data in settings.items():
                export_data['settings'][key] = {
                    'value': data['value'],
                    'data_type': data['data_type']
                }

            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)

            logger.info(f"Settings exported to: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export settings: {e}")
            return False

    def import_settings(self, file_path: str, overwrite: bool = False) -> bool:
        """
        Import settings from JSON file

        Args:
            file_path: Path to import file
            overwrite: Overwrite existing settings

        Returns:
            True if import successful
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)

            if 'settings' not in import_data:
                logger.error("Invalid settings file format")
                return False

            imported_count = 0
            for key, data in import_data['settings'].items():
                # Check if setting exists
                existing = self.db_manager.execute_query(
                    "SELECT key FROM settings WHERE key = ?",
                    (key,),
                    fetch_one=True
                )

                if existing and not overwrite:
                    continue  # Skip existing settings

                # Import setting
                if self.set_setting(key, data['value'], data.get('data_type', 'string')):
                    imported_count += 1

            # Reload cache
            self._load_settings_cache()

            logger.info(f"Imported {imported_count} settings from: {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to import settings: {e}")
            return False

    def reset_to_defaults(self, user_id: Optional[int] = None) -> bool:
        """
        Reset all non-system settings to defaults

        Args:
            user_id: User ID performing the reset

        Returns:
            True if reset successful
        """
        try:
            # Delete all non-system settings
            affected_rows = self.db_manager.delete_record("settings", "is_system = 0")

            # Clear cache
            self._cache.clear()

            # Insert default settings
            self._insert_default_settings(user_id)

            # Reload cache
            self._load_settings_cache()

            logger.info(f"Reset {affected_rows} settings to defaults")
            return True

        except Exception as e:
            logger.error(f"Failed to reset settings: {e}")
            return False

    def _insert_default_settings(self, created_by: Optional[int] = None):
        """Insert default system settings"""

        default_settings = [
            ("app_name", "Professional Accounting ERP", "string", "Application name", True),
            ("app_version", "1.0.0", "string", "Application version", True),
            ("language", "ar", "string", "Default language (ar/en)", False),
            ("theme", "light", "string", "Application theme (light/dark/system)", False),
            ("color_theme", "blue", "string", "Color theme (blue/dark-blue/green)", False),
            ("decimal_places", "2", "integer", "Number of decimal places for amounts", False),
            ("date_format", "dd/MM/yyyy", "string", "Date display format", False),
            ("currency_symbol", "ر.س", "string", "Currency symbol", False),
            ("auto_backup", "true", "boolean", "Enable automatic backups", False),
            ("backup_retention_days", "30", "integer", "Backup retention period in days", False),
            ("session_timeout", "480", "integer", "Session timeout in minutes", False),
            ("max_login_attempts", "5", "integer", "Maximum failed login attempts", False),
            ("require_approval", "false", "boolean", "Require journal entry approval", False),
            ("export_format", "excel", "string", "Default export format", False),
            ("rtl_support", "true", "boolean", "Enable RTL language support", True)
        ]

        for setting in default_settings:
            key, value, data_type, description, is_system = setting

            # Check if setting already exists
            existing = self.db_manager.execute_query(
                "SELECT key FROM settings WHERE key = ?",
                (key,),
                fetch_one=True
            )

            if not existing:
                self.db_manager.insert_record("settings", {
                    "key": key,
                    "value": value,
                    "data_type": data_type,
                    "description": description,
                    "is_system": is_system,
                    "created_by": created_by
                }, return_id=False)

    def validate_setting_value(self, key: str, value: Any) -> tuple[bool, str]:
        """
        Validate setting value

        Args:
            key: Setting key
            value: Value to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            # Language validation
            if key == "language" and value not in ['ar', 'en']:
                return False, "Language must be 'ar' or 'en'"

            # Theme validation
            elif key == "theme" and value not in ['light', 'dark', 'system']:
                return False, "Theme must be 'light', 'dark', or 'system'"

            # Color theme validation
            elif key == "color_theme" and value not in ['blue', 'dark-blue', 'green']:
                return False, "Color theme must be 'blue', 'dark-blue', or 'green'"

            # Numeric validations
            elif key == "decimal_places" and (not isinstance(value, int) or value < 0 or value > 6):
                return False, "Decimal places must be between 0 and 6"

            elif key == "session_timeout" and (not isinstance(value, int) or value < 1):
                return False, "Session timeout must be at least 1 minute"

            elif key == "max_login_attempts" and (not isinstance(value, int) or value < 1 or value > 10):
                return False, "Max login attempts must be between 1 and 10"

            elif key == "backup_retention_days" and (not isinstance(value, int) or value < 1):
                return False, "Backup retention days must be at least 1"

            return True, ""

        except Exception as e:
            logger.error(f"Setting validation error: {e}")
            return False, f"Validation error: {str(e)}"

    def clear_cache(self):
        """Clear settings cache"""
        self._cache.clear()
        self._cache_loaded = False
        logger.debug("Settings cache cleared")

    def reload_cache(self):
        """Reload settings cache from database"""
        self._load_settings_cache()
        logger.debug("Settings cache reloaded")