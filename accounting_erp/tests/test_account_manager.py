#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Account Manager Tests
Unit tests for account management functionality
"""

import unittest
import sys
import os
import tempfile
import shutil
from datetime import datetime, date

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from managers.database_manager import DatabaseManager
from managers.account_manager import AccountManager
from error_handling import AccountingError, ValidationError

class TestAccountManager(unittest.TestCase):
    """Test cases for AccountManager"""

    def setUp(self):
        """Set up test environment"""
        # Create temporary database
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_accounting.db")

        # Initialize managers
        self.db_manager = DatabaseManager(self.db_path)
        self.account_manager = AccountManager(self.db_manager)

        # Create basic schema
        self.create_test_schema()

    def tearDown(self):
        """Clean up test environment"""
        try:
            if hasattr(self, 'db_manager'):
                self.db_manager.close_connection()
            shutil.rmtree(self.temp_dir)
        except:
            pass

    def create_test_schema(self):
        """Create basic test schema"""
        # Create accounts table
        self.db_manager.execute_query("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                parent_id INTEGER NULL,
                code TEXT UNIQUE NOT NULL,
                name_ar TEXT NOT NULL,
                name_en TEXT NOT NULL,
                account_type TEXT CHECK (account_type IN ('general', 'assistant', 'analytic')),
                account_category TEXT CHECK (account_category IN ('asset', 'liability', 'expense', 'revenue', 'equity')),
                level INTEGER NOT NULL,
                full_path TEXT,
                is_active BOOLEAN DEFAULT TRUE,
                opening_balance DECIMAL(15,2) DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (parent_id) REFERENCES accounts(id)
            )
        """, commit=True)

    def test_add_root_account(self):
        """Test adding a root account"""
        # Test adding asset root account
        account_id = self.account_manager.add_account(
            parent_id=None,
            name_ar="الأصول",
            name_en="Assets",
            account_type="general",
            account_category="asset",
            opening_balance=0.0
        )

        self.assertIsNotNone(account_id)
        self.assertGreater(account_id, 0)

        # Verify account was created
        account = self.account_manager.get_account_by_id(account_id)
        self.assertIsNotNone(account)
        self.assertEqual(account['name_ar'], "الأصول")
        self.assertEqual(account['name_en'], "Assets")
        self.assertEqual(account['account_type'], "general")
        self.assertEqual(account['account_category'], "asset")
        self.assertEqual(account['level'], 1)
        self.assertIsNone(account['parent_id'])

    def test_add_child_account(self):
        """Test adding a child account"""
        # First add parent account
        parent_id = self.account_manager.add_account(
            parent_id=None,
            name_ar="الأصول",
            name_en="Assets",
            account_type="general",
            account_category="asset"
        )

        self.assertIsNotNone(parent_id)

        # Add child account
        child_id = self.account_manager.add_account(
            parent_id=parent_id,
            name_ar="الأصول المتداولة",
            name_en="Current Assets",
            account_type="general",
            account_category="asset"
        )

        self.assertIsNotNone(child_id)

        # Verify child account
        child_account = self.account_manager.get_account_by_id(child_id)
        self.assertEqual(child_account['parent_id'], parent_id)
        self.assertEqual(child_account['level'], 2)

    def test_generate_account_code(self):
        """Test automatic account code generation"""
        # Test root level code generation
        code1 = self.account_manager.generate_account_code(None)
        self.assertEqual(code1, "1")

        # Add account and test child code generation
        parent_id = self.account_manager.add_account(
            parent_id=None,
            name_ar="الأصول",
            name_en="Assets",
            account_type="general",
            account_category="asset"
        )

        child_code = self.account_manager.generate_account_code(parent_id)
        self.assertEqual(child_code, "101")

        # Add another child
        child_id = self.account_manager.add_account(
            parent_id=parent_id,
            name_ar="الأصول غير المتداولة",
            name_en="Non-Current Assets",
            account_type="general",
            account_category="asset"
        )

        third_code = self.account_manager.generate_account_code(parent_id)
        self.assertEqual(third_code, "103")

    def test_account_hierarchy_validation(self):
        """Test account hierarchy validation rules"""
        # Add parent account
        parent_id = self.account_manager.add_account(
            parent_id=None,
            name_ar="الأصول",
            name_en="Assets",
            account_type="general",
            account_category="asset"
        )

        # Test adding analytic child to general parent (should work)
        is_valid = self.account_manager.validate_account_hierarchy(parent_id, "analytic")
        self.assertTrue(is_valid)

        # Add assistant account
        assistant_id = self.account_manager.add_account(
            parent_id=parent_id,
            name_ar="النقدية",
            name_en="Cash",
            account_type="assistant",
            account_category="asset"
        )

        # Test adding analytic child to assistant parent (should work)
        is_valid = self.account_manager.validate_account_hierarchy(assistant_id, "analytic")
        self.assertTrue(is_valid)

        # Test adding general child to assistant parent (should fail)
        is_valid = self.account_manager.validate_account_hierarchy(assistant_id, "general")
        self.assertFalse(is_valid)

        # Test adding child to analytic parent (should fail)
        analytic_id = self.account_manager.add_account(
            parent_id=assistant_id,
            name_ar="النقدية المحلية",
            name_en="Local Cash",
            account_type="analytic",
            account_category="asset"
        )

        is_valid = self.account_manager.validate_account_hierarchy(analytic_id, "analytic")
        self.assertFalse(is_valid)

    def test_duplicate_account_names(self):
        """Test validation for duplicate account names"""
        # Add parent account
        parent_id = self.account_manager.add_account(
            parent_id=None,
            name_ar="الأصول",
            name_en="Assets",
            account_type="general",
            account_category="asset"
        )

        # Add first child
        child1_id = self.account_manager.add_account(
            parent_id=parent_id,
            name_ar="النقدية",
            name_en="Cash",
            account_type="assistant",
            account_category="asset"
        )

        self.assertIsNotNone(child1_id)

        # Try to add duplicate child (should fail)
        child2_id = self.account_manager.add_account(
            parent_id=parent_id,
            name_ar="النقدية",
            name_en="Cash",
            account_type="assistant",
            account_category="asset"
        )

        self.assertIsNone(child2_id)

    def test_update_account(self):
        """Test updating account information"""
        # Add account
        account_id = self.account_manager.add_account(
            parent_id=None,
            name_ar="اختبار",
            name_en="Test",
            account_type="general",
            account_category="asset"
        )

        # Update account
        success = self.account_manager.update_account(
            account_id,
            name_ar="اختبار محدث",
            name_en="Test Updated"
        )

        self.assertTrue(success)

        # Verify update
        updated_account = self.account_manager.get_account_by_id(account_id)
        self.assertEqual(updated_account['name_ar'], "اختبار محدث")
        self.assertEqual(updated_account['name_en'], "Test Updated")

    def test_delete_account(self):
        """Test deleting account"""
        # Add account
        account_id = self.account_manager.add_account(
            parent_id=None,
            name_ar="اختبار للحذف",
            name_en="Test for Delete",
            account_type="general",
            account_category="asset"
        )

        self.assertIsNotNone(account_id)

        # Delete account
        success = self.account_manager.delete_account(account_id)
        self.assertTrue(success)

        # Verify deletion
        deleted_account = self.account_manager.get_account_by_id(account_id)
        self.assertIsNone(deleted_account)

    def test_delete_account_with_children(self):
        """Test deleting account with children (should fail)"""
        # Add parent account
        parent_id = self.account_manager.add_account(
            parent_id=None,
            name_ar="أب",
            name_en="Parent",
            account_type="general",
            account_category="asset"
        )

        # Add child account
        child_id = self.account_manager.add_account(
            parent_id=parent_id,
            name_ar="ابن",
            name_en="Child",
            account_type="assistant",
            account_category="asset"
        )

        # Try to delete parent (should fail)
        success = self.account_manager.delete_account(parent_id)
        self.assertFalse(success)

        # Child should still exist
        child_account = self.account_manager.get_account_by_id(child_id)
        self.assertIsNotNone(child_account)

    def test_get_accounts_tree(self):
        """Test retrieving accounts tree structure"""
        # Create test hierarchy
        root_id = self.account_manager.add_account(
            parent_id=None,
            name_ar="الأصول",
            name_en="Assets",
            account_type="general",
            account_category="asset"
        )

        child_id = self.account_manager.add_account(
            parent_id=root_id,
            name_ar="الأصول المتداولة",
            name_en="Current Assets",
            account_type="general",
            account_category="asset"
        )

        grandchild_id = self.account_manager.add_account(
            parent_id=child_id,
            name_ar="النقدية",
            name_en="Cash",
            account_type="assistant",
            account_category="asset"
        )

        # Get tree
        tree = self.account_manager.get_accounts_tree()
        self.assertEqual(len(tree), 1)  # One root account

        root_account = tree[0]
        self.assertEqual(root_account['name_ar'], "الأصول")
        self.assertEqual(len(root_account['children']), 1)

        child_account = root_account['children'][0]
        self.assertEqual(child_account['name_ar'], "الأصول المتداولة")
        self.assertEqual(len(child_account['children']), 1)

        grandchild_account = child_account['children'][0]
        self.assertEqual(grandchild_account['name_ar'], "النقدية")

    def test_search_accounts(self):
        """Test account search functionality"""
        # Add test accounts
        self.account_manager.add_account(
            parent_id=None,
            name_ar="الأصول",
            name_en="Assets",
            account_type="general",
            account_category="asset"
        )

        self.account_manager.add_account(
            parent_id=None,
            name_ar="الخصوم",
            name_en="Liabilities",
            account_type="general",
            account_category="liability"
        )

        # Search by Arabic name
        results = self.account_manager.search_accounts("أص", "name")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name_ar'], "الأصول")

        # Search by English name
        results = self.account_manager.search_accounts("Asset", "name")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]['name_en'], "Assets")

        # Search by code (if exists)
        results = self.account_manager.search_accounts("1", "code")
        self.assertEqual(len(results), 1)

    def test_get_account_balance(self):
        """Test getting account balance"""
        # Add account with opening balance
        account_id = self.account_manager.add_account(
            parent_id=None,
            name_ar="حساب اختبار",
            name_en="Test Account",
            account_type="assistant",
            account_category="asset",
            opening_balance=1000.0
        )

        # Get balance (should be opening balance with no transactions)
        balance_info = self.account_manager.get_account_balance(account_id)
        self.assertIsNotNone(balance_info)
        self.assertEqual(balance_info['opening_balance'], 1000.0)
        self.assertEqual(balance_info['current_balance'], 1000.0)

    def test_account_category_translation(self):
        """Test account category translations"""
        # Test Arabic translations
        arabic_asset = self.account_manager.language_manager.get_account_category_translation('asset')
        self.assertEqual(arabic_asset, "أصل")

        # Test English translations
        english_asset = self.account_manager.language_manager.get_account_category_translation('asset', 'en')
        self.assertEqual(english_asset, "Asset")

    def test_account_type_translation(self):
        """Test account type translations"""
        # Test Arabic translations
        arabic_general = self.account_manager.language_manager.get_account_type_translation('general')
        self.assertEqual(arabic_general, "عام")

        # Test English translations
        english_general = self.account_manager.language_manager.get_account_type_translation('general', 'en')
        self.assertEqual(english_general, "General")

    def test_invalid_inputs(self):
        """Test handling of invalid inputs"""
        # Test empty names
        account_id = self.account_manager.add_account(
            parent_id=None,
            name_ar="",  # Empty name
            name_en="Test",
            account_type="general",
            account_category="asset"
        )
        self.assertIsNone(account_id)

        # Test invalid account type
        account_id = self.account_manager.add_account(
            parent_id=None,
            name_ar="اختبار",
            name_en="Test",
            account_type="invalid_type",
            account_category="asset"
        )
        self.assertIsNone(account_id)

        # Test invalid account category
        account_id = self.account_manager.add_account(
            parent_id=None,
            name_ar="اختبار",
            name_en="Test",
            account_type="general",
            account_category="invalid_category"
        )
        self.assertIsNone(account_id)


if __name__ == '__main__':
    # Set up test environment
    unittest.main(verbosity=2)