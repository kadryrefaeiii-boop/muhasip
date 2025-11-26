#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Settings Page
Application settings and preferences
"""

import customtkinter as ctk
import logging

logger = logging.getLogger(__name__)

class SettingsPage(ctk.CTkFrame):
    """Application settings page"""

    def __init__(self, parent, app):
        """
        Initialize settings page

        Args:
            parent: Parent frame
            app: Application instance
        """
        super().__init__(parent)
        self.app = app
        self.language_manager = app.language_manager
        self.settings_manager = app.settings_manager

        # Configure frame
        self.configure(fg_color="transparent")

        # Create settings content
        self.create_settings_content()

        logger.info("Settings page initialized")

    def create_settings_content(self):
        """Create settings interface"""
        try:
            # Main container
            main_frame = ctk.CTkFrame(self)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

            # Title
            title_label = ctk.CTkLabel(
                main_frame,
                text=self.language_manager.get_text("settings.title"),
                font=ctk.CTkFont(size=24, weight="bold")
            )
            title_label.pack(pady=(20, 40), anchor=tk.W)

            # Settings sections
            self.create_general_settings(main_frame)
            self.create_appearance_settings(main_frame)
            self.create_backup_settings(main_frame)

        except Exception as e:
            logger.error(f"Failed to create settings content: {e}")

    def create_general_settings(self, parent):
        """Create general settings section"""
        try:
            # Section frame
            section_frame = ctk.CTkFrame(parent)
            section_frame.pack(fill=tk.X, pady=(0, 20))

            # Section title
            section_title = ctk.CTkLabel(
                section_frame,
                text=self.language_manager.get_text("settings.general"),
                font=ctk.CTkFont(size=16, weight="bold")
            )
            section_title.pack(pady=(20, 15), padx=20, anchor=tk.W)

            # Language setting
            language_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
            language_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

            language_label = ctk.CTkLabel(
                language_frame,
                text=self.language_manager.get_text("settings.language") + ":",
                width=150,
                anchor=tk.W
            )
            language_label.pack(side=tk.LEFT)

            current_lang = self.language_manager.get_current_language()
            lang_text = "العربية" if current_lang == "ar" else "English"

            lang_button = ctk.CTkButton(
                language_frame,
                text=f"🌐 {lang_text}",
                width=100,
                command=self.change_language
            )
            lang_button.pack(side=tk.RIGHT)

            # Currency setting
            currency_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
            currency_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

            currency_label = ctk.CTkLabel(
                currency_frame,
                text=self.language_manager.get_text("settings.currency") + ":",
                width=150,
                anchor=tk.W
            )
            currency_label.pack(side=tk.LEFT)

            currency_text = self.settings_manager.get_currency_symbol()
            currency_button = ctk.CTkButton(
                currency_frame,
                text=f"💵 {currency_text}",
                width=100,
                state="disabled"
            )
            currency_button.pack(side=tk.RIGHT)

        except Exception as e:
            logger.error(f"Failed to create general settings: {e}")

    def create_appearance_settings(self, parent):
        """Create appearance settings section"""
        try:
            # Section frame
            section_frame = ctk.CTkFrame(parent)
            section_frame.pack(fill=tk.X, pady=(0, 20))

            # Section title
            section_title = ctk.CTkLabel(
                section_frame,
                text=self.language_manager.get_text("settings.theme"),
                font=ctk.CTkFont(size=16, weight="bold")
            )
            section_title.pack(pady=(20, 15), padx=20, anchor=tk.W)

            # Theme options
            theme_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
            theme_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

            theme_label = ctk.CTkLabel(
                theme_frame,
                text=self.language_manager.get_text("settings.theme") + ":",
                width=150,
                anchor=tk.W
            )
            theme_label.pack(side=tk.LEFT)

            # Theme buttons
            import customtkinter as ctk
            current_theme = ctk.get_appearance_mode()

            light_button = ctk.CTkButton(
                theme_frame,
                text="☀️ Light",
                width=80,
                fg_color="#2b2b2b" if current_theme == "light" else "transparent",
                command=lambda: self.set_theme("light")
            )
            light_button.pack(side=tk.RIGHT, padx=5)

            dark_button = ctk.CTkButton(
                theme_frame,
                text="🌙 Dark",
                width=80,
                fg_color="#2b2b2b" if current_theme == "dark" else "transparent",
                command=lambda: self.set_theme("dark")
            )
            dark_button.pack(side=tk.RIGHT, padx=5)

        except Exception as e:
            logger.error(f"Failed to create appearance settings: {e}")

    def create_backup_settings(self, parent):
        """Create backup settings section"""
        try:
            # Section frame
            section_frame = ctk.CTkFrame(parent)
            section_frame.pack(fill=tk.X, pady=(0, 20))

            # Section title
            section_title = ctk.CTkLabel(
                section_frame,
                text=self.language_manager.get_text("settings.backup"),
                font=ctk.CTkFont(size=16, weight="bold")
            )
            section_title.pack(pady=(20, 15), padx=20, anchor=tk.W)

            # Auto backup setting
            backup_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
            backup_frame.pack(fill=tk.X, padx=20, pady=(0, 10))

            backup_label = ctk.CTkLabel(
                backup_frame,
                text=self.language_manager.get_text("settings.auto_backup") + ":",
                width=150,
                anchor=tk.W
            )
            backup_label.pack(side=tk.LEFT)

            backup_var = tk.BooleanVar(value=self.settings_manager.get_auto_backup())
            backup_switch = ctk.CTkSwitch(
                backup_frame,
                variable=backup_var,
                command=self.toggle_auto_backup
            )
            backup_switch.pack(side=tk.RIGHT)

            # Backup button
            backup_button_frame = ctk.CTkFrame(section_frame, fg_color="transparent")
            backup_button_frame.pack(fill=tk.X, padx=20, pady=(0, 20))

            backup_button = ctk.CTkButton(
                backup_button_frame,
                text="💾 Create Backup Now",
                command=self.create_backup,
                width=200
            )
            backup_button.pack(side=tk.RIGHT)

        except Exception as e:
            logger.error(f"Failed to create backup settings: {e}")

    def change_language(self):
        """Change application language"""
        try:
            current_lang = self.language_manager.get_current_language()
            new_lang = "en" if current_lang == "ar" else "ar"

            if self.language_manager.set_language(new_lang):
                self.settings_manager.set_language(new_lang)

                # Show confirmation
                lang_name = "English" if new_lang == "en" else "العربية"
                from tkinter import messagebox
                messagebox.showinfo("Language Changed", f"Language changed to {lang_name}\nتم تغيير اللغة إلى {lang_name}")

                # Note: Full UI refresh would require page reload
        except Exception as e:
            logger.error(f"Failed to change language: {e}")

    def set_theme(self, theme):
        """Set application theme"""
        try:
            import customtkinter as ctk
            ctk.set_appearance_mode(theme)
            self.settings_manager.set_theme(theme)

            logger.info(f"Theme changed to: {theme}")
        except Exception as e:
            logger.error(f"Failed to set theme: {e}")

    def toggle_auto_backup(self):
        """Toggle auto backup setting"""
        try:
            current_value = self.settings_manager.get_auto_backup()
            new_value = not current_value
            self.settings_manager.set_setting("auto_backup", new_value)

            logger.info(f"Auto backup toggled to: {new_value}")
        except Exception as e:
            logger.error(f"Failed to toggle auto backup: {e}")

    def create_backup(self):
        """Create immediate backup"""
        try:
            from tkinter import messagebox
            from managers.backup_manager import BackupManager

            backup_manager = BackupManager(self.app.db_manager)
            from datetime import datetime
            backup_path = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

            success = backup_manager.create_backup(backup_path)

            if success:
                messagebox.showinfo(
                    "Backup Successful",
                    f"Backup created successfully!\nFile: {backup_path}\n\nتم إنشاء نسخة احتياطية بنجاح!\nالملف: {backup_path}"
                )
            else:
                messagebox.showerror(
                    "Backup Failed",
                    "Failed to create backup\nفشل إنشاء النسخة الاحتياطية"
                )

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            from tkinter import messagebox
            messagebox.showerror(
                "Backup Error",
                "An error occurred while creating backup\nحدث خطأ أثناء إنشاء النسخة الاحتياطية"
            )