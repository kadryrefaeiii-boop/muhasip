#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Journal Manager Tests
Unit tests for journal entries management
"""

import unittest
import sys
import os
import tempfile
import shutil
from datetime import datetime, date
from decimal import Decimal

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from managers.database_manager import DatabaseManager
from managers.journal_manager import JournalManager
from managers.account_manager import AccountManager
from error_handling import AccountingError, ValidationError

class TestJournalManager(unittest.TestCase):
    """Test cases for JournalManager"""

    def setUp(self):
        """Set up test environment"""
        # Create temporary database
        self.temp_dir = tempfile.mkdtemp()
        self.db_path = os.path.join(self.temp_dir, "test_journal.db")

        # Initialize managers
        self.db_manager = DatabaseManager(self.db_path)
        self.journal_manager = JournalManager(self.db_manager)
        self.account_manager = AccountManager(self.db_manager)

        # Create test schema
        self.create_test_schema()

        # Create test accounts
        self.create_test_accounts()

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
        # Create fiscal years table
        self.db_manager.execute_query("""
            CREATE TABLE IF NOT EXISTS fiscal_years (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                start_date DATE NOT NULL,
                end_date DATE NOT NULL,
                is_active BOOLEAN DEFAULT FALSE
            )
        """, commit=True)

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
                opening_balance DECIMAL(15,2) DEFAULT 0,
                is_active BOOLEAN DEFAULT TRUE
            )
        """, commit=True)

        # Create journal entries table
        self.db_manager.execute_query("""
            CREATE TABLE IF NOT EXISTS journal_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_number TEXT UNIQUE NOT NULL,
                date DATE NOT NULL,
                description TEXT,
                fiscal_year_id INTEGER NOT NULL,
                total_debit DECIMAL(15,2) NOT NULL DEFAULT 0,
                total_credit DECIMAL(15,2) NOT NULL DEFAULT 0,
                status TEXT CHECK (status IN ('draft', 'posted', 'approved')) DEFAULT 'draft'
            )
        """, commit=True)

        # Create journal lines table
        self.db_manager.execute_query("""
            CREATE TABLE IF NOT EXISTS journal_lines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id INTEGER NOT NULL,
                account_id INTEGER NOT NULL,
                line_number INTEGER NOT NULL,
                description TEXT,
                debit DECIMAL(15,2) DEFAULT 0,
                credit DECIMAL(15,2) DEFAULT 0,
                UNIQUE(entry_id, line_number)
            )
        """, commit=True)

    def create_test_accounts(self):
        """Create test accounts"""
        # Create fiscal year
        fiscal_year_id = self.db_manager.insert_record("fiscal_years", {
            "name": "Test Fiscal Year",
            "start_date": date(2024, 1, 1),
            "end_date": date(2024, 12, 31),
            "is_active": True
        })
        self.fiscal_year_id = fiscal_year_id

        # Create cash account
        cash_id = self.db_manager.insert_record("accounts", {
            "code": "101",
            "name_ar": "النقدية",
            "name_en": "Cash",
            "account_type": "assistant",
            "account_category": "asset",
            "level": 1,
            "opening_balance": 5000.0
        })
        self.cash_id = cash_id

        # Create expense account
        expense_id = self.db_manager.insert_record("accounts", {
            "code": "301",
            "name_ar": "مصروفات",
            "name_en": "Expenses",
            "account_type": "general",
            "account_category": "expense",
            "level": 1,
            "opening_balance": 0.0
        })
        self.expense_id = expense_id

        # Create revenue account
        revenue_id = self.db_manager.insert_record("accounts", {
            "code": "401",
            "name_ar": "الإيرادات",
            "name_en": "Revenue",
            "account_type": "general",
            "account_category": "revenue",
            "level": 1,
            "opening_balance": 0.0
        })
        self.revenue_id = revenue_id

    def test_create_journal_entry(self):
        """Test creating a journal entry"""
        # Create simple entry lines
        lines = [
            {"account_id": self.cash_id, "debit": 1000.0, "credit": 0.0, "description": "Cash received"},
            {"account_id": self.revenue_id, "debit": 0.0, "credit": 1000.0, "description": "Service revenue"}
        ]

        entry_id = self.journal_manager.create_entry(
            date=date.today(),
            description="Test journal entry",
            lines=lines,
            fiscal_year_id=self.fiscal_year_id
        )

        self.assertIsNotNone(entry_id)
        self.assertGreater(entry_id, 0)

        # Verify entry was created
        entry = self.journal_manager.get_entry_details(entry_id)
        self.assertIsNotNone(entry)
        self.assertEqual(entry['description'], "Test journal entry")
        self.assertEqual(entry['status'], "draft")

    def test_validate_journal_entry(self):
        """Test journal entry validation"""
        # Test valid entry
        lines = [
            {"account_id": self.cash_id, "debit": 500.0, "credit": 0.0},
            {"account_id": self.expense_id, "debit": 0.0, "credit": 500.0}
        ]

        validation = self.journal_manager.validate_entry(lines)
        self.assertTrue(validation['valid'])
        self.assertIsNone(validation['error'])

        # Test invalid entry (debit != credit)
        invalid_lines = [
            {"account_id": self.cash_id, "debit": 500.0, "credit": 0.0},
            {"account_id": self.expense_id, "debit": 0.0, "credit": 400.0}
        ]

        validation = self.journal_manager.validate_entry(invalid_lines)
        self.assertFalse(validation['valid'])
        self.assertIsNotNone(validation['error'])

        # Test entry with no lines
        validation = self.journal_manager.validate_entry([])
        self.assertFalse(validation['valid'])
        self.assertIsNotNone(validation['error'])

    def test_generate_entry_number(self):
        """Test entry number generation"""
        # Generate first number
        number1 = self.journal_manager.generate_entry_number(self.fiscal_year_id)
        self.assertEqual(number1, "JE-000001")

        # Create an entry
        lines = [
            {"account_id": self.cash_id, "debit": 100.0, "credit": 0.0},
            {"account_id": self.revenue_id, "debit": 0.0, "credit": 100.0}
        ]
        self.journal_manager.create_entry(
            date=date.today(),
            description="Test",
            lines=lines,
            fiscal_year_id=self.fiscal_year_id
        )

        # Generate next number
        number2 = self.journal_manager.generate_entry_number(self.fiscal_year_id)
        self.assertEqual(number2, "JE-000002")

    def test_post_journal_entry(self):
        """Test posting a journal entry"""
        # Create entry
        lines = [
            {"account_id": self.cash_id, "debit": 2000.0, "credit": 0.0},
            {"account_id": self.revenue_id, "debit": 0.0, "credit": 2000.0}
        ]

        entry_id = self.journal_manager.create_entry(
            date=date.today(),
            description="Test posting",
            lines=lines,
            fiscal_year_id=self.fiscal_year_id
        )

        self.assertIsNotNone(entry_id)

        # Post the entry
        success = self.journal_manager.post_entry(entry_id, 1)
        self.assertTrue(success)

        # Verify status changed
        entry = self.journal_manager.get_entry_details(entry_id)
        self.assertEqual(entry['status'], "posted")

    def test_approve_journal_entry(self):
        """Test approving a journal entry"""
        # Create and post entry first
        lines = [
            {"account_id": self.cash_id, "debit": 1500.0, "credit": 0.0},
            {"account_id": self.revenue_id, "debit": 0.0, "credit": 1500.0}
        ]

        entry_id = self.journal_manager.create_entry(
            date=date.today(),
            description="Test approval",
            lines=lines,
            fiscal_year_id=self.fiscal_year_id
        )

        self.journal_manager.post_entry(entry_id, 1)

        # Approve the entry
        success = self.journal_manager.approve_entry(entry_id, 1)
        self.assertTrue(success)

        # Verify status changed
        entry = self.journal_manager.get_entry_details(entry_id)
        self.assertEqual(entry['status'], "approved")

    def test_delete_journal_entry(self):
        """Test deleting a journal entry"""
        # Create draft entry
        lines = [
            {"account_id": self.cash_id, "debit": 300.0, "credit": 0.0},
            {"account_id": self.expense_id, "debit": 0.0, "credit": 300.0}
        ]

        entry_id = self.journal_manager.create_entry(
            date=date.today(),
            description="Test delete",
            lines=lines,
            fiscal_year_id=self.fiscal_year_id
        )

        self.assertIsNotNone(entry_id)

        # Delete entry
        success = self.journal_manager.delete_entry(entry_id, "Test deletion")
        self.assertTrue(success)

        # Verify deletion
        entry = self.journal_manager.get_entry_details(entry_id)
        self.assertIsNone(entry)

    def test_delete_posted_entry(self):
        """Test that posted entries cannot be deleted"""
        # Create and post entry
        lines = [
            {"account_id": self.cash_id, "debit": 400.0, "credit": 0.0},
            {"account_id": self.revenue_id, "debit": 0.0, "credit": 400.0}
        ]

        entry_id = self.journal_manager.create_entry(
            date=date.today(),
            description="Test posted delete",
            lines=lines,
            fiscal_year_id=self.fiscal_year_id
        )

        self.journal_manager.post_entry(entry_id, 1)

        # Try to delete posted entry (should fail)
        success = self.journal_manager.delete_entry(entry_id)
        self.assertFalse(success)

    def test_get_entry_lines(self):
        """Test getting journal entry lines"""
        # Create entry with multiple lines
        lines = [
            {"account_id": self.cash_id, "debit": 1000.0, "credit": 0.0, "description": "Cash"},
            {"account_id": self.revenue_id, "debit": 0.0, "credit": 600.0, "description": "Revenue 1"},
            {"account_id": self.revenue_id, "debit": 0.0, "credit": 400.0, "description": "Revenue 2"}
        ]

        entry_id = self.journal_manager.create_entry(
            date=date.today(),
            description="Test multiple lines",
            lines=lines,
            fiscal_year_id=self.fiscal_year_id
        )

        # Get lines
        entry_lines = self.journal_manager.get_entry_lines(entry_id)
        self.assertEqual(len(entry_lines), 3)

        # Verify line numbers
        for i, line in enumerate(entry_lines):
            self.assertEqual(line['line_number'], i + 1)

    def test_update_journal_entry(self):
        """Test updating journal entry"""
        # Create draft entry
        lines = [
            {"account_id": self.cash_id, "debit": 500.0, "credit": 0.0},
            {"account_id": self.revenue_id, "debit": 0.0, "credit": 500.0}
        ]

        entry_id = self.journal_manager.create_entry(
            date=date.today(),
            description="Original description",
            lines=lines,
            fiscal_year_id=self.fiscal_year_id
        )

        # Update description
        success = self.journal_manager.update_entry(
            entry_id,
            description="Updated description"
        )
        self.assertTrue(success)

        # Verify update
        entry = self.journal_manager.get_entry_details(entry_id)
        self.assertEqual(entry['description'], "Updated description")

    def test_update_posted_entry(self):
        """Test that posted entries cannot be updated"""
        # Create and post entry
        lines = [
            {"account_id": self.cash_id, "debit": 600.0, "credit": 0.0},
            {"account_id": self.revenue_id, "debit": 0.0, "credit": 600.0}
        ]

        entry_id = self.journal_manager.create_entry(
            date=date.today(),
            description="Original",
            lines=lines,
            fiscal_year_id=self.fiscal_year_id
        )

        self.journal_manager.post_entry(entry_id, 1)

        # Try to update posted entry (should fail)
        success = self.journal_manager.update_entry(
            entry_id,
            description="Updated"
        )
        self.assertFalse(success)

    def test_get_entries_with_filters(self):
        """Test getting entries with filters"""
        # Create multiple entries
        for i in range(5):
            lines = [
                {"account_id": self.cash_id, "debit": 100.0 * (i + 1), "credit": 0.0},
                {"account_id": self.revenue_id, "debit": 0.0, "credit": 100.0 * (i + 1)}
            ]

            self.journal_manager.create_entry(
                date=date(2024, 1, 1 + i),
                description=f"Test entry {i + 1}",
                lines=lines,
                fiscal_year_id=self.fiscal_year_id
            )

        # Get all entries
        all_entries = self.journal_manager.get_entries()
        self.assertEqual(len(all_entries), 5)

        # Filter by status
        draft_entries = self.journal_manager.get_entries({"status": "draft"})
        self.assertEqual(len(draft_entries), 5)

        # Post first entry
        posted_entries = self.journal_manager.get_entries()
        self.journal_manager.post_entry(posted_entries[0]['id'], 1)

        posted_filter = self.journal_manager.get_entries({"status": "posted"})
        self.assertEqual(len(posted_filter), 1)

    def test_calculate_entry_totals(self):
        """Test calculating entry totals"""
        lines = [
            {"account_id": self.cash_id, "debit": 1000.0, "credit": 0.0},
            {"account_id": self.revenue_id, "debit": 0.0, "credit": 600.0},
            {"account_id": self.revenue_id, "debit": 0.0, "credit": 400.0}
        ]

        totals = self.journal_manager._calculate_entry_totals(lines)
        self.assertEqual(totals['debit'], 1000.0)
        self.assertEqual(totals['credit'], 1000.0)

    def test_validate_journal_line(self):
        """Test individual journal line validation"""
        # Valid line
        valid_line = {
            "account_id": self.cash_id,
            "debit": 500.0,
            "credit": 0.0
        }

        validation = self.journal_manager._validate_journal_line(valid_line)
        self.assertTrue(validation['valid'])

        # Invalid line (no account_id)
        invalid_line = {
            "debit": 500.0,
            "credit": 0.0
        }

        validation = self.journal_manager._validate_journal_line(invalid_line)
        self.assertFalse(validation['valid'])

        # Invalid line (both debit and credit)
        invalid_line = {
            "account_id": self.cash_id,
            "debit": 500.0,
            "credit": 100.0
        }

        validation = self.journal_manager._validate_journal_line(invalid_line)
        self.assertFalse(validation['valid'])

    def test_double_entry_compliance(self):
        """Test that all entries maintain double-entry balance"""
        # Create multiple entries and verify balance
        for i in range(10):
            amount = (i + 1) * 100
            lines = [
                {"account_id": self.cash_id, "debit": amount, "credit": 0.0},
                {"account_id": self.revenue_id, "debit": 0.0, "credit": amount}
            ]

            entry_id = self.journal_manager.create_entry(
                date=date.today(),
                description=f"Balance test {i + 1}",
                lines=lines,
                fiscal_year_id=self.fiscal_year_id
            )

            # Get entry and verify balance
            entry = self.journal_manager.get_entry_details(entry_id)
            self.assertEqual(entry['total_debit'], entry['total_credit'])

    def test_get_fiscal_year_entries(self):
        """Test getting entries for specific fiscal year"""
        # Create entries in current fiscal year
        lines = [
            {"account_id": self.cash_id, "debit": 100.0, "credit": 0.0},
            {"account_id": self.revenue_id, "debit": 0.0, "credit": 100.0}
        ]

        self.journal_manager.create_entry(
            date=date.today(),
            description="Fiscal year test",
            lines=lines,
            fiscal_year_id=self.fiscal_year_id
        )

        # Get fiscal year entries
        fiscal_entries = self.journal_manager.get_fiscal_year_entries(self.fiscal_year_id)
        self.assertEqual(len(fiscal_entries), 1)


if __name__ == '__main__':
    # Set up test environment
    unittest.main(verbosity=2)