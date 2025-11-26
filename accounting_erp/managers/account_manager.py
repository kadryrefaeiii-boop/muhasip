#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Account Manager
Chart of Accounts management with hierarchical support
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import re

logger = logging.getLogger(__name__)

class AccountManager:
    """Chart of Accounts management with hierarchical support"""

    def __init__(self, db_manager):
        """
        Initialize Account Manager

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        logger.info("Account Manager initialized")

    def add_account(
        self,
        parent_id: Optional[int],
        name_ar: str,
        name_en: str,
        account_type: str,
        account_category: str,
        opening_balance: float = 0.0,
        created_by: Optional[int] = None
    ) -> Optional[int]:
        """
        Add new account to Chart of Accounts

        Args:
            parent_id: Parent account ID (None for root accounts)
            name_ar: Account name in Arabic
            name_en: Account name in English
            account_type: Account type ('general', 'assistant', 'analytic')
            account_category: Account category ('asset', 'liability', 'expense', 'revenue', 'equity')
            opening_balance: Opening balance
            created_by: User ID who created the account

        Returns:
            New account ID or None if failed
        """
        try:
            # Validate inputs
            if not self._validate_account_inputs(parent_id, name_ar, name_en, account_type, account_category):
                return None

            # Generate account code
            code = self.generate_account_code(parent_id)
            if not code:
                logger.error("Failed to generate account code")
                return None

            # Determine account level
            level = self._get_account_level(parent_id)

            # Create full path
            full_path = self._generate_full_path(parent_id, name_ar)

            account_data = {
                "parent_id": parent_id,
                "code": code,
                "name_ar": name_ar,
                "name_en": name_en,
                "account_type": account_type,
                "account_category": account_category,
                "level": level,
                "full_path": full_path,
                "opening_balance": opening_balance,
                "current_balance": opening_balance,
                "created_by": created_by
            }

            account_id = self.db_manager.insert_record("accounts", account_data)

            if account_id:
                logger.info(f"Account '{name_ar}' created successfully with ID: {account_id}")

                # Update parent account status if needed
                self._update_parent_account_status(parent_id)

                # Log the action
                self._log_account_action("CREATE", account_id, None, account_data, created_by)

            return account_id

        except Exception as e:
            logger.error(f"Failed to add account: {e}")
            return None

    def _validate_account_inputs(
        self,
        parent_id: Optional[int],
        name_ar: str,
        name_en: str,
        account_type: str,
        account_category: str
    ) -> bool:
        """Validate account creation inputs"""

        # Validate required fields
        if not name_ar or not name_en:
            logger.error("Account names cannot be empty")
            return False

        if not account_type or account_type not in ['general', 'assistant', 'analytic']:
            logger.error(f"Invalid account type: {account_type}")
            return False

        if not account_category or account_category not in ['asset', 'liability', 'expense', 'revenue', 'equity']:
            logger.error(f"Invalid account category: {account_category}")
            return False

        # Validate account hierarchy rules
        if parent_id:
            parent_account = self.get_account_by_id(parent_id)
            if not parent_account:
                logger.error(f"Parent account not found: {parent_id}")
                return False

            # Check hierarchy validation rules
            if not self.validate_account_hierarchy(parent_id, account_type):
                return False

        # Validate name uniqueness within parent
        if not self._validate_name_uniqueness(parent_id, name_ar):
            logger.error(f"Account name '{name_ar}' already exists under parent")
            return False

        return True

    def validate_account_hierarchy(self, parent_id: int, account_type: str) -> bool:
        """
        Validate account hierarchy rules

        Args:
            parent_id: Parent account ID
            account_type: New account type

        Returns:
            True if hierarchy rules are valid
        """
        try:
            parent_account = self.get_account_by_id(parent_id)
            if not parent_account:
                return False

            parent_type = parent_account['account_type']

            # Hierarchy rules:
            # General account can have any type of children
            # Assistant account can only have analytic children
            # Analytic account cannot have children
            if parent_type == 'analytic':
                logger.error("Analytic accounts cannot have children")
                return False
            elif parent_type == 'assistant' and account_type != 'analytic':
                logger.error("Assistant accounts can only have analytic children")
                return False

            # Check maximum level (prevent too deep hierarchy)
            if parent_account['level'] >= 9:
                logger.error("Account hierarchy level too deep (max 9 levels)")
                return False

            return True

        except Exception as e:
            logger.error(f"Hierarchy validation failed: {e}")
            return False

    def _validate_name_uniqueness(self, parent_id: Optional[int], name_ar: str) -> bool:
        """Check if account name is unique within parent"""

        try:
            if parent_id:
                query = """
                    SELECT id FROM accounts
                    WHERE parent_id = ? AND name_ar = ? AND is_active = 1
                """
                params = (parent_id, name_ar)
            else:
                query = """
                    SELECT id FROM accounts
                    WHERE parent_id IS NULL AND name_ar = ? AND is_active = 1
                """
                params = (name_ar,)

            existing = self.db_manager.execute_query(query, params, fetch_one=True)
            return existing is None

        except Exception as e:
            logger.error(f"Name uniqueness validation failed: {e}")
            return False

    def generate_account_code(self, parent_id: Optional[int]) -> Optional[str]:
        """
        Generate account code based on parent

        Args:
            parent_id: Parent account ID

        Returns:
            Generated account code or None if failed
        """
        try:
            if parent_id:
                # Get parent account
                parent_account = self.get_account_by_id(parent_id)
                if not parent_account:
                    return None

                parent_code = parent_account['code']
                parent_level = parent_account['level']

                # Find the last child code
                query = """
                    SELECT code FROM accounts
                    WHERE parent_id = ? AND is_active = 1
                    ORDER BY code DESC
                    LIMIT 1
                """
                last_child = self.db_manager.execute_query(query, (parent_id,), fetch_one=True)

                if last_child:
                    last_code = last_child['code']
                    # Extract the last 2 digits and increment
                    last_number = int(last_code[-2:])
                    new_number = last_number + 1
                else:
                    new_number = 1

                # Generate new code (add 2 digits for each level)
                if parent_level == 0:  # Root level
                    new_code = str(new_number)
                else:
                    new_code = f"{parent_code}{new_number:02d}"

                # Check if code doesn't exceed 99 for this level
                if new_number > 99:
                    logger.error(f"Cannot create more than 99 accounts under parent {parent_code}")
                    return None

                return new_code

            else:
                # Root level - generate code for main categories
                query = """
                    SELECT code FROM accounts
                    WHERE parent_id IS NULL AND is_active = 1
                    ORDER BY code DESC
                    LIMIT 1
                """
                last_root = self.db_manager.execute_query(query, fetch_one=True)

                if last_root:
                    last_code = int(last_root['code'])
                    new_code = str(last_code + 1)
                else:
                    new_code = "1"  # Start with Assets

                return new_code

        except Exception as e:
            logger.error(f"Account code generation failed: {e}")
            return None

    def _get_account_level(self, parent_id: Optional[int]) -> int:
        """Get account level based on parent"""

        if not parent_id:
            return 1  # Root level

        try:
            parent_account = self.get_account_by_id(parent_id)
            if parent_account:
                return parent_account['level'] + 1
            return 1

        except Exception as e:
            logger.error(f"Failed to get account level: {e}")
            return 1

    def _generate_full_path(self, parent_id: Optional[int], name_ar: str) -> str:
        """Generate full hierarchical path for account"""

        if not parent_id:
            return name_ar

        try:
            parent_account = self.get_account_by_id(parent_id)
            if parent_account and parent_account['full_path']:
                return f"{parent_account['full_path']} > {name_ar}"
            else:
                return name_ar

        except Exception as e:
            logger.error(f"Failed to generate full path: {e}")
            return name_ar

    def update_account(self, account_id: int, **kwargs) -> bool:
        """
        Update account information

        Args:
            account_id: Account ID to update
            **kwargs: Fields to update

        Returns:
            True if update successful
        """
        try:
            # Get current account data for logging
            current_data = self.get_account_by_id(account_id)
            if not current_data:
                logger.error(f"Account not found: {account_id}")
                return False

            # Validate update data
            if not self._validate_update_data(account_id, kwargs):
                return False

            # Update account
            affected_rows = self.db_manager.update_record(
                "accounts",
                kwargs,
                "id = ?",
                (account_id,)
            )

            if affected_rows > 0:
                # Update full path if name changed
                if 'name_ar' in kwargs:
                    self._update_account_full_path(account_id)

                logger.info(f"Account {account_id} updated successfully")

                # Log the action
                self._log_account_action("UPDATE", account_id, current_data, kwargs, kwargs.get('updated_by'))

                return True

            return False

        except Exception as e:
            logger.error(f"Failed to update account: {e}")
            return False

    def _validate_update_data(self, account_id: int, update_data: Dict[str, Any]) -> bool:
        """Validate account update data"""

        # Cannot change parent if account has children
        if 'parent_id' in update_data:
            children = self.get_child_accounts(account_id)
            if children:
                logger.error("Cannot change parent of account with children")
                return False

        # Validate name uniqueness if name changed
        if 'name_ar' in update_data:
            account = self.get_account_by_id(account_id)
            if account and not self._validate_name_uniqueness(
                account['parent_id'], update_data['name_ar']
            ):
                return False

        return True

    def _update_account_full_path(self, account_id: int):
        """Update full path for account and all its children"""

        try:
            account = self.get_account_by_id(account_id)
            if not account:
                return

            new_path = self._generate_full_path(account['parent_id'], account['name_ar'])

            # Update current account
            self.db_manager.update_record(
                "accounts",
                {"full_path": new_path},
                "id = ?",
                (account_id,)
            )

            # Update all children recursively
            children = self.get_child_accounts(account_id)
            for child in children:
                self._update_account_full_path(child['id'])

        except Exception as e:
            logger.error(f"Failed to update full path: {e}")

    def delete_account(self, account_id: int, force: bool = False, deleted_by: Optional[int] = None) -> bool:
        """
        Delete account with validation

        Args:
            account_id: Account ID to delete
            force: Force deletion (skip some validations)
            deleted_by: User ID who deleted the account

        Returns:
            True if deletion successful
        """
        try:
            account = self.get_account_by_id(account_id)
            if not account:
                logger.error(f"Account not found: {account_id}")
                return False

            # Validate deletion rules
            if not force:
                if not self._validate_account_deletion(account_id):
                    return False

            # Check for journal entries
            if self._has_journal_entries(account_id):
                if not force:
                    logger.error("Cannot delete account with journal entries")
                    return False
                else:
                    logger.warning("Force deleting account with journal entries")

            # Delete children first if forcing
            if force:
                children = self.get_child_accounts(account_id)
                for child in children:
                    self.delete_account(child['id'], force=True, deleted_by=deleted_by)

            # Log before deletion
            self._log_account_action("DELETE", account_id, account, None, deleted_by)

            # Delete account
            affected_rows = self.db_manager.delete_record("accounts", "id = ?", (account_id,))

            if affected_rows > 0:
                logger.info(f"Account {account_id} deleted successfully")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to delete account: {e}")
            return False

    def _validate_account_deletion(self, account_id: int) -> bool:
        """Validate if account can be deleted"""

        try:
            # Check if account has children
            children = self.get_child_accounts(account_id)
            if children:
                logger.error("Cannot delete account with children")
                return False

            # Check for journal entries
            if self._has_journal_entries(account_id):
                logger.error("Cannot delete account with journal entries")
                return False

            return True

        except Exception as e:
            logger.error(f"Account deletion validation failed: {e}")
            return False

    def _has_journal_entries(self, account_id: int) -> bool:
        """Check if account has journal entries"""

        try:
            query = """
                SELECT COUNT(*) as count FROM journal_lines
                WHERE account_id = ?
            """
            result = self.db_manager.execute_query(query, (account_id,), fetch_one=True)
            return result['count'] > 0 if result else False

        except Exception as e:
            logger.error(f"Failed to check journal entries: {e}")
            return False

    def get_account_by_id(self, account_id: int) -> Optional[Dict[str, Any]]:
        """Get account by ID"""

        try:
            query = """
                SELECT a.*, u.username as created_by_name
                FROM accounts a
                LEFT JOIN users u ON a.created_by = u.id
                WHERE a.id = ?
            """
            result = self.db_manager.execute_query(query, (account_id,), fetch_one=True)
            return result

        except Exception as e:
            logger.error(f"Failed to get account by ID: {e}")
            return None

    def get_child_accounts(self, parent_id: int, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """Get child accounts of given parent"""

        try:
            query = """
                SELECT a.*, u.username as created_by_name
                FROM accounts a
                LEFT JOIN users u ON a.created_by = u.id
                WHERE a.parent_id = ?
            """

            if not include_inactive:
                query += " AND a.is_active = 1"

            query += " ORDER BY a.code"

            result = self.db_manager.execute_query(query, (parent_id,), fetch_all=True)
            return result or []

        except Exception as e:
            logger.error(f"Failed to get child accounts: {e}")
            return []

    def get_accounts_tree(self, parent_id: Optional[int] = None, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """Get complete accounts tree structure"""

        try:
            if parent_id:
                # Get children of specific parent
                accounts = self.get_child_accounts(parent_id, include_inactive)
            else:
                # Get root accounts
                query = """
                    SELECT a.*, u.username as created_by_name
                    FROM accounts a
                    LEFT JOIN users u ON a.created_by = u.id
                    WHERE a.parent_id IS NULL
                """

                if not include_inactive:
                    query += " AND a.is_active = 1"

                query += " ORDER BY a.code"

                result = self.db_manager.execute_query(query, fetch_all=True)
                accounts = result or []

            # Recursively build tree for each account
            for account in accounts:
                account['children'] = self.get_accounts_tree(account['id'], include_inactive)

            return accounts

        except Exception as e:
            logger.error(f"Failed to get accounts tree: {e}")
            return []

    def search_accounts(self, query: str, search_type: str = 'name') -> List[Dict[str, Any]]:
        """
        Search accounts by different criteria

        Args:
            query: Search query string
            search_type: Type of search ('name', 'code', 'all')

        Returns:
            List of matching accounts
        """
        try:
            query_param = f"%{query}%"

            if search_type == 'name':
                sql_query = """
                    SELECT a.*, u.username as created_by_name
                    FROM accounts a
                    LEFT JOIN users u ON a.created_by = u.id
                    WHERE (a.name_ar LIKE ? OR a.name_en LIKE ?)
                    AND a.is_active = 1
                    ORDER BY a.code
                """
                params = (query_param, query_param)

            elif search_type == 'code':
                sql_query = """
                    SELECT a.*, u.username as created_by_name
                    FROM accounts a
                    LEFT JOIN users u ON a.created_by = u.id
                    WHERE a.code LIKE ? AND a.is_active = 1
                    ORDER BY a.code
                """
                params = (query_param,)

            else:  # all
                sql_query = """
                    SELECT a.*, u.username as created_by_name
                    FROM accounts a
                    LEFT JOIN users u ON a.created_by = u.id
                    WHERE (a.name_ar LIKE ? OR a.name_en LIKE ? OR a.code LIKE ? OR a.full_path LIKE ?)
                    AND a.is_active = 1
                    ORDER BY a.code
                """
                params = (query_param, query_param, query_param, query_param)

            result = self.db_manager.execute_query(sql_query, params, fetch_all=True)
            return result or []

        except Exception as e:
            logger.error(f"Failed to search accounts: {e}")
            return []

    def get_accounts_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Get accounts by category"""

        try:
            query = """
                SELECT a.*, u.username as created_by_name
                FROM accounts a
                LEFT JOIN users u ON a.created_by = u.id
                WHERE a.account_category = ? AND a.is_active = 1
                ORDER BY a.code
            """
            result = self.db_manager.execute_query(query, (category,), fetch_all=True)
            return result or []

        except Exception as e:
            logger.error(f"Failed to get accounts by category: {e}")
            return []

    def get_account_balance(self, account_id: int, as_of_date: Optional[str] = None) -> Dict[str, float]:
        """
        Get account balance information

        Args:
            account_id: Account ID
            as_of_date: Calculate balance as of this date

        Returns:
            Dictionary with balance information
        """
        try:
            account = self.get_account_by_id(account_id)
            if not account:
                return {"opening_balance": 0, "current_balance": 0, "period_debit": 0, "period_credit": 0}

            # Get journal lines for the account
            query = """
                SELECT
                    SUM(CASE WHEN jl.debit > 0 THEN jl.debit ELSE 0 END) as total_debit,
                    SUM(CASE WHEN jl.credit > 0 THEN jl.credit ELSE 0 END) as total_credit
                FROM journal_lines jl
                JOIN journal_entries je ON jl.entry_id = je.id
                WHERE jl.account_id = ? AND je.status = 'posted'
            """

            params = (account_id,)
            if as_of_date:
                query += " AND je.date <= ?"
                params = (account_id, as_of_date)

            result = self.db_manager.execute_query(query, params, fetch_one=True)

            if result:
                total_debit = result['total_debit'] or 0
                total_credit = result['total_credit'] or 0
            else:
                total_debit = total_credit = 0

            # Calculate current balance based on account category
            opening_balance = account['opening_balance'] or 0

            if account['account_category'] in ['asset', 'expense']:
                current_balance = opening_balance + total_debit - total_credit
            else:  # liability, revenue, equity
                current_balance = opening_balance - total_debit + total_credit

            return {
                "opening_balance": opening_balance,
                "current_balance": current_balance,
                "period_debit": total_debit,
                "period_credit": total_credit
            }

        except Exception as e:
            logger.error(f"Failed to get account balance: {e}")
            return {"opening_balance": 0, "current_balance": 0, "period_debit": 0, "period_credit": 0}

    def _update_parent_account_status(self, parent_id: Optional[int]):
        """Update parent account status when children are added"""

        if not parent_id:
            return

        try:
            # This can be used for business logic like updating parent account type
            # or status when children are added/removed
            pass

        except Exception as e:
            logger.error(f"Failed to update parent account status: {e}")

    def _log_account_action(self, action: str, account_id: int, old_data: Optional[Dict], new_data: Optional[Dict], user_id: Optional[int]):
        """Log account-related actions"""

        try:
            import json
            from datetime import datetime

            audit_data = {
                "user_id": user_id,
                "action": f"ACCOUNT_{action}",
                "table_name": "accounts",
                "record_id": account_id,
                "old_values": json.dumps(old_data) if old_data else None,
                "new_values": json.dumps(new_data) if new_data else None,
                "timestamp": datetime.now()
            }

            self.db_manager.insert_record("audit_log", audit_data, return_id=False)

        except Exception as e:
            logger.error(f"Failed to log account action: {e}")

    def export_accounts(self, format: str = 'excel') -> Optional[str]:
        """Export accounts to specified format"""

        try:
            accounts = self.get_accounts_tree()

            if format.lower() == 'excel':
                # Use report manager for Excel export
                from .report_manager import ReportManager
                report_manager = ReportManager(self.db_manager)
                return report_manager.export_accounts_to_excel(accounts)
            else:
                logger.error(f"Unsupported export format: {format}")
                return None

        except Exception as e:
            logger.error(f"Failed to export accounts: {e}")
            return None

    def import_accounts(self, file_path: str, format: str = 'excel') -> Tuple[bool, str]:
        """Import accounts from file"""

        try:
            # This would implement account import functionality
            # For now, return placeholder
            return True, "Account import not implemented yet"

        except Exception as e:
            logger.error(f"Failed to import accounts: {e}")
            return False, str(e)