#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Reports Page
Financial reports and analytics page
"""

import customtkinter as ctk
import logging

logger = logging.getLogger(__name__)

class ReportsPage(ctk.CTkFrame):
    """Financial reports page"""

    def __init__(self, parent, app):
        """
        Initialize reports page

        Args:
            parent: Parent frame
            app: Application instance
        """
        super().__init__(parent)
        self.app = app
        self.language_manager = app.language_manager

        # Configure frame
        self.configure(fg_color="transparent")

        # Create placeholder content
        self.create_placeholder_content()

        logger.info("Reports page initialized")

    def create_placeholder_content(self):
        """Create placeholder content for reports page"""
        try:
            # Main container
            main_frame = ctk.CTkFrame(self)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

            # Title
            title_label = ctk.CTkLabel(
                main_frame,
                text=self.language_manager.get_text("reports.title"),
                font=ctk.CTkFont(size=24, weight="bold")
            )
            title_label.pack(pady=(20, 40))

            # Report types grid
            reports_grid = ctk.CTkFrame(main_frame, fg_color="transparent")
            reports_grid.pack(expand=True)

            # Define available reports
            reports = [
                {"name": self.language_manager.get_text("reports.general_ledger"), "icon": "📊"},
                {"name": self.language_manager.get_text("reports.trial_balance"), "icon": "⚖️"},
                {"name": self.language_manager.get_text("reports.cost_accounts"), "icon": "💰"},
                {"name": self.language_manager.get_text("reports.balance_sheet"), "icon": "📋"},
                {"name": self.language_manager.get_text("reports.income_statement"), "icon": "📈"},
                {"name": self.language_manager.get_text("reports.cash_flow"), "icon": "💵"}
            ]

            # Create report buttons
            for i, report in enumerate(reports):
                row = i // 3
                col = i % 3

                report_button = ctk.CTkButton(
                    reports_grid,
                    text=f"{report['icon']}\n{report['name']}",
                    width=150,
                    height=100,
                    state="disabled"
                )
                report_button.grid(row=row, column=col, padx=10, pady=10)

            # Configure grid weights
            for i in range(3):
                reports_grid.grid_columnconfigure(i, weight=1)

            # Development notice
            notice_label = ctk.CTkLabel(
                main_frame,
                text="🚧 Reports section is under development\n\nقسم التقارير قيد التطوير",
                font=ctk.CTkFont(size=12),
                text_color="gray"
            )
            notice_label.pack(pady=20)

        except Exception as e:
            logger.error(f"Failed to create reports placeholder: {e}")