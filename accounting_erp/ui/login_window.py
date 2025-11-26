#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Login Window
Professional authentication interface with Arabic/English support
"""

import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
import logging

logger = logging.getLogger(__name__)

class LoginWindow:
    """Professional login window with RTL support"""

    def __init__(self, parent, app):
        """
        Initialize login window

        Args:
            parent: Parent window
            app: Application instance
        """
        self.parent = parent
        self.app = app
        self.language_manager = app.language_manager
        self.settings_manager = app.settings_manager
        self.user_manager = None

        # Create login window
        self.window = ctk.CTkToplevel(parent)
        self.window.title(self.language_manager.get_text("app.title"))
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.window.resizable(False, False)

        # Variables
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.remember_var = tk.BooleanVar()

        # Setup UI
        self.setup_ui()
        self.center_window()

        # Load remembered username if exists
        self.load_remembered_username()

        # Focus on username field
        self.username_entry.focus_set()

        # Bind Enter key for login
        self.window.bind('<Return>', lambda e: self.attempt_login())

    def setup_ui(self):
        """Setup login interface"""
        try:
            # Main container
            main_frame = ctk.CTkFrame(self.window, corner_radius=15)
            main_frame.pack(padx=40, pady=40, fill=tk.BOTH, expand=True)

            # Logo/Header section
            self.create_header_section(main_frame)

            # Login form section
            self.create_login_form(main_frame)

            # Language selector
            self.create_language_selector(main_frame)

            # Footer section
            self.create_footer_section(main_frame)

        except Exception as e:
            logger.error(f"Failed to setup login UI: {e}")
            messagebox.showerror("Error", "Failed to setup login interface")

    def create_header_section(self, parent):
        """Create logo and header section"""
        try:
            header_frame = ctk.CTkFrame(parent, fg_color="transparent")
            header_frame.pack(pady=(0, 30), fill=tk.X)

            # Application title
            title_text = self.language_manager.get_text("login.subtitle")
            title_label = ctk.CTkLabel(
                header_frame,
                text=title_text,
                font=ctk.CTkFont(size=20, weight="bold")
            )
            title_label.pack()

            # Subtitle
            subtitle_text = "Professional Accounting System"
            if self.language_manager.get_current_language() == "ar":
                subtitle_text = "نظام المحاسبة الاحترافي"

            subtitle_label = ctk.CTkLabel(
                header_frame,
                text=subtitle_text,
                font=ctk.CTkFont(size=12),
                text_color="gray"
            )
            subtitle_label.pack(pady=(5, 0))

        except Exception as e:
            logger.error(f"Failed to create header section: {e}")

    def create_login_form(self, parent):
        """Create login form fields"""
        try:
            # Form container
            form_frame = ctk.CTkFrame(parent, fg_color="transparent")
            form_frame.pack(pady=20, fill=tk.X)

            # Username field
            username_label = ctk.CTkLabel(
                form_frame,
                text=self.language_manager.get_text("login.username"),
                anchor=self.language_manager.get_widget_alignment()
            )
            username_label.pack(fill=tk.X, pady=(0, 5))

            self.username_entry = ctk.CTkEntry(
                form_frame,
                textvariable=self.username_var,
                placeholder_text=self.language_manager.get_text("login.username"),
                width=300,
                height=40
            )
            self.username_entry.pack(fill=tk.X, pady=(0, 15))

            # Password field
            password_label = ctk.CTkLabel(
                form_frame,
                text=self.language_manager.get_text("login.password"),
                anchor=self.language_manager.get_widget_alignment()
            )
            password_label.pack(fill=tk.X, pady=(0, 5))

            self.password_entry = ctk.CTkEntry(
                form_frame,
                textvariable=self.password_var,
                placeholder_text=self.language_manager.get_text("login.password"),
                show="*",
                width=300,
                height=40
            )
            self.password_entry.pack(fill=tk.X, pady=(0, 15))

            # Remember me checkbox
            remember_checkbox = ctk.CTkCheckBox(
                form_frame,
                text=self.language_manager.get_text("login.remember_me"),
                variable=self.remember_var
            )
            remember_checkbox.pack(anchor=self.language_manager.get_widget_alignment(), pady=(0, 15))

            # Login button
            login_button = ctk.CTkButton(
                form_frame,
                text=self.language_manager.get_text("login.login_button"),
                command=self.attempt_login,
                width=300,
                height=45,
                font=ctk.CTkFont(size=14, weight="bold")
            )
            login_button.pack(fill=tk.X, pady=(10, 0))

            # Forgot password link
            forgot_link = ctk.CTkLabel(
                form_frame,
                text=self.language_manager.get_text("login.forgot_password"),
                text_color="#1f6aa5",
                cursor="hand2"
            )
            forgot_link.pack(anchor=self.language_manager.get_widget_alignment(), pady=(10, 0))
            forgot_link.bind("<Button-1>", self.on_forgot_password)

        except Exception as e:
            logger.error(f"Failed to create login form: {e}")

    def create_language_selector(self, parent):
        """Create language selection"""
        try:
            language_frame = ctk.CTkFrame(parent, fg_color="transparent")
            language_frame.pack(pady=10, fill=tk.X)

            language_label = ctk.CTkLabel(
                language_frame,
                text="Language / اللغة",
                font=ctk.CTkFont(size=10)
            )
            language_label.pack()

            # Language buttons
            button_frame = ctk.CTkFrame(language_frame, fg_color="transparent")
            button_frame.pack(pady=5)

            current_lang = self.language_manager.get_current_language()

            # Arabic button
            ar_button = ctk.CTkButton(
                button_frame,
                text="العربية",
                width=80,
                height=30,
                fg_color="#2b2b2b" if current_lang == "ar" else "transparent",
                border_width=2 if current_lang == "ar" else 0,
                command=lambda: self.change_language("ar")
            )
            ar_button.pack(side=tk.LEFT, padx=5)

            # English button
            en_button = ctk.CTkButton(
                button_frame,
                text="English",
                width=80,
                height=30,
                fg_color="#2b2b2b" if current_lang == "en" else "transparent",
                border_width=2 if current_lang == "en" else 0,
                command=lambda: self.change_language("en")
            )
            en_button.pack(side=tk.LEFT, padx=5)

        except Exception as e:
            logger.error(f"Failed to create language selector: {e}")

    def create_footer_section(self, parent):
        """Create footer section"""
        try:
            footer_frame = ctk.CTkFrame(parent, fg_color="transparent")
            footer_frame.pack(side=tk.BOTTOM, pady=(20, 0))

            version_label = ctk.CTkLabel(
                footer_frame,
                text=f"Version 1.0.0",
                font=ctk.CTkFont(size=9),
                text_color="gray"
            )
            version_label.pack()

        except Exception as e:
            logger.error(f"Failed to create footer section: {e}")

    def change_language(self, language_code):
        """Change application language"""
        try:
            # Update language manager
            if self.language_manager.set_language(language_code):
                # Save to settings
                self.settings_manager.set_language(language_code)

                # Update UI text
                self.update_ui_texts()

                # Update language button colors
                self.update_language_buttons()

                logger.info(f"Language changed to: {language_code}")

        except Exception as e:
            logger.error(f"Failed to change language: {e}")

    def update_ui_texts(self):
        """Update all UI text elements"""
        try:
            # Update window title
            self.window.title(self.language_manager.get_text("app.title"))

            # Update form labels and placeholders
            for widget in self.window.winfo_children():
                self.update_widget_texts(widget)

        except Exception as e:
            logger.error(f"Failed to update UI texts: {e}")

    def update_widget_texts(self, widget):
        """Recursively update widget texts"""
        try:
            if isinstance(widget, ctk.CTkLabel):
                # Update label text based on current text
                current_text = widget.cget("text")
                # This is simplified - in practice, you'd map widgets to translation keys
                pass

            elif isinstance(widget, ctk.CTkEntry):
                # Update placeholder text
                if "username" in str(widget).lower():
                    widget.configure(placeholder_text=self.language_manager.get_text("login.username"))
                elif "password" in str(widget).lower():
                    widget.configure(placeholder_text=self.language_manager.get_text("login.password"))

            # Recursively update children
            for child in widget.winfo_children():
                self.update_widget_texts(child)

        except Exception as e:
            logger.debug(f"Failed to update widget text: {e}")

    def update_language_buttons(self):
        """Update language button colors"""
        try:
            current_lang = self.language_manager.get_current_language()

            # Find and update language buttons
            for widget in self.window.winfo_children():
                self.update_language_button_colors(widget, current_lang)

        except Exception as e:
            logger.error(f"Failed to update language buttons: {e}")

    def update_language_button_colors(self, widget, current_lang):
        """Recursively update language button colors"""
        try:
            if isinstance(widget, ctk.CTkButton):
                button_text = widget.cget("text")
                if button_text == "العربية":
                    widget.configure(
                        fg_color="#2b2b2b" if current_lang == "ar" else "transparent",
                        border_width=2 if current_lang == "ar" else 0
                    )
                elif button_text == "English":
                    widget.configure(
                        fg_color="#2b2b2b" if current_lang == "en" else "transparent",
                        border_width=2 if current_lang == "en" else 0
                    )

            # Recursively update children
            for child in widget.winfo_children():
                self.update_language_button_colors(child, current_lang)

        except Exception as e:
            logger.debug(f"Failed to update button colors: {e}")

    def attempt_login(self):
        """Attempt user login"""
        try:
            username = self.username_var.get().strip()
            password = self.password_var.get()

            # Validate inputs
            if not username or not password:
                messagebox.showerror(
                    self.language_manager.get_text("common.error"),
                    self.language_manager.get_text("login.invalid_credentials")
                )
                return

            # Disable login button during authentication
            self.set_login_state(False)

            # Authenticate user
            user_data = self.authenticate_user(username, password)

            if user_data:
                # Save remembered username
                if self.remember_var.get():
                    self.save_remembered_username(username)
                else:
                    self.clear_remembered_username()

                # Show success and proceed to main app
                messagebox.showinfo(
                    self.language_manager.get_text("common.success"),
                    self.language_manager.get_text("login.login_success")
                )

                # Notify app of successful login
                self.app.on_login_success(user_data)

            else:
                # Show error and enable retry
                messagebox.showerror(
                    self.language_manager.get_text("common.error"),
                    self.language_manager.get_text("login.invalid_credentials")
                )
                self.set_login_state(True)

        except Exception as e:
            logger.error(f"Login attempt failed: {e}")
            messagebox.showerror(
                self.language_manager.get_text("common.error"),
                "Login failed. Please try again."
            )
            self.set_login_state(True)

    def authenticate_user(self, username, password):
        """Authenticate user credentials"""
        try:
            # Initialize user manager if not already done
            if not self.user_manager:
                from managers.user_manager import UserManager
                self.user_manager = UserManager(self.app.db_manager)

            # Authenticate user
            user_data = self.user_manager.authenticate_user(username, password)

            return user_data

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return None

    def set_login_state(self, enabled):
        """Enable/disable login controls"""
        try:
            state = "normal" if enabled else "disabled"
            self.username_entry.configure(state=state)
            self.password_entry.configure(state=state)

            # Update login button
            login_button = None
            for widget in self.window.winfo_children():
                login_button = self.find_login_button(widget)
                if login_button:
                    break

            if login_button:
                if enabled:
                    login_button.configure(
                        text=self.language_manager.get_text("login.login_button"),
                        command=self.attempt_login
                    )
                else:
                    login_button.configure(
                        text=self.language_manager.get_text("common.loading"),
                        command=None
                    )

        except Exception as e:
            logger.error(f"Failed to set login state: {e}")

    def find_login_button(self, widget):
        """Find login button in widget tree"""
        try:
            if isinstance(widget, ctk.CTkButton):
                button_text = widget.cget("text")
                if any(keyword in button_text.lower() for keyword in ["login", "دخول"]):
                    return widget

            for child in widget.winfo_children():
                result = self.find_login_button(child)
                if result:
                    return result

            return None

        except Exception as e:
            return None

    def load_remembered_username(self):
        """Load remembered username from settings"""
        try:
            remembered_username = self.settings_manager.get_setting("remembered_username")
            if remembered_username:
                self.username_var.set(remembered_username)
                self.remember_var.set(True)

        except Exception as e:
            logger.error(f"Failed to load remembered username: {e}")

    def save_remembered_username(self, username):
        """Save username to settings"""
        try:
            self.settings_manager.set_setting("remembered_username", username)
        except Exception as e:
            logger.error(f"Failed to save remembered username: {e}")

    def clear_remembered_username(self):
        """Clear remembered username from settings"""
        try:
            self.settings_manager.delete_setting("remembered_username")
        except Exception as e:
            logger.error(f"Failed to clear remembered username: {e}")

    def on_forgot_password(self, event=None):
        """Handle forgot password click"""
        try:
            # Show password reset dialog or open reset form
            messagebox.showinfo(
                "Password Reset",
                "Please contact your system administrator to reset your password.\n\n"
                "يرجى الاتصال بمسؤول النظام لإعادة تعيين كلمة المرور."
            )
        except Exception as e:
            logger.error(f"Failed to handle forgot password: {e}")

    def center_window(self):
        """Center window on screen"""
        try:
            self.window.update_idletasks()
            width = self.window.winfo_width()
            height = self.window.winfo_height()
            x = (self.window.winfo_screenwidth() // 2) - (width // 2)
            y = (self.window.winfo_screenheight() // 2) - (height // 2)
            self.window.geometry(f'{width}x{height}+{x}+{y}')
        except Exception as e:
            logger.error(f"Failed to center window: {e}")

    def on_closing(self):
        """Handle window closing"""
        try:
            # Clear password field
            self.password_var.set("")
            # Hide window instead of destroy to allow reopening
            self.window.withdraw()
        except Exception as e:
            logger.error(f"Failed to handle window closing: {e}")

    def show(self):
        """Show login window"""
        try:
            self.window.deiconify()
            self.window.lift()
            self.window.focus_force()
        except Exception as e:
            logger.error(f"Failed to show window: {e}")

    def destroy(self):
        """Destroy login window"""
        try:
            if self.window:
                self.window.destroy()
        except Exception as e:
            logger.error(f"Failed to destroy window: {e}")