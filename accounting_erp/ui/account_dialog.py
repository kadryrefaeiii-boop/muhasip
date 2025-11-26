#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Account Dialog
Dialog for adding and editing accounts
"""

import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class AccountDialog:
    """Dialog for adding and editing accounts"""

    def __init__(self, parent, parent_account=None, account=None):
        """
        Initialize account dialog

        Args:
            parent: Parent widget
            parent_account: Parent account for new account
            account: Existing account for editing
        """
        self.parent = parent
        self.language_manager = parent.language_manager
        self.parent_account = parent_account
        self.account = account
        self.result = None

        # Dialog variables
        self.dialog = None
        self.name_ar_var = tk.StringVar()
        self.name_en_var = tk.StringVar()
        self.account_type_var = tk.StringVar()
        self.account_category_var = tk.StringVar()
        self.opening_balance_var = tk.StringVar(value="0")
        self.parent_code_var = tk.StringVar()

        # Set initial values
        if account:
            self.is_edit = True
            self.set_initial_values()
        else:
            self.is_edit = False
            if parent_account:
                self.parent_code_var.set(f"{parent_account['name_ar']} ({parent_account['code']})")
                self.account_type_var.set("assistant")

        logger.info(f"Account dialog initialized - Edit: {self.is_edit}")

    def set_initial_values(self):
        """Set initial values from account data"""
        try:
            if self.account:
                self.name_ar_var.set(self.account['name_ar'])
                self.name_en_var.set(self.account['name_en'])
                self.account_type_var.set(self.account['account_type'])
                self.account_category_var.set(self.account['account_category'])
                self.opening_balance_var.set(str(self.account.get('opening_balance', 0)))

                if self.account.get('parent_id'):
                    from managers.account_manager import AccountManager
                    account_manager = AccountManager(self.parent.app.db_manager)
                    parent = account_manager.get_account_by_id(self.account['parent_id'])
                    if parent:
                        self.parent_code_var.set(f"{parent['name_ar']} ({parent['code']})")

        except Exception as e:
            logger.error(f"Failed to set initial values: {e}")

    def show(self):
        """Show dialog and return result"""
        try:
            self.create_dialog()
            self.dialog.wait_window()
            return self.result
        except Exception as e:
            logger.error(f"Failed to show dialog: {e}")
            return None

    def create_dialog(self):
        """Create dialog window"""
        try:
            # Create dialog
            self.dialog = tk.Toplevel(self.parent)
            self.dialog.title(
                self.language_manager.get_text("accounts.edit_account") if self.is_edit
                else self.language_manager.get_text("accounts.add_account")
            )
            self.dialog.geometry("500x600")
            self.dialog.resizable(False, False)
            self.dialog.transient(self.parent)
            self.dialog.grab_set()

            # Center dialog
            self.center_dialog()

            # Create content
            self.create_dialog_content()

            # Focus on first field
            self.name_ar_entry.focus_set()

            # Bind Enter key
            self.dialog.bind('<Return>', lambda e: self.save_account())

        except Exception as e:
            logger.error(f"Failed to create dialog: {e}")

    def center_dialog(self):
        """Center dialog on parent window"""
        try:
            self.dialog.update_idletasks()
            x = (self.dialog.winfo_screenwidth() // 2) - (500 // 2)
            y = (self.dialog.winfo_screenheight() // 2) - (600 // 2)
            self.dialog.geometry(f"500x600+{x}+{y}")
        except Exception as e:
            logger.error(f"Failed to center dialog: {e}")

    def create_dialog_content(self):
        """Create dialog content"""
        try:
            # Main frame with padding
            main_frame = ctk.CTkFrame(self.dialog)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

            # Title
            title_text = self.language_manager.get_text("accounts.edit_account") if self.is_edit \
                       else self.language_manager.get_text("accounts.add_account")

            title_label = ctk.CTkLabel(
                main_frame,
                text=title_text,
                font=ctk.CTkFont(size=18, weight="bold")
            )
            title_label.pack(pady=(0, 20))

            # Account info frame
            self.create_account_info_frame(main_frame)

            # Balance frame
            self.create_balance_frame(main_frame)

            # Button frame
            self.create_button_frame(main_frame)

        except Exception as e:
            logger.error(f"Failed to create dialog content: {e}")

    def create_account_info_frame(self, parent):
        """Create account information input frame"""
        try:
            info_frame = ctk.CTkFrame(parent)
            info_frame.pack(fill=tk.X, pady=(0, 20))

            # Parent account (read-only if editing, visible if new)
            if not self.is_edit or self.account.get('parent_id'):
                parent_label = ctk.CTkLabel(
                    info_frame,
                    text=self.language_manager.get_text("accounts.parent_account"),
                    anchor=self.language_manager.get_widget_alignment()
                )
                parent_label.pack(fill=tk.X, pady=(10, 5))

                parent_entry = ctk.CTkEntry(
                    info_frame,
                    textvariable=self.parent_code_var,
                    width=400,
                    height=35
                )
                parent_entry.pack(fill=tk.X, pady=(0, 15))
                parent_entry.configure(state="readonly")

            # Account code (read-only, generated automatically)
            if self.is_edit:
                code_label = ctk.CTkLabel(
                    info_frame,
                    text=self.language_manager.get_text("accounts.account_code"),
                    anchor=self.language_manager.get_widget_alignment()
                )
                code_label.pack(fill=tk.X, pady=(10, 5))

                code_entry = ctk.CTkEntry(
                    info_frame,
                    text=self.account['code'],
                    width=400,
                    height=35
                )
                code_entry.pack(fill=tk.X, pady=(0, 15))
                code_entry.configure(state="readonly")

            # Account Name (Arabic)
            name_ar_label = ctk.CTkLabel(
                info_frame,
                text=self.language_manager.get_text("accounts.account_name_ar") + " *",
                anchor=self.language_manager.get_widget_alignment()
            )
            name_ar_label.pack(fill=tk.X, pady=(10, 5))

            self.name_ar_entry = ctk.CTkEntry(
                info_frame,
                textvariable=self.name_ar_var,
                placeholder_text="أدخل اسم الحساب بالعربية",
                width=400,
                height=35
            )
            self.name_ar_entry.pack(fill=tk.X, pady=(0, 15))

            # Account Name (English)
            name_en_label = ctk.CTkLabel(
                info_frame,
                text=self.language_manager.get_text("accounts.account_name_en"),
                anchor=self.language_manager.get_widget_alignment()
            )
            name_en_label.pack(fill=tk.X, pady=(10, 5))

            self.name_en_entry = ctk.CTkEntry(
                info_frame,
                textvariable=self.name_en_var,
                placeholder_text="Enter account name in English",
                width=400,
                height=35
            )
            self.name_en_entry.pack(fill=tk.X, pady=(0, 15))

            # Account Type
            type_label = ctk.CTkLabel(
                info_frame,
                text=self.language_manager.get_text("accounts.account_type") + " *",
                anchor=self.language_manager.get_widget_alignment()
            )
            type_label.pack(fill=tk.X, pady=(10, 5))

            # Get available account types based on parent
            available_types = self.get_available_account_types()
            self.account_type_var.set(available_types[0] if available_types else "assistant")

            type_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
            type_frame.pack(fill=tk.X, pady=(0, 15))

            for account_type in available_types:
                type_radio = ctk.CTkRadioButton(
                    type_frame,
                    text=self.language_manager.get_account_type_translation(account_type),
                    variable=self.account_type_var,
                    value=account_type
                )
                type_radio.pack(side=tk.LEFT, padx=10)

            # Account Category
            category_label = ctk.CTkLabel(
                info_frame,
                text=self.language_manager.get_text("accounts.account_category") + " *",
                anchor=self.language_manager.get_widget_alignment()
            )
            category_label.pack(fill=tk.X, pady=(10, 5))

            # Category options
            categories = ["asset", "liability", "expense", "revenue", "equity"]

            category_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
            category_frame.pack(fill=tk.X, pady=(0, 15))

            # Create radio buttons for categories
            for i, category in enumerate(categories):
                if i % 3 == 0 and i > 0:
                    category_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
                    category_frame.pack(fill=tk.X)

                category_radio = ctk.CTkRadioButton(
                    category_frame,
                    text=self.language_manager.get_account_category_translation(category),
                    variable=self.account_category_var,
                    value=category
                )
                category_radio.pack(side=tk.LEFT, padx=10)

            # Set default category if editing
            if self.is_edit and self.account:
                self.account_category_var.set(self.account['account_category'])
            else:
                self.account_category_var.set(categories[0])

        except Exception as e:
            logger.error(f"Failed to create account info frame: {e}")

    def get_available_account_types(self):
        """Get available account types based on hierarchy rules"""
        try:
            if self.is_edit:
                # When editing, keep current type
                return [self.account['account_type']]

            if self.parent_account:
                parent_type = self.parent_account['account_type']

                # Hierarchy rules
                if parent_type == 'general':
                    return ['general', 'assistant', 'analytic']
                elif parent_type == 'assistant':
                    return ['analytic']
                else:  # analytic
                    return []  # No children allowed
            else:
                # Root level - only general accounts
                return ['general']

        except Exception as e:
            logger.error(f"Failed to get available account types: {e}")
            return ['assistant']  # Fallback

    def create_balance_frame(self, parent):
        """Create balance input frame"""
        try:
            balance_frame = ctk.CTkFrame(parent)
            balance_frame.pack(fill=tk.X, pady=(0, 20))

            balance_label = ctk.CTkLabel(
                balance_frame,
                text=self.language_manager.get_text("accounts.opening_balance"),
                anchor=self.language_manager.get_widget_alignment()
            )
            balance_label.pack(fill=tk.X, pady=(10, 5))

            balance_entry = ctk.CTkEntry(
                balance_frame,
                textvariable=self.opening_balance_var,
                placeholder_text="0.00",
                width=200,
                height=35
            )
            balance_entry.pack(fill=tk.X, pady=(0, 5))

            # Add currency label
            currency_label = ctk.CTkLabel(
                balance_frame,
                text=f"Currency: {self.language_manager.get_currency_symbol()}",
                font=ctk.CTkFont(size=10),
                text_color="gray"
            )
            currency_label.pack(anchor=self.language_manager.get_widget_alignment())

        except Exception as e:
            logger.error(f"Failed to create balance frame: {e}")

    def create_button_frame(self, parent):
        """Create dialog buttons"""
        try:
            button_frame = ctk.CTkFrame(parent)
            button_frame.pack(fill=tk.X, pady=(20, 0))

            # Buttons container
            buttons_container = ctk.CTkFrame(button_frame, fg_color="transparent")
            buttons_container.pack(fill=tk.X, padx=20, pady=20)

            # Save button
            save_button = ctk.CTkButton(
                buttons_container,
                text=self.language_manager.get_text("common.save"),
                command=self.save_account,
                width=150,
                height=40,
                font=ctk.CTkFont(size=14, weight="bold")
            )
            save_button.pack(side=tk.LEFT, padx=(0, 10))

            # Cancel button
            cancel_button = ctk.CTkButton(
                buttons_container,
                text=self.language_manager.get_text("common.cancel"),
                command=self.cancel_dialog,
                width=150,
                height=40,
                fg_color="gray50",
                hover_color="gray40"
            )
            cancel_button.pack(side=tk.LEFT)

        except Exception as e:
            logger.error(f"Failed to create button frame: {e}")

    def validate_input(self):
        """Validate form input"""
        try:
            # Check required fields
            name_ar = self.name_ar_var.get().strip()
            name_en = self.name_en_var.get().strip()
            account_type = self.account_type_var.get()
            account_category = self.account_category_var.get()

            if not name_ar:
                messagebox.showerror(
                    self.language_manager.get_text("common.error"),
                    "Account name (Arabic) is required\nاسم الحساب (عربي) مطلوب"
                )
                return False

            if not account_type:
                messagebox.showerror(
                    self.language_manager.get_text("common.error"),
                    "Account type is required\nنوع الحساب مطلوب"
                )
                return False

            if not account_category:
                messagebox.showerror(
                    self.language_manager.get_text("common.error"),
                    "Account category is required\nفئة الحساب مطلوبة"
                )
                return False

            # Validate opening balance
            try:
                opening_balance = float(self.opening_balance_var.get() or 0)
                if opening_balance < 0:
                    messagebox.showerror(
                        self.language_manager.get_text("common.error"),
                        "Opening balance cannot be negative\nالرصيد الافتتاحي لا يمكن أن يكون سالباً"
                    )
                    return False
            except ValueError:
                messagebox.showerror(
                    self.language_manager.get_text("common.error"),
                    "Invalid opening balance format\nتنسيق الرصيد الافتتاحي غير صحيح"
                )
                return False

            return True

        except Exception as e:
            logger.error(f"Input validation failed: {e}")
            return False

    def save_account(self):
        """Save account data"""
        try:
            if not self.validate_input():
                return

            # Initialize account manager
            from managers.account_manager import AccountManager
            account_manager = AccountManager(self.parent.app.db_manager)

            # Prepare data
            name_ar = self.name_ar_var.get().strip()
            name_en = self.name_en_var.get().strip()
            account_type = self.account_type_var.get()
            account_category = self.account_category_var.get()
            opening_balance = float(self.opening_balance_var.get() or 0)

            if self.is_edit:
                # Update existing account
                success = account_manager.update_account(
                    self.account['id'],
                    name_ar=name_ar,
                    name_en=name_en,
                    account_type=account_type,
                    account_category=account_category,
                    opening_balance=opening_balance,
                    updated_by=self.parent.app.current_user['id'] if self.parent.app.current_user else None
                )

                if success:
                    messagebox.showinfo(
                        self.language_manager.get_text("common.success"),
                        "Account updated successfully\nتم تحديث الحساب بنجاح"
                    )
                    self.result = True
                else:
                    messagebox.showerror(
                        self.language_manager.get_text("common.error"),
                        "Failed to update account\nفشل تحديث الحساب"
                    )

            else:
                # Add new account
                parent_id = self.parent_account['id'] if self.parent_account else None

                account_id = account_manager.add_account(
                    parent_id=parent_id,
                    name_ar=name_ar,
                    name_en=name_en,
                    account_type=account_type,
                    account_category=account_category,
                    opening_balance=opening_balance,
                    created_by=self.parent.app.current_user['id'] if self.parent.app.current_user else None
                )

                if account_id:
                    messagebox.showinfo(
                        self.language_manager.get_text("common.success"),
                        "Account added successfully\nتم إضافة الحساب بنجاح"
                    )
                    self.result = True
                else:
                    messagebox.showerror(
                        self.language_manager.get_text("common.error"),
                        "Failed to add account\nفشل إضافة الحساب"
                    )

            # Close dialog
            self.dialog.destroy()

        except Exception as e:
            logger.error(f"Failed to save account: {e}")
            messagebox.showerror(
                self.language_manager.get_text("common.error"),
                "Failed to save account\nفشل حفظ الحساب"
            )

    def cancel_dialog(self):
        """Cancel dialog"""
        try:
            if messagebox.askyesno(
                self.language_manager.get_text("common.cancel"),
                "Are you sure you want to cancel?\nهل أنت متأكد من الإلغاء؟"
            ):
                self.dialog.destroy()
        except Exception as e:
            logger.error(f"Failed to cancel dialog: {e}")