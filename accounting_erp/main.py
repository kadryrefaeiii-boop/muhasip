#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Professional Accounting ERP System
Main application entry point with Arabic/English support
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from managers.database_manager import DatabaseManager
from managers.settings_manager import SettingsManager
from managers.language_manager import LanguageManager
from managers.session_manager import SessionManager
from ui.login_window import LoginWindow
from ui.main_window import MainWindow
from ui.splash_screen import SplashScreen

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('accounting_erp.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class AccountingERPApp:
    """Main application class for Professional Accounting ERP System"""

    def __init__(self):
        logger.info("Starting Professional Accounting ERP System...")

        # Initialize managers
        self.db_manager = None
        self.settings_manager = None
        self.language_manager = None
        self.session_manager = None

        # UI components
        self.root = None
        self.login_window = None
        self.main_window = None
        self.splash_screen = None

        # App state
        self.current_user = None
        self.is_running = False

    def initialize_application(self):
        """Initialize all application components"""
        try:
            # Show splash screen
            self.show_splash_screen()

            # Initialize database
            self.initialize_database()

            # Initialize managers
            self.initialize_managers()

            # Setup theme and language
            self.setup_theme()
            self.setup_language()

            # Check if database needs initial setup
            self.check_database_setup()

            logger.info("Application initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize application: {e}")
            self.show_error_and_exit("فشل تهيئة التطبيق" if self.get_language_direction() == 'rtl' else "Application initialization failed")

    def show_splash_screen(self):
        """Show splash screen during loading"""
        self.root = tk.Tk()
        self.root.withdraw()  # Hide main window initially

        self.splash_screen = SplashScreen(self.root)
        self.root.after(100, self.splash_screen.show)

    def initialize_database(self):
        """Initialize database connection"""
        try:
            db_path = "database/accounting_erp.db"
            os.makedirs("database", exist_ok=True)

            self.db_manager = DatabaseManager(db_path)
            logger.info("Database initialized successfully")

        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise

    def initialize_managers(self):
        """Initialize all manager classes"""
        try:
            self.settings_manager = SettingsManager(self.db_manager)
            self.language_manager = LanguageManager()
            self.session_manager = SessionManager(self.db_manager)

            logger.info("Managers initialized successfully")

        except Exception as e:
            logger.error(f"Managers initialization failed: {e}")
            raise

    def setup_theme(self):
        """Setup CustomTkinter theme"""
        try:
            theme = self.settings_manager.get_setting("theme", "light")
            ctk.set_appearance_mode(theme)

            color_theme = self.settings_manager.get_setting("color_theme", "blue")
            ctk.set_default_color_theme(color_theme)

            logger.info(f"Theme set to {theme}/{color_theme}")

        except Exception as e:
            logger.error(f"Theme setup failed: {e}")
            # Use defaults
            ctk.set_appearance_mode("light")
            ctk.set_default_color_theme("blue")

    def setup_language(self):
        """Setup application language"""
        try:
            language = self.settings_manager.get_setting("language", "ar")
            self.language_manager.set_language(language)

            logger.info(f"Language set to {language}")

        except Exception as e:
            logger.error(f"Language setup failed: {e}")
            # Use Arabic as default
            self.language_manager.set_language("ar")

    def check_database_setup(self):
        """Check if database needs initial setup"""
        try:
            # Check if tables exist
            result = self.db_manager.execute_query(
                "SELECT name FROM sqlite_master WHERE type='table'",
                fetch_all=True
            )

            if not result:
                logger.info("Database empty - running initial setup")
                self.run_database_setup()

        except Exception as e:
            logger.error(f"Database setup check failed: {e}")
            raise

    def run_database_setup(self):
        """Run initial database setup"""
        try:
            from database.schema import create_all_tables
            from database.initial_data import insert_initial_data

            create_all_tables(self.db_manager)
            insert_initial_data(self.db_manager)

            logger.info("Database setup completed")

        except Exception as e:
            logger.error(f"Database setup failed: {e}")
            raise

    def get_language_direction(self):
        """Get current language direction (rtl/ltr)"""
        if self.language_manager:
            return self.language_manager.get_rtl_direction()
        return "rtl"  # Default to Arabic

    def show_login_screen(self):
        """Show login window"""
        try:
            # Close splash screen
            if self.splash_screen:
                self.splash_screen.close()
                self.splash_screen = None

            # Setup main window for login
            self.root.deiconify()
            self.root.withdraw()  # Keep hidden for now

            # Create login window
            self.login_window = LoginWindow(self.root, self)

            # Center window on screen
            self.center_window(self.login_window)

            self.login_window.grab_set()  # Modal dialog
            self.login_window.focus_set()

            logger.info("Login screen displayed")

        except Exception as e:
            logger.error(f"Failed to show login screen: {e}")
            self.show_error_and_exit("فشل عرض شاشة تسجيل الدخول" if self.get_language_direction() == 'rtl' else "Failed to show login screen")

    def center_window(self, window):
        """Center window on screen"""
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}')

    def on_login_success(self, user_data):
        """Handle successful login"""
        try:
            self.current_user = user_data
            self.session_manager.create_session(user_data['id'])

            # Close login window
            if self.login_window:
                self.login_window.destroy()
                self.login_window = None

            # Show main application
            self.show_main_window()

            logger.info(f"User {user_data['username']} logged in successfully")

        except Exception as e:
            logger.error(f"Login success handling failed: {e}")
            self.show_error_message("فشل في معالجة تسجيل الدخول" if self.get_language_direction() == 'rtl' else "Login processing failed")

    def show_main_window(self):
        """Show main application window"""
        try:
            # Setup main window
            self.root.deiconify()
            self.root.title("محاسبة احترافية - Professional Accounting ERP")

            # Create main window interface
            self.main_window = MainWindow(self.root, self)

            # Setup window properties
            self.setup_main_window_properties()

            logger.info("Main window displayed")

        except Exception as e:
            logger.error(f"Failed to show main window: {e}")
            self.show_error_and_exit("فشل عرض النافذة الرئيسية" if self.get_language_direction() == 'rtl' else "Failed to show main window")

    def setup_main_window_properties(self):
        """Setup main window properties"""
        try:
            # Window size and position
            self.root.geometry("1400x900")
            self.center_window(self.root)

            # Window properties
            self.root.minsize(1200, 800)
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

            # RTL/LTR support
            direction = self.get_language_direction()
            if direction == 'rtl':
                self.root.tk_setPalette(background=self.root.cget("bg"))
                # Additional RTL setup if needed

        except Exception as e:
            logger.error(f"Main window setup failed: {e}")

    def logout(self):
        """Handle user logout"""
        try:
            logger.info(f"User {self.current_user['username']} logging out")

            # Clear session
            if self.session_manager:
                self.session_manager.clear_session()

            self.current_user = None

            # Close main window
            if self.main_window:
                self.main_window.destroy()
                self.main_window = None

            # Show login screen again
            self.show_login_screen()

        except Exception as e:
            logger.error(f"Logout failed: {e}")

    def on_closing(self):
        """Handle application closing"""
        try:
            logger.info("Application closing...")

            # Confirm logout if user is logged in
            if self.current_user:
                result = messagebox.askyesno(
                    "تسجيل خروج - Logout",
                    "هل تريد تسجيل الخروج والخروج من التطبيق؟" if self.get_language_direction() == 'rtl' else "Do you want to logout and exit the application?"
                )
                if not result:
                    return

            # Clear session
            if self.session_manager:
                self.session_manager.clear_session()

            # Close database connection
            if self.db_manager:
                self.db_manager.close_connection()

            # Destroy windows
            if self.main_window:
                self.main_window.destroy()
            if self.login_window:
                self.login_window.destroy()
            if self.root:
                self.root.destroy()

            self.is_running = False
            logger.info("Application closed successfully")

        except Exception as e:
            logger.error(f"Application closing failed: {e}")
            sys.exit(1)

    def show_error_message(self, message):
        """Show error message to user"""
        try:
            messagebox.showerror(
                "خطأ - Error",
                message
            )
        except Exception as e:
            logger.error(f"Failed to show error message: {e}")

    def show_error_and_exit(self, message):
        """Show error message and exit application"""
        try:
            if self.root and self.root.winfo_exists():
                messagebox.showerror("خطأ - Error", message)
                if self.root:
                    self.root.destroy()
            else:
                print(f"FATAL ERROR: {message}")
        except:
            print(f"FATAL ERROR: {message}")

        sys.exit(1)

    def run(self):
        """Main application loop"""
        try:
            self.is_running = True

            # Initialize application
            self.initialize_application()

            # Show login screen after initialization
            self.root.after(2000, self.show_login_screen)  # 2 second splash

            # Start main loop
            self.root.mainloop()

        except KeyboardInterrupt:
            logger.info("Application interrupted by user")
            self.on_closing()
        except Exception as e:
            logger.error(f"Application run failed: {e}")
            self.show_error_and_exit("فشل تشغيل التطبيق" if self.get_language_direction() == 'rtl' else "Application run failed")

def main():
    """Main entry point"""
    try:
        # Set working directory
        os.chdir(os.path.dirname(os.path.abspath(__file__)))

        # Create and run application
        app = AccountingERPApp()
        app.run()

    except Exception as e:
        print(f"FATAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()