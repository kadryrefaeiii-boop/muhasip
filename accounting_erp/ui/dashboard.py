#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Dashboard Component
Professional financial dashboard with KPIs and charts
"""

import tkinter as tk
from tkinter import ttk
import customtkinter as ctk
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class Dashboard(ctk.CTkFrame):
    """Financial dashboard with KPIs and charts"""

    def __init__(self, parent, app):
        """
        Initialize dashboard

        Args:
            parent: Parent frame
            app: Application instance
        """
        super().__init__(parent)
        self.app = app
        self.language_manager = app.language_manager

        # Configure frame
        self.configure(fg_color="transparent")

        # Create dashboard sections
        self.create_kpi_section()
        self.create_charts_section()
        self.create_recent_transactions_section()
        self.create_quick_actions_section()

        # Load data
        self.refresh_data()

        logger.info("Dashboard initialized")

    def create_kpi_section(self):
        """Create KPI cards section"""
        try:
            # KPI container
            kpi_frame = ctk.CTkFrame(self)
            kpi_frame.pack(fill=tk.X, pady=(0, 20))

            # Title
            title_label = ctk.CTkLabel(
                kpi_frame,
                text=self.language_manager.get_text("dashboard.financial_summary"),
                font=ctk.CTkFont(size=18, weight="bold")
            )
            title_label.pack(pady=(20, 10), padx=20, anchor=tk.W)

            # KPI cards container
            kpi_cards_frame = ctk.CTkFrame(kpi_frame, fg_color="transparent")
            kpi_cards_frame.pack(fill=tk.X, padx=20, pady=10)

            # Create KPI cards
            self.create_kpi_cards(kpi_cards_frame)

        except Exception as e:
            logger.error(f"Failed to create KPI section: {e}")

    def create_kpi_cards(self, parent):
        """Create individual KPI cards"""
        try:
            # Define KPI configuration
            kpis = [
                {
                    "key": "total_assets",
                    "title": self.language_manager.get_text("dashboard.total_assets"),
                    "value": "0",
                    "color": "#28a745",
                    "icon": "💰"
                },
                {
                    "key": "total_liabilities",
                    "title": self.language_manager.get_text("dashboard.total_liabilities"),
                    "value": "0",
                    "color": "#dc3545",
                    "icon": "📊"
                },
                {
                    "key": "current_revenue",
                    "title": self.language_manager.get_text("dashboard.current_revenue"),
                    "value": "0",
                    "color": "#007bff",
                    "icon": "📈"
                },
                {
                    "key": "current_expenses",
                    "title": self.language_manager.get_text("dashboard.current_expenses"),
                    "value": "0",
                    "color": "#ffc107",
                    "icon": "📉"
                },
                {
                    "key": "net_profit",
                    "title": self.language_manager.get_text("dashboard.net_profit"),
                    "value": "0",
                    "color": "#17a2b8",
                    "icon": "💵"
                }
            ]

            # Store KPI references
            self.kpi_cards = {}

            # Create card grid
            for i, kpi in enumerate(kpis):
                card = self.create_kpi_card(kpi_cards_frame, kpi)
                card.grid(row=i // 3, column=i % 3, padx=10, pady=10, sticky="ew")
                self.kpi_cards[kpi['key']] = card

            # Configure grid weights
            for i in range(3):
                kpi_cards_frame.grid_columnconfigure(i, weight=1)

        except Exception as e:
            logger.error(f"Failed to create KPI cards: {e}")

    def create_kpi_card(self, parent, kpi_data):
        """Create individual KPI card"""
        try:
            # Card frame
            card_frame = ctk.CTkFrame(parent, corner_radius=10)
            card_frame.configure(fg_color=("#f8f9fa", "#2b2b2b"))

            # Card content
            content_frame = ctk.CTkFrame(card_frame, fg_color="transparent")
            content_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=15)

            # Icon and title row
            header_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
            header_frame.pack(fill=tk.X, pady=(0, 10))

            # Icon
            icon_label = ctk.CTkLabel(
                header_frame,
                text=kpi_data["icon"],
                font=ctk.CTkFont(size=24)
            )
            icon_label.pack(side=tk.LEFT)

            # Title
            title_label = ctk.CTkLabel(
                header_frame,
                text=kpi_data["title"],
                font=ctk.CTkFont(size=12),
                text_color="gray"
            )
            title_label.pack(side=tk.RIGHT)

            # Value
            value_label = ctk.CTkLabel(
                content_frame,
                text=kpi_data["value"],
                font=ctk.CTkFont(size=20, weight="bold"),
                text_color=kpi_data["color"]
            )
            value_label.pack(anchor=tk.W)

            return card_frame

        except Exception as e:
            logger.error(f"Failed to create KPI card: {e}")
            return None

    def create_charts_section(self):
        """Create charts section"""
        try:
            # Charts container
            charts_frame = ctk.CTkFrame(self)
            charts_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

            # Title
            title_label = ctk.CTkLabel(
                charts_frame,
                text="Charts & Analytics",
                font=ctk.CTkFont(size=18, weight="bold")
            )
            title_label.pack(pady=(20, 10), padx=20, anchor=tk.W)

            # Charts container
            charts_content = ctk.CTkFrame(charts_frame, fg_color="transparent")
            charts_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

            # Create revenue/expense chart
            self.create_revenue_expense_chart(charts_content)

        except Exception as e:
            logger.error(f"Failed to create charts section: {e}")

    def create_revenue_expense_chart(self, parent):
        """Create revenue vs expense chart"""
        try:
            # Chart frame
            chart_frame = ctk.CTkFrame(parent, corner_radius=10)
            chart_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

            # Create matplotlib figure
            self.fig, self.ax = plt.subplots(figsize=(10, 4), facecolor=("#f0f0f0", "#2b2b2b"))
            self.fig.patch.set_facecolor(("#f0f0f0", "#2b2b2b"))
            self.ax.set_facecolor(("#f8f9fa", "#1e1e1e"))

            # Create sample data
            dates = pd.date_range(start=datetime.now() - timedelta(days=30), periods=30, freq='D')
            revenue_data = [1000 + i * 50 + (i % 7) * 100 for i in range(30)]
            expense_data = [800 + i * 30 + (i % 5) * 80 for i in range(30)]

            # Plot data
            self.ax.plot(dates, revenue_data, label='Revenue', color='#28a745', linewidth=2)
            self.ax.plot(dates, expense_data, label='Expenses', color='#dc3545', linewidth=2)

            # Configure chart
            self.ax.set_title('Revenue vs Expenses (Last 30 Days)', fontsize=14, fontweight='bold')
            self.ax.set_xlabel('Date', fontsize=12)
            self.ax.set_ylabel('Amount', fontsize=12)
            self.ax.legend()
            self.ax.grid(True, alpha=0.3)

            # Format x-axis
            self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d'))
            self.ax.xaxis.set_major_locator(mdates.DayLocator(interval=5))
            plt.setp(self.ax.xaxis.get_majorticklabels(), rotation=45)

            # Embed chart in tkinter
            self.canvas = FigureCanvasTkAgg(self.fig, chart_frame)
            self.canvas.draw()
            self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        except Exception as e:
            logger.error(f"Failed to create revenue/expense chart: {e}")
            # Fallback to placeholder
            self.create_chart_placeholder(parent, "Revenue vs Expenses Chart")

    def create_chart_placeholder(self, parent, title):
        """Create chart placeholder when matplotlib fails"""
        try:
            placeholder_frame = ctk.CTkFrame(parent, corner_radius=10)
            placeholder_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

            placeholder_label = ctk.CTkLabel(
                placeholder_frame,
                text=f"📊 {title}\n\nCharts will be displayed here",
                font=ctk.CTkFont(size=14),
                text_color="gray"
            )
            placeholder_label.pack(expand=True)

        except Exception as e:
            logger.error(f"Failed to create chart placeholder: {e}")

    def create_recent_transactions_section(self):
        """Create recent transactions section"""
        try:
            # Transactions frame
            transactions_frame = ctk.CTkFrame(self)
            transactions_frame.pack(fill=tk.X, pady=(0, 20))

            # Header
            header_frame = ctk.CTkFrame(transactions_frame, fg_color="transparent")
            header_frame.pack(fill=tk.X, padx=20, pady=(15, 10))

            title_label = ctk.CTkLabel(
                header_frame,
                text=self.language_manager.get_text("dashboard.recent_transactions"),
                font=ctk.CTkFont(size=18, weight="bold")
            )
            title_label.pack(side=tk.LEFT)

            # View all button
            view_all_button = ctk.CTkButton(
                header_frame,
                text="View All",
                width=100,
                height=30,
                command=self.view_all_transactions
            )
            view_all_button.pack(side=tk.RIGHT)

            # Create transactions table
            self.create_transactions_table(transactions_frame)

        except Exception as e:
            logger.error(f"Failed to create recent transactions section: {e}")

    def create_transactions_table(self, parent):
        """Create transactions table"""
        try:
            # Table frame
            table_frame = ctk.CTkFrame(parent)
            table_frame.pack(fill=tk.X, padx=20, pady=(0, 15))

            # Create custom table using ttk
            style = ttk.Style()
            style.configure("Treeview", font=("Arial", 10))
            style.configure("Treeview.Heading", font=("Arial", 10, "bold"))

            # Columns
            columns = ("date", "entry_number", "description", "debit", "credit", "status")

            # Create treeview
            self.transactions_tree = ttk.Treeview(
                table_frame,
                columns=columns,
                show="headings",
                height=6
            )

            # Configure columns
            column_widths = {
                "date": 100,
                "entry_number": 120,
                "description": 200,
                "debit": 100,
                "credit": 100,
                "status": 100
            }

            column_headers = {
                "date": "Date",
                "entry_number": "Entry #",
                "description": "Description",
                "debit": "Debit",
                "credit": "Credit",
                "status": "Status"
            }

            for col in columns:
                self.transactions_tree.heading(col, text=column_headers[col])
                self.transactions_tree.column(col, width=column_widths[col], anchor=tk.CENTER if col in ["debit", "credit", "status"] else tk.W)

            # Add scrollbar
            scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.transactions_tree.yview)
            self.transactions_tree.configure(yscrollcommand=scrollbar.set)

            # Pack table and scrollbar
            self.transactions_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            # Load sample data
            self.load_sample_transactions()

        except Exception as e:
            logger.error(f"Failed to create transactions table: {e}")
            # Fallback placeholder
            placeholder = ctk.CTkLabel(
                parent,
                text="Recent transactions will appear here",
                text_color="gray"
            )
            placeholder.pack(pady=20)

    def load_sample_transactions(self):
        """Load sample transaction data"""
        try:
            # Sample transactions
            sample_transactions = [
                ("2024-01-15", "JE-000001", "Office Supplies Purchase", 500.00, 0.00, "Posted"),
                ("2024-01-14", "JE-000002", "Service Revenue", 0.00, 1500.00, "Posted"),
                ("2024-01-13", "JE-000003", "Rent Payment", 2000.00, 0.00, "Approved"),
                ("2024-01-12", "JE-000004", "Client Payment", 0.00, 3000.00, "Posted"),
                ("2024-01-11", "JE-000005", "Utility Bills", 350.00, 0.00, "Draft"),
            ]

            # Clear existing items
            for item in self.transactions_tree.get_children():
                self.transactions_tree.delete(item)

            # Add transactions
            for transaction in sample_transactions:
                self.transactions_tree.insert("", tk.END, values=transaction)

        except Exception as e:
            logger.error(f"Failed to load sample transactions: {e}")

    def create_quick_actions_section(self):
        """Create quick actions section"""
        try:
            # Actions frame
            actions_frame = ctk.CTkFrame(self)
            actions_frame.pack(fill=tk.X)

            # Title
            title_label = ctk.CTkLabel(
                actions_frame,
                text=self.language_manager.get_text("dashboard.quick_actions"),
                font=ctk.CTkFont(size=18, weight="bold")
            )
            title_label.pack(pady=(15, 10), padx=20, anchor=tk.W)

            # Actions container
            actions_container = ctk.CTkFrame(actions_frame, fg_color="transparent")
            actions_container.pack(fill=tk.X, padx=20, pady=(0, 20))

            # Action buttons
            actions = [
                {"text": "New Journal Entry", "icon": "📝", "command": self.new_journal_entry},
                {"text": "Add Account", "icon": "➕", "command": self.add_account},
                {"text": "Generate Report", "icon": "📊", "command": self.generate_report},
                {"text": "Backup Data", "icon": "💾", "command": self.backup_data}
            ]

            for i, action in enumerate(actions):
                button = ctk.CTkButton(
                    actions_container,
                    text=f"{action['icon']} {action['text']}",
                    command=action['command'],
                    width=200,
                    height=40
                )
                button.grid(row=i // 4, column=i % 4, padx=10, pady=5)

            # Configure grid weights
            for i in range(4):
                actions_container.grid_columnconfigure(i, weight=1)

        except Exception as e:
            logger.error(f"Failed to create quick actions section: {e}")

    def refresh_data(self):
        """Refresh dashboard data"""
        try:
            # Update KPI values
            self.update_kpi_values()

            # Update charts
            self.update_charts()

            # Update transactions
            self.load_recent_transactions()

        except Exception as e:
            logger.error(f"Failed to refresh dashboard data: {e}")

    def update_kpi_values(self):
        """Update KPI card values"""
        try:
            # Calculate financial summaries
            from managers.account_manager import AccountManager
            from managers.journal_manager import JournalManager

            account_manager = AccountManager(self.app.db_manager)
            journal_manager = JournalManager(self.app.db_manager)

            # Get current period
            start_date = (datetime.now().replace(day=1)).date()
            end_date = datetime.now().date()

            # Calculate totals
            total_assets = 0
            total_liabilities = 0
            current_revenue = 0
            current_expenses = 0

            # Get asset accounts
            asset_accounts = account_manager.get_accounts_by_category('asset')
            for account in asset_accounts:
                balance = account_manager.get_account_balance(account['id'])
                total_assets += balance['current_balance']

            # Get liability accounts
            liability_accounts = account_manager.get_accounts_by_category('liability')
            for account in liability_accounts:
                balance = account_manager.get_account_balance(account['id'])
                total_liabilities += balance['current_balance']

            # Get revenue accounts
            revenue_accounts = account_manager.get_accounts_by_category('revenue')
            for account in revenue_accounts:
                balance = account_manager.get_account_balance(account['id'])
                current_revenue += abs(balance['current_balance'])

            # Get expense accounts
            expense_accounts = account_manager.get_accounts_by_category('expense')
            for account in expense_accounts:
                balance = account_manager.get_account_balance(account['id'])
                current_expenses += balance['current_balance']

            # Calculate net profit
            net_profit = current_revenue - current_expenses

            # Update KPI cards
            kpi_values = {
                "total_assets": self.app.language_manager.format_currency(total_assets),
                "total_liabilities": self.app.language_manager.format_currency(total_liabilities),
                "current_revenue": self.app.language_manager.format_currency(current_revenue),
                "current_expenses": self.app.language_manager.format_currency(current_expenses),
                "net_profit": self.app.language_manager.format_currency(net_profit)
            }

            for key, value in kpi_values.items():
                if key in self.kpi_cards:
                    self.update_kpi_card(self.kpi_cards[key], value)

        except Exception as e:
            logger.error(f"Failed to update KPI values: {e}")

    def update_kpi_card(self, card_frame, value):
        """Update KPI card value"""
        try:
            # Find the value label in the card
            for widget in card_frame.winfo_children():
                for child in widget.winfo_children():
                    if isinstance(child, ctk.CTkLabel) and hasattr(child, 'cget'):
                        try:
                            font = child.cget("font")
                            if isinstance(font, ctk.CTkFont) and font.size == 20:
                                child.configure(text=value)
                                break
                        except:
                            continue

        except Exception as e:
            logger.error(f"Failed to update KPI card: {e}")

    def update_charts(self):
        """Update chart data"""
        try:
            # Update revenue/expense chart
            if hasattr(self, 'ax'):
                self.ax.clear()

                # Generate new data
                dates = pd.date_range(start=datetime.now() - timedelta(days=30), periods=30, freq='D')
                revenue_data = [1000 + i * 50 + (i % 7) * 100 for i in range(30)]
                expense_data = [800 + i * 30 + (i % 5) * 80 for i in range(30)]

                # Plot new data
                self.ax.plot(dates, revenue_data, label='Revenue', color='#28a745', linewidth=2)
                self.ax.plot(dates, expense_data, label='Expenses', color='#dc3545', linewidth=2)

                # Configure chart
                self.ax.set_title('Revenue vs Expenses (Last 30 Days)', fontsize=14, fontweight='bold')
                self.ax.set_xlabel('Date', fontsize=12)
                self.ax.set_ylabel('Amount', fontsize=12)
                self.ax.legend()
                self.ax.grid(True, alpha=0.3)

                # Redraw canvas
                if hasattr(self, 'canvas'):
                    self.canvas.draw()

        except Exception as e:
            logger.error(f"Failed to update charts: {e}")

    def load_recent_transactions(self):
        """Load recent transactions from database"""
        try:
            from managers.journal_manager import JournalManager
            journal_manager = JournalManager(self.app.db_manager)

            # Get recent entries
            recent_entries = journal_manager.get_entries(
                filters={"limit": 10},
                pagination={"limit": 10, "offset": 0}
            )

            # Clear and update table
            if hasattr(self, 'transactions_tree'):
                # Clear existing items
                for item in self.transactions_tree.get_children():
                    self.transactions_tree.delete(item)

                # Add recent transactions
                for entry in recent_entries:
                    date_str = entry['date'].strftime('%Y-%m-%d') if entry['date'] else ''
                    status = entry['status'].title() if entry['status'] else ''

                    self.transactions_tree.insert("", tk.END, values=(
                        date_str,
                        entry['entry_number'],
                        entry['description'] or '',
                        entry['total_debit'] or 0.0,
                        entry['total_credit'] or 0.0,
                        status
                    ))

        except Exception as e:
            logger.error(f"Failed to load recent transactions: {e}")

    def new_journal_entry(self):
        """Handle new journal entry action"""
        try:
            self.app.show_journal()
        except Exception as e:
            logger.error(f"Failed to open journal entry: {e}")

    def add_account(self):
        """Handle add account action"""
        try:
            self.app.show_accounts()
        except Exception as e:
            logger.error(f"Failed to open accounts: {e}")

    def generate_report(self):
        """Handle generate report action"""
        try:
            self.app.show_reports()
        except Exception as e:
            logger.error(f"Failed to open reports: {e}")

    def backup_data(self):
        """Handle backup data action"""
        try:
            from managers.backup_manager import BackupManager
            backup_manager = BackupManager(self.app.db_manager)

            # Create backup
            backup_path = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            success = backup_manager.create_backup(backup_path)

            if success:
                messagebox.showinfo("Backup Successful", f"Backup created: {backup_path}")
            else:
                messagebox.showerror("Backup Failed", "Failed to create backup")

        except Exception as e:
            logger.error(f"Failed to backup data: {e}")
            messagebox.showerror("Backup Error", "Failed to create backup")

    def view_all_transactions(self):
        """Handle view all transactions action"""
        try:
            self.app.show_journal()
        except Exception as e:
            logger.error(f"Failed to view all transactions: {e}")