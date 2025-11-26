#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Main Window
Professional accounting ERP main interface with sidebar navigation
"""

import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class MainWindow:
    """Main application window with sidebar navigation"""

    def __init__(self, root, app):
        """
        Initialize main window

        Args:
            root: Root tkinter window
            app: Application instance
        """
        self.root = root
        self.app = app
        self.language_manager = app.language_manager
        self.settings_manager = app.settings_manager

        # Current page tracking
        self.current_page = None
        self.pages = {}

        # Setup main window
        self.setup_window()
        self.create_sidebar()
        self.create_content_area()
        self.create_header()

        # Load dashboard by default
        self.show_dashboard()

        logger.info("Main window initialized")

    def setup_window(self):
        """Setup main window properties"""
        try:
            # Set window title
            self.root.title(
                f"{self.language_manager.get_text('app.title')} - {self.language_manager.get_text('dashboard.title')}"
            )

            # Configure window sizing
            self.root.minsize(1200, 800)

            # Handle window closing
            self.root.protocol("WM_DELETE_WINDOW", self.app.logout)

        except Exception as e:
            logger.error(f"Failed to setup main window: {e}")

    def create_sidebar(self):
        """Create navigation sidebar"""
        try:
            # Sidebar frame
            self.sidebar = ctk.CTkFrame(self.root, width=250, corner_radius=0)
            self.sidebar.pack(side=tk.LEFT, fill=tk.Y)
            self.sidebar.pack_propagate(False)

            # Logo area
            self.create_sidebar_header()

            # Navigation menu
            self.create_navigation_menu()

            # User info area
            self.create_sidebar_footer()

        except Exception as e:
            logger.error(f"Failed to create sidebar: {e}")

    def create_sidebar_header(self):
        """Create sidebar header with logo"""
        try:
            # Logo frame
            logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
            logo_frame.pack(pady=(30, 20), padx=20, fill=tk.X)

            # App title
            title_label = ctk.CTkLabel(
                logo_frame,
                text=self.language_manager.get_text("app.title"),
                font=ctk.CTkFont(size=18, weight="bold"),
                wraplength=200
            )
            title_label.pack()

            # Version
            version_label = ctk.CTkLabel(
                logo_frame,
                text="v1.0.0",
                font=ctk.CTkFont(size=10),
                text_color="gray"
            )
            version_label.pack()

        except Exception as e:
            logger.error(f"Failed to create sidebar header: {e}")

    def create_navigation_menu(self):
        """Create navigation menu items"""
        try:
            # Navigation frame
            nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
            nav_frame.pack(pady=20, padx=10, fill=tk.X)

            # Menu items
            self.menu_items = [
                {
                    "key": "dashboard",
                    "icon": "📊",
                    "text": self.language_manager.get_text("menu.dashboard"),
                    "command": self.show_dashboard
                },
                {
                    "key": "accounts",
                    "icon": "📋",
                    "text": self.language_manager.get_text("menu.accounts"),
                    "command": self.show_accounts
                },
                {
                    "key": "journal",
                    "icon": "📝",
                    "text": self.language_manager.get_text("menu.journal"),
                    "command": self.show_journal
                },
                {
                    "key": "reports",
                    "icon": "📈",
                    "text": self.language_manager.get_text("menu.reports"),
                    "command": self.show_reports
                },
                {
                    "key": "settings",
                    "icon": "⚙️",
                    "text": self.language_manager.get_text("menu.settings"),
                    "command": self.show_settings
                }
            ]

            # Create menu buttons
            self.menu_buttons = {}
            for item in self.menu_items:
                button = self.create_menu_button(nav_frame, item)
                self.menu_buttons[item["key"]] = button

            # Add separator
            separator_frame = ctk.CTkFrame(nav_frame, height=1)
            separator_frame.pack(fill=tk.X, pady=20)

            # Logout button
            logout_button = ctk.CTkButton(
                nav_frame,
                text=f"🚪 {self.language_manager.get_text('menu.logout')}",
                command=self.app.logout,
                fg_color="#dc3545",
                hover_color="#c82333",
                anchor=self.language_manager.get_widget_alignment()
            )
            logout_button.pack(fill=tk.X, pady=5)

        except Exception as e:
            logger.error(f"Failed to create navigation menu: {e}")

    def create_menu_button(self, parent, menu_item):
        """Create individual menu button"""
        try:
            button = ctk.CTkButton(
                parent,
                text=f"{menu_item['icon']} {menu_item['text']}",
                command=menu_item['command'],
                height=40,
                anchor=self.language_manager.get_widget_alignment(),
                font=ctk.CTkFont(size=12)
            )
            button.pack(fill=tk.X, pady=3)
            return button

        except Exception as e:
            logger.error(f"Failed to create menu button: {e}")
            return None

    def create_sidebar_footer(self):
        """Create sidebar footer with user info"""
        try:
            # User info frame
            user_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
            user_frame.pack(side=tk.BOTTOM, pady=20, padx=20, fill=tk.X)

            # Current user
            if self.app.current_user:
                user_label = ctk.CTkLabel(
                    user_frame,
                    text=f"👤 {self.app.current_user['full_name'] or self.app.current_user['username']}",
                    font=ctk.CTkFont(size=10),
                    wraplength=200
                )
                user_label.pack()

                # Role
                role_text = self.language_manager.get_text(f"user_roles.{self.app.current_user['role']}")
                role_label = ctk.CTkLabel(
                    user_frame,
                    text=role_text,
                    font=ctk.CTkFont(size=9),
                    text_color="gray"
                )
                role_label.pack()

            # Last login
            last_login_text = self.language_manager.get_text("settings.last_login", "Last Login")
            last_login_label = ctk.CTkLabel(
                user_frame,
                text=f"{last_login_text}: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                font=ctk.CTkFont(size=8),
                text_color="gray60"
            )
            last_login_label.pack(pady=(5, 0))

        except Exception as e:
            logger.error(f"Failed to create sidebar footer: {e}")

    def create_content_area(self):
        """Create main content area"""
        try:
            # Content frame
            self.content_frame = ctk.CTkFrame(self.root)
            self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        except Exception as e:
            logger.error(f"Failed to create content area: {e}")

    def create_header(self):
        """Create application header"""
        try:
            # Header frame
            self.header_frame = ctk.CTkFrame(self.content_frame, height=60)
            self.header_frame.pack(fill=tk.X, pady=(0, 10))
            self.header_frame.pack_propagate(False)

            # Header content
            header_content = ctk.CTkFrame(self.header_frame, fg_color="transparent")
            header_content.pack(fill=tk.X, padx=20, pady=15)

            # Page title
            self.page_title = ctk.CTkLabel(
                header_content,
                text=self.language_manager.get_text("dashboard.title"),
                font=ctk.CTkFont(size=24, weight="bold")
            )
            self.page_title.pack(side=self.language_manager.get_widget_alignment())

            # Quick actions
            self.create_quick_actions(header_content)

        except Exception as e:
            logger.error(f"Failed to create header: {e}")

    def create_quick_actions(self, parent):
        """Create quick action buttons"""
        try:
            # Actions frame
            actions_frame = ctk.CTkFrame(parent, fg_color="transparent")
            actions_frame.pack(side=tk.RIGHT)

            # Language switcher
            lang_button = ctk.CTkButton(
                actions_frame,
                text="🌐 ع/En",
                width=60,
                height=30,
                command=self.toggle_language
            )
            lang_button.pack(side=tk.LEFT, padx=5)

            # Theme switcher
            theme_button = ctk.CTkButton(
                actions_frame,
                text="🌙",
                width=40,
                height=30,
                command=self.toggle_theme
            )
            theme_button.pack(side=tk.LEFT, padx=5)

        except Exception as e:
            logger.error(f"Failed to create quick actions: {e}")

    def toggle_language(self):
        """Toggle between Arabic and English"""
        try:
            current_lang = self.language_manager.get_current_language()
            new_lang = "en" if current_lang == "ar" else "ar"

            # Change language
            if self.language_manager.set_language(new_lang):
                # Save to settings
                self.settings_manager.set_language(new_lang)

                # Show success message
                lang_name = "English" if new_lang == "en" else "العربية"
                messagebox.showinfo("Language Changed", f"Language changed to {lang_name}")

                # Note: Full UI update would require page refresh
                # For now, just show confirmation

        except Exception as e:
            logger.error(f"Failed to toggle language: {e}")

    def toggle_theme(self):
        """Toggle between light and dark theme"""
        try:
            import customtkinter as ctk
            current_theme = ctk.get_appearance_mode()
            new_theme = "dark" if current_theme == "light" else "light"

            # Set new theme
            ctk.set_appearance_mode(new_theme)

            # Save to settings
            self.settings_manager.set_theme(new_theme)

            logger.info(f"Theme changed to: {new_theme}")

        except Exception as e:
            logger.error(f"Failed to toggle theme: {e}")

    def clear_content(self):
        """Clear current content area"""
        try:
            for widget in self.content_frame.winfo_children():
                if widget != self.header_frame:
                    widget.destroy()

        except Exception as e:
            logger.error(f"Failed to clear content: {e}")

    def show_dashboard(self):
        """Show dashboard page"""
        try:
            self.clear_content()
            self.page_title.configure(text=self.language_manager.get_text("dashboard.title"))

            # Create dashboard page
            from ui.dashboard import Dashboard
            dashboard = Dashboard(self.content_frame, self.app)
            dashboard.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # Update window title
            self.root.title(f"{self.language_manager.get_text('app.title')} - {self.language_manager.get_text('dashboard.title')}")

            # Highlight menu item
            self.highlight_menu_item("dashboard")

            self.current_page = "dashboard"

        except Exception as e:
            logger.error(f"Failed to show dashboard: {e}")
            messagebox.showerror("Error", "Failed to load dashboard")

    def show_accounts(self):
        """Show accounts page"""
        try:
            self.clear_content()
            self.page_title.configure(text=self.language_manager.get_text("accounts.title"))

            # Create accounts page
            from ui.accounts_page import AccountsPage
            accounts_page = AccountsPage(self.content_frame, self.app)
            accounts_page.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # Update window title
            self.root.title(f"{self.language_manager.get_text('app.title')} - {self.language_manager.get_text('accounts.title')}")

            # Highlight menu item
            self.highlight_menu_item("accounts")

            self.current_page = "accounts"

        except Exception as e:
            logger.error(f"Failed to show accounts: {e}")
            messagebox.showerror("Error", "Failed to load accounts page")

    def show_journal(self):
        """Show journal page"""
        try:
            self.clear_content()
            self.page_title.configure(text=self.language_manager.get_text("journal.title"))

            # Create journal page
            from ui.journal_page import JournalPage
            journal_page = JournalPage(self.content_frame, self.app)
            journal_page.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # Update window title
            self.root.title(f"{self.language_manager.get_text('app.title')} - {self.language_manager.get_text('journal.title')}")

            # Highlight menu item
            self.highlight_menu_item("journal")

            self.current_page = "journal"

        except Exception as e:
            logger.error(f"Failed to show journal: {e}")
            messagebox.showerror("Error", "Failed to load journal page")

    def show_reports(self):
        """Show reports page"""
        try:
            self.clear_content()
            self.page_title.configure(text=self.language_manager.get_text("reports.title"))

            # Create reports page
            from ui.reports_page import ReportsPage
            reports_page = ReportsPage(self.content_frame, self.app)
            reports_page.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # Update window title
            self.root.title(f"{self.language_manager.get_text('app.title')} - {self.language_manager.get_text('reports.title')}")

            # Highlight menu item
            self.highlight_menu_item("reports")

            self.current_page = "reports"

        except Exception as e:
            logger.error(f"Failed to show reports: {e}")
            messagebox.showerror("Error", "Failed to load reports page")

    def show_settings(self):
        """Show settings page"""
        try:
            self.clear_content()
            self.page_title.configure(text=self.language_manager.get_text("settings.title"))

            # Create settings page
            from ui.settings_page import SettingsPage
            settings_page = SettingsPage(self.content_frame, self.app)
            settings_page.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            # Update window title
            self.root.title(f"{self.language_manager.get_text('app.title')} - {self.language_manager.get_text('settings.title')}")

            # Highlight menu item
            self.highlight_menu_item("settings")

            self.current_page = "settings"

        except Exception as e:
            logger.error(f"Failed to show settings: {e}")
            messagebox.showerror("Error", "Failed to load settings page")

    def highlight_menu_item(self, item_key):
        """Highlight selected menu item"""
        try:
            # Reset all buttons to default color
            for key, button in self.menu_buttons.items():
                button.configure(fg_color=("gray75", "gray25"))

            # Highlight selected button
            if item_key in self.menu_buttons:
                self.menu_buttons[item_key].configure(fg_color=("#3B8ED0", "#1F6AA5"))

        except Exception as e:
            logger.error(f"Failed to highlight menu item: {e}")

    def refresh_current_page(self):
        """Refresh the currently displayed page"""
        try:
            if self.current_page:
                # Call the appropriate show method
                getattr(self, f"show_{self.current_page}")()

        except Exception as e:
            logger.error(f"Failed to refresh current page: {e}")

    def update_user_info(self):
        """Update user information in sidebar"""
        try:
            # Recreate sidebar footer with updated user info
            self.create_sidebar_footer()

        except Exception as e:
            logger.error(f"Failed to update user info: {e}")

    def get_current_page(self):
        """Get currently displayed page"""
        return self.current_page

    def show_status_message(self, message, message_type="info"):
        """Show status message in header"""
        try:
            # Create status label
            status_label = ctk.CTkLabel(
                self.header_frame,
                text=message,
                font=ctk.CTkFont(size=10)
            )

            # Set color based on message type
            colors = {
                "success": "#28a745",
                "error": "#dc3545",
                "warning": "#ffc107",
                "info": "#17a2b8"
            }
            status_label.configure(text_color=colors.get(message_type, "gray"))

            # Add to header
            status_label.pack(side=tk.LEFT, padx=20)

            # Auto-remove after 3 seconds
            self.root.after(3000, status_label.destroy)

        except Exception as e:
            logger.error(f"Failed to show status message: {e}")

    def confirm_action(self, title, message):
        """Show confirmation dialog"""
        try:
            result = messagebox.askyesno(title, message)
            return result

        except Exception as e:
            logger.error(f"Failed to show confirmation dialog: {e}")
            return False

    def destroy(self):
        """Cleanup when window is destroyed"""
        try:
            # Clear all pages
            self.clear_content()
            logger.info("Main window destroyed")

        except Exception as e:
            logger.error(f"Failed to destroy main window: {e}")