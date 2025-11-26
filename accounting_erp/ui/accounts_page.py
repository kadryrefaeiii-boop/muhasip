#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Accounts Page
Complete accounts management page
"""

import customtkinter as ctk
import logging

logger = logging.getLogger(__name__)

class AccountsPage(ctk.CTkFrame):
    """Accounts management page"""

    def __init__(self, parent, app):
        """
        Initialize accounts page

        Args:
            parent: Parent frame
            app: Application instance
        """
        super().__init__(parent)
        self.app = app
        self.language_manager = app.language_manager

        # Configure frame
        self.configure(fg_color="transparent")

        # Create accounts tree
        from ui.accounts_tree import AccountsTree
        self.accounts_tree = AccountsTree(self, app)
        self.accounts_tree.pack(fill=tk.BOTH, expand=True)

        logger.info("Accounts page initialized")