#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Journal Page
Journal entries management page
"""

import customtkinter as ctk
import logging

logger = logging.getLogger(__name__)

class JournalPage(ctk.CTkFrame):
    """Journal entries management page"""

    def __init__(self, parent, app):
        """
        Initialize journal page

        Args:
            parent: Parent frame
            app: Application instance
        """
        super().__init__(parent)
        self.app = app
        self.language_manager = app.language_manager

        # Configure frame
        self.configure(fg_color="transparent")

        # Create placeholder content for now
        self.create_placeholder_content()

        logger.info("Journal page initialized")

    def create_placeholder_content(self):
        """Create placeholder content for journal page"""
        try:
            # Main container
            main_frame = ctk.CTkFrame(self)
            main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

            # Title
            title_label = ctk.CTkLabel(
                main_frame,
                text=self.language_manager.get_text("journal.title"),
                font=ctk.CTkFont(size=24, weight="bold")
            )
            title_label.pack(pady=(20, 40))

            # Placeholder message
            placeholder_label = ctk.CTkLabel(
                main_frame,
                text="📝 Journal Entries Management\n\nقيد إدارة القيود اليومية\n\nThis page will contain:\n• New journal entry creation\n• Journal entry list with filters\n• Double-entry validation\n• Entry posting and approval workflows",
                font=ctk.CTkFont(size=14),
                text_color="gray"
            )
            placeholder_label.pack(expand=True)

            # Action button
            action_button = ctk.CTkButton(
                main_frame,
                text="🚧 Under Development / قيد التطوير",
                state="disabled",
                width=200,
                height=40
            )
            action_button.pack(pady=20)

        except Exception as e:
            logger.error(f"Failed to create journal placeholder: {e}")