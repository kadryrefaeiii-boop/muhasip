#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Accounts Tree Component
Advanced tree view with drag-drop and search functionality
"""

import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk
from tkinter import colorchooser
from tkinterdnd2 import TkinterDnD, DND_FILES
import logging

logger = logging.getLogger(__name__)

class AccountsTree(ctk.CTkFrame):
    """Advanced tree view with drag-drop and search"""

    def __init__(self, parent, app):
        """
        Initialize accounts tree

        Args:
            parent: Parent frame
            app: Application instance
        """
        super().__init__(parent)
        self.app = app
        self.language_manager = app.language_manager
        self.account_manager = None

        # Tree data
        self.tree_data = {}
        self.expanded_items = set()

        # Setup UI
        self.setup_ui()
        self.load_accounts()

        logger.info("Accounts tree initialized")

    def setup_ui(self):
        """Setup tree interface"""
        try:
            # Toolbar
            self.create_toolbar()

            # Tree container
            self.create_tree_container()

        except Exception as e:
            logger.error(f"Failed to setup accounts tree: {e}")

    def create_toolbar(self):
        """Create tree toolbar"""
        try:
            # Toolbar frame
            toolbar_frame = ctk.CTkFrame(self)
            toolbar_frame.pack(fill=tk.X, pady=(0, 10))

            # Left side controls
            left_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
            left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)

            # Search entry
            self.search_var = tk.StringVar()
            self.search_var.trace('w', self.on_search_change)

            search_entry = ctk.CTkEntry(
                left_frame,
                textvariable=self.search_var,
                placeholder_text=self.language_manager.get_text("accounts.search_placeholder"),
                width=300
            )
            search_entry.pack(side=tk.LEFT, padx=(0, 10))

            # Clear search button
            clear_button = ctk.CTkButton(
                left_frame,
                text="✕",
                width=30,
                height=30,
                command=self.clear_search
            )
            clear_button.pack(side=tk.LEFT, padx=(0, 10))

            # Right side controls
            right_frame = ctk.CTkFrame(toolbar_frame, fg_color="transparent")
            right_frame.pack(side=tk.RIGHT)

            # Add account button
            add_button = ctk.CTkButton(
                right_frame,
                text="➕ " + self.language_manager.get_text("accounts.add_account"),
                command=self.add_account,
                width=120
            )
            add_button.pack(side=tk.LEFT, padx=5)

            # Refresh button
            refresh_button = ctk.CTkButton(
                right_frame,
                text="🔄",
                width=35,
                height=35,
                command=self.refresh_tree
            )
            refresh_button.pack(side=tk.LEFT, padx=5)

            # Expand/Collapse buttons
            expand_button = ctk.CTkButton(
                right_frame,
                text="➕",
                width=35,
                height=35,
                command=self.expand_all
            )
            expand_button.pack(side=tk.LEFT, padx=5)

            collapse_button = ctk.CTkButton(
                right_frame,
                text="➖",
                width=35,
                height=35,
                command=self.collapse_all
            )
            collapse_button.pack(side=tk.LEFT)

        except Exception as e:
            logger.error(f"Failed to create toolbar: {e}")

    def create_tree_container(self):
        """Create tree view container"""
        try:
            # Tree frame
            tree_frame = ctk.CTkFrame(self)
            tree_frame.pack(fill=tk.BOTH, expand=True)

            # Create traditional ttk Treeview for better tree functionality
            self.tree = ttk.Treeview(tree_frame)

            # Configure columns
            self.tree["columns"] = ("code", "type", "category", "balance")
            self.tree.column("#0", width=300, minwidth=200)  # Account name
            self.tree.column("code", width=100, minwidth=80)
            self.tree.column("type", width=100, minwidth=80)
            self.tree.column("category", width=100, minwidth=80)
            self.tree.column("balance", width=120, minwidth=100)

            # Configure headings
            self.tree.heading("#0", text=self.language_manager.get_text("accounts.account_name_ar"))
            self.tree.heading("code", text=self.language_manager.get_text("accounts.account_code"))
            self.tree.heading("type", text=self.language_manager.get_text("accounts.account_type"))
            self.tree.heading("category", text=self.language_manager.get_text("accounts.account_category"))
            self.tree.heading("balance", text=self.language_manager.get_text("accounts.current_balance"))

            # Configure style for RTL support
            style = ttk.Style()
            if self.language_manager.is_rtl():
                self.tree.configure(yscrollcommand=self.tree.yview)

            # Add scrollbars
            y_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=self.tree.yview)
            x_scrollbar = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL, command=self.tree.xview)

            self.tree.configure(yscrollcommand=y_scrollbar.set, xscrollcommand=x_scrollbar.set)

            # Pack tree and scrollbars
            self.tree.grid(row=0, column=0, sticky="nsew")
            y_scrollbar.grid(row=0, column=1, sticky="ns")
            x_scrollbar.grid(row=1, column=0, sticky="ew")

            # Configure grid weights
            tree_frame.grid_rowconfigure(0, weight=1)
            tree_frame.grid_columnconfigure(0, weight=1)

            # Bind events
            self.tree.bind("<Double-1>", self.on_double_click)
            self.tree.bind("<Button-3>", self.on_right_click)
            self.tree.bind("<<TreeviewSelect>>", self.on_selection_change)

        except Exception as e:
            logger.error(f"Failed to create tree container: {e}")

    def load_accounts(self, search_query=None):
        """Load accounts into tree"""
        try:
            # Clear existing items
            for item in self.tree.get_children():
                self.tree.delete(item)

            # Initialize account manager
            if not self.account_manager:
                from managers.account_manager import AccountManager
                self.account_manager = AccountManager(self.app.db_manager)

            # Get accounts
            if search_query:
                accounts = self.account_manager.search_accounts(search_query, "all")
            else:
                accounts = self.account_manager.get_accounts_tree()

            # Load accounts into tree
            self.tree_data.clear()
            if accounts:
                self.load_accounts_recursive(accounts, "")

            # Restore expanded state
            self.restore_expanded_state()

        except Exception as e:
            logger.error(f"Failed to load accounts: {e}")

    def load_accounts_recursive(self, accounts, parent_id):
        """Recursively load accounts into tree"""
        try:
            for account in accounts:
                # Prepare display values
                display_name = account['name_ar']
                if account['name_en']:
                    display_name += f" / {account['name_en']}"

                # Format balance
                balance = self.app.language_manager.format_currency(account.get('current_balance', 0))

                # Account type translation
                account_type = self.language_manager.get_account_type_translation(account['account_type'])
                account_category = self.language_manager.get_account_category_translation(account['account_category'])

                # Insert into tree
                item_id = self.tree.insert(
                    parent_id,
                    tk.END,
                    text=display_name,
                    values=(
                        account['code'],
                        account_type,
                        account_category,
                        balance
                    ),
                    tags=(account['account_type'], account['account_category'])
                )

                # Store account data
                self.tree_data[item_id] = account

                # Color code based on account type
                self.configure_item_tags(item_id, account)

                # Load children
                if 'children' in account and account['children']:
                    self.load_accounts_recursive(account['children'], item_id)

        except Exception as e:
            logger.error(f"Failed to load accounts recursively: {e}")

    def configure_item_tags(self, item_id, account):
        """Configure item tags and colors"""
        try:
            # Remove existing tags
            self.tree.item(item_id, tags=())

            # Add type-specific tags
            tags = [account['account_type']]

            # Configure tag colors
            if account['account_type'] == 'general':
                self.tree.tag_configure('general', foreground='#0066cc')
            elif account['account_type'] == 'assistant':
                self.tree.tag_configure('assistant', foreground='#9966cc')
            elif account['account_type'] == 'analytic':
                self.tree.tag_configure('analytic', foreground='#009900')

            # Configure category colors
            if account['account_category'] == 'asset':
                self.tree.tag_configure('asset', background='#e6f3ff')
            elif account['account_category'] == 'liability':
                self.tree.tag_configure('liability', background='#ffe6e6')
            elif account['account_category'] == 'expense':
                self.tree.tag_configure('expense', background='#fff9e6')
            elif account['account_category'] == 'revenue':
                self.tree.tag_configure('revenue', background='#e6ffe6')

            tags.append(account['account_category'])
            self.tree.item(item_id, tags=tags)

        except Exception as e:
            logger.error(f"Failed to configure item tags: {e}")

    def on_search_change(self, *args):
        """Handle search input change"""
        try:
            search_query = self.search_var.get().strip()
            if len(search_query) == 0 or len(search_query) >= 2:
                self.load_accounts(search_query)
        except Exception as e:
            logger.error(f"Failed to handle search change: {e}")

    def clear_search(self):
        """Clear search input"""
        try:
            self.search_var.set("")
        except Exception as e:
            logger.error(f"Failed to clear search: {e}")

    def on_double_click(self, event):
        """Handle tree double click"""
        try:
            item = self.tree.selection()[0]
            if item and item in self.tree_data:
                account = self.tree_data[item]
                self.edit_account(account)
        except (IndexError, KeyError) as e:
            logger.debug(f"No item selected for double click: {e}")

    def on_right_click(self, event):
        """Handle right click for context menu"""
        try:
            # Select item under cursor
            item = self.tree.identify_row(event.y)
            if item:
                self.tree.selection_set(item)

                if item in self.tree_data:
                    account = self.tree_data[item]
                    self.show_context_menu(event, account)
        except Exception as e:
            logger.error(f"Failed to handle right click: {e}")

    def on_selection_change(self, event):
        """Handle tree selection change"""
        try:
            selection = self.tree.selection()
            if selection:
                item = selection[0]
                if item in self.tree_data:
                    account = self.tree_data[item]
                    self.show_account_details(account)
        except Exception as e:
            logger.error(f"Failed to handle selection change: {e}")

    def show_context_menu(self, event, account):
        """Show context menu for account"""
        try:
            # Create context menu
            context_menu = tk.Menu(self.tree, tearoff=0)

            # Add menu items based on account type
            if account['account_type'] != 'analytic':
                context_menu.add_command(
                    label="➕ " + self.language_manager.get_text("accounts.add_account"),
                    command=lambda: self.add_child_account(account)
                )

            context_menu.add_command(
                label="✏️ " + self.language_manager.get_text("accounts.edit_account"),
                command=lambda: self.edit_account(account)
            )

            if not self.account_manager._has_journal_entries(account['id']):
                context_menu.add_command(
                    label="🗑️ " + self.language_manager.get_text("accounts.delete_account"),
                    command=lambda: self.delete_account(account)
                )

            context_menu.add_separator()

            # View options
            context_menu.add_command(
                label="👁️ View Ledger",
                command=lambda: self.view_account_ledger(account)
            )

            context_menu.add_command(
                label="📊 View Balance",
                command=lambda: self.view_account_balance(account)
            )

            # Show menu
            try:
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()

        except Exception as e:
            logger.error(f"Failed to show context menu: {e}")

    def show_account_details(self, account):
        """Show account details in status bar or panel"""
        try:
            # This would update a details panel or status bar
            details = f"Account: {account['name_ar']} ({account['code']}) - Balance: {self.app.language_manager.format_currency(account.get('current_balance', 0))}"
            self.app.main_window.show_status_message(details, "info")
        except Exception as e:
            logger.error(f"Failed to show account details: {e}")

    def add_account(self, parent_account=None):
        """Add new account dialog"""
        try:
            self.show_account_dialog(parent_account)
        except Exception as e:
            logger.error(f"Failed to add account: {e}")

    def add_child_account(self, parent_account):
        """Add child account to specified parent"""
        try:
            self.show_account_dialog(parent_account)
        except Exception as e:
            logger.error(f"Failed to add child account: {e}")

    def edit_account(self, account):
        """Edit account dialog"""
        try:
            self.show_account_dialog(None, account)
        except Exception as e:
            logger.error(f"Failed to edit account: {e}")

    def delete_account(self, account):
        """Delete account"""
        try:
            # Confirm deletion
            if messagebox.askyesno(
                self.language_manager.get_text("accounts.delete_account"),
                f"Are you sure you want to delete account '{account['name_ar']}'?\n\n"
                f"هل أنت متأكد من حذف حساب '{account['name_ar']}'؟"
            ):
                # Delete account
                success = self.account_manager.delete_account(
                    account['id'],
                    deleted_by=self.app.current_user['id'] if self.app.current_user else None
                )

                if success:
                    messagebox.showinfo(
                        "Success",
                        self.language_manager.get_text("common.operation_success")
                    )
                    self.refresh_tree()
                else:
                    messagebox.showerror(
                        "Error",
                        self.language_manager.get_text("common.operation_failed")
                    )

        except Exception as e:
            logger.error(f"Failed to delete account: {e}")
            messagebox.showerror("Error", "Failed to delete account")

    def show_account_dialog(self, parent_account, account=None):
        """Show add/edit account dialog"""
        try:
            # Import dialog
            from ui.account_dialog import AccountDialog

            dialog = AccountDialog(self, parent_account, account)
            result = dialog.show()

            if result:
                # Refresh tree
                self.refresh_tree()

        except Exception as e:
            logger.error(f"Failed to show account dialog: {e}")

    def view_account_ledger(self, account):
        """View account ledger"""
        try:
            # Open reports page filtered for this account
            self.app.show_reports()
            # Filter would be set in reports page
        except Exception as e:
            logger.error(f"Failed to view account ledger: {e}")

    def view_account_balance(self, account):
        """View detailed account balance"""
        try:
            balance = self.account_manager.get_account_balance(account['id'])
            balance_text = f"""
            Account: {account['name_ar']}
            Code: {account['code']}
            Opening Balance: {self.app.language_manager.format_currency(balance['opening_balance'])}
            Current Balance: {self.app.language_manager.format_currency(balance['current_balance'])}
            Period Debit: {self.app.language_manager.format_currency(balance['period_debit'])}
            Period Credit: {self.app.language_manager.format_currency(balance['period_credit'])}
            """

            messagebox.showinfo("Account Balance", balance_text)
        except Exception as e:
            logger.error(f"Failed to view account balance: {e}")

    def expand_all(self):
        """Expand all tree items"""
        try:
            def expand_recursive(item):
                self.tree.item(item, open=True)
                for child in self.tree.get_children(item):
                    expand_recursive(child)

            for item in self.tree.get_children():
                expand_recursive(item)

        except Exception as e:
            logger.error(f"Failed to expand all: {e}")

    def collapse_all(self):
        """Collapse all tree items"""
        try:
            def collapse_recursive(item):
                self.tree.item(item, open=False)
                for child in self.tree.get_children(item):
                    collapse_recursive(child)

            for item in self.tree.get_children():
                collapse_recursive(item)

        except Exception as e:
            logger.error(f"Failed to collapse all: {e}")

    def save_expanded_state(self):
        """Save current expanded state"""
        try:
            self.expanded_items.clear()

            def save_recursive(item):
                if self.tree.item(item, "open"):
                    self.expanded_items.add(item)
                for child in self.tree.get_children(item):
                    save_recursive(child)

            for item in self.tree.get_children():
                save_recursive(item)

        except Exception as e:
            logger.error(f"Failed to save expanded state: {e}")

    def restore_expanded_state(self):
        """Restore saved expanded state"""
        try:
            def restore_recursive(item):
                if item in self.expanded_items:
                    self.tree.item(item, open=True)
                for child in self.tree.get_children(item):
                    restore_recursive(child)

            for item in self.tree.get_children():
                restore_recursive(item)

        except Exception as e:
            logger.error(f"Failed to restore expanded state: {e}")

    def refresh_tree(self):
        """Refresh tree data"""
        try:
            # Save expanded state
            self.save_expanded_state()

            # Reload accounts
            self.load_accounts()

        except Exception as e:
            logger.error(f"Failed to refresh tree: {e}")

    def get_selected_account(self):
        """Get currently selected account"""
        try:
            selection = self.tree.selection()
            if selection:
                item = selection[0]
                if item in self.tree_data:
                    return self.tree_data[item]
            return None
        except Exception as e:
            logger.error(f"Failed to get selected account: {e}")
            return None

    def select_account(self, account_id):
        """Select and show account in tree"""
        try:
            # Find account in tree
            for item_id, account in self.tree_data.items():
                if account['id'] == account_id:
                    # Expand parents and select item
                    self.tree.selection_set(item_id)
                    self.tree.see(item_id)

                    # Show details
                    self.show_account_details(account)
                    break

        except Exception as e:
            logger.error(f"Failed to select account: {e}")

    def export_accounts(self):
        """Export accounts to file"""
        try:
            # Use account manager export functionality
            export_path = self.account_manager.export_accounts('excel')
            if export_path:
                messagebox.showinfo(
                    "Export Successful",
                    f"Accounts exported to: {export_path}"
                )
            else:
                messagebox.showerror("Export Failed", "Failed to export accounts")

        except Exception as e:
            logger.error(f"Failed to export accounts: {e}")
            messagebox.showerror("Export Error", "Failed to export accounts")