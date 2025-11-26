#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Initial Data
Default data for Professional Accounting ERP system
"""

import logging
from datetime import datetime, date
from typing import Dict, Any

logger = logging.getLogger(__name__)

def insert_initial_data(db_manager) -> bool:
    """
    Insert initial data for new database setup

    Args:
        db_manager: Database manager instance

    Returns:
        True if initial data inserted successfully
    """
    try:
        logger.info("Starting initial data insertion...")

        # Insert in proper order due to foreign key constraints
        insert_default_admin_user(db_manager)
        insert_initial_fiscal_years(db_manager)
        insert_initial_chart_of_accounts(db_manager)
        insert_default_reports(db_manager)

        logger.info("Initial data insertion completed successfully")
        return True

    except Exception as e:
        logger.error(f"Initial data insertion failed: {e}")
        return False

def insert_default_admin_user(db_manager):
    """Insert default admin user"""

    try:
        # Check if admin user already exists
        existing = db_manager.execute_query(
            "SELECT id FROM users WHERE username = 'admin'",
            fetch_one=True
        )

        if existing:
            logger.info("Admin user already exists")
            return

        # Hash password (using bcrypt placeholder for now)
        import hashlib
        password_hash = hashlib.sha256("admin123".encode()).hexdigest()

        admin_data = {
            "username": "admin",
            "password_hash": password_hash,
            "full_name": "مدير النظام / System Administrator",
            "email": "admin@accounting-erp.com",
            "role": "admin",
            "is_active": True
        }

        admin_id = db_manager.insert_record("users", admin_data)

        logger.info(f"Default admin user created with ID: {admin_id}")

    except Exception as e:
        logger.error(f"Failed to insert admin user: {e}")
        raise

def insert_initial_fiscal_years(db_manager):
    """Insert initial fiscal years"""

    try:
        current_year = datetime.now().year

        fiscal_years = [
            {
                "name": f"السنة المالية {current_year}",
                "description": f"Fiscal Year {current_year}",
                "start_date": date(current_year, 1, 1),
                "end_date": date(current_year, 12, 31),
                "is_active": True,
                "is_closed": False
            },
            {
                "name": f"السنة المالية {current_year - 1}",
                "description": f"Fiscal Year {current_year - 1}",
                "start_date": date(current_year - 1, 1, 1),
                "end_date": date(current_year - 1, 12, 31),
                "is_active": False,
                "is_closed": True
            }
        ]

        for fiscal_year in fiscal_years:
            # Check if fiscal year already exists
            existing = db_manager.execute_query(
                "SELECT id FROM fiscal_years WHERE name = ?",
                (fiscal_year["name"],),
                fetch_one=True
            )

            if not existing:
                fiscal_year_id = db_manager.insert_record("fiscal_years", fiscal_year)
                logger.info(f"Fiscal year '{fiscal_year['name']}' created with ID: {fiscal_year_id}")

    except Exception as e:
        logger.error(f"Failed to insert fiscal years: {e}")
        raise

def insert_initial_chart_of_accounts(db_manager):
    """Insert initial Chart of Accounts structure"""

    try:
        # Root accounts (Level 1)
        root_accounts = [
            {
                "parent_id": None,
                "code": "1",
                "name_ar": "الأصول",
                "name_en": "Assets",
                "account_type": "general",
                "account_category": "asset",
                "level": 1
            },
            {
                "parent_id": None,
                "code": "2",
                "name_ar": "الخصوم",
                "name_en": "Liabilities",
                "account_type": "general",
                "account_category": "liability",
                "level": 1
            },
            {
                "parent_id": None,
                "code": "3",
                "name_ar": "المصروفات",
                "name_en": "Expenses",
                "account_type": "general",
                "account_category": "expense",
                "level": 1
            },
            {
                "parent_id": None,
                "code": "4",
                "name_ar": "الإيرادات",
                "name_en": "Revenues",
                "account_type": "general",
                "account_category": "revenue",
                "level": 1
            },
            {
                "parent_id": None,
                "code": "5",
                "name_ar": "حقوق الملكية",
                "name_en": "Equity",
                "account_type": "general",
                "account_category": "equity",
                "level": 1
            }
        ]

        # Insert root accounts and track their IDs
        root_account_ids = {}
        for account in root_accounts:
            # Check if account already exists
            existing = db_manager.execute_query(
                "SELECT id FROM accounts WHERE code = ?",
                (account["code"],),
                fetch_one=True
            )

            if not existing:
                account_id = db_manager.insert_record("accounts", account)
                root_account_ids[account["code"]] = account_id
                logger.info(f"Root account '{account['name_ar']}' created with ID: {account_id}")
            else:
                root_account_ids[account["code"]] = existing["id"]

        # Asset sub-accounts (Level 2)
        asset_sub_accounts = [
            {
                "parent_id": root_account_ids["1"],
                "code": "101",
                "name_ar": "الأصول المتداولة",
                "name_en": "Current Assets",
                "account_type": "general",
                "account_category": "asset",
                "level": 2
            },
            {
                "parent_id": root_account_ids["1"],
                "code": "102",
                "name_ar": "الأصول غير المتداولة",
                "name_en": "Non-Current Assets",
                "account_type": "general",
                "account_category": "asset",
                "level": 2
            }
        ]

        asset_sub_ids = {}
        for account in asset_sub_accounts:
            existing = db_manager.execute_query(
                "SELECT id FROM accounts WHERE code = ?",
                (account["code"],),
                fetch_one=True
            )

            if not existing:
                account_id = db_manager.insert_record("accounts", account)
                asset_sub_ids[account["code"]] = account_id
                logger.info(f"Asset sub-account '{account['name_ar']}' created with ID: {account_id}")
            else:
                asset_sub_ids[account["code"]] = existing["id"]

        # Current Assets detailed accounts (Level 3)
        current_assets_accounts = [
            {
                "parent_id": asset_sub_ids["101"],
                "code": "10101",
                "name_ar": "النقدية والبنوك",
                "name_en": "Cash and Banks",
                "account_type": "assistant",
                "account_category": "asset",
                "level": 3
            },
            {
                "parent_id": asset_sub_ids["101"],
                "code": "10102",
                "name_ar": "الذمم المدينة",
                "name_en": "Accounts Receivable",
                "account_type": "assistant",
                "account_category": "asset",
                "level": 3
            },
            {
                "parent_id": asset_sub_ids["101"],
                "code": "10103",
                "name_ar": "المخزون",
                "name_en": "Inventory",
                "account_type": "assistant",
                "account_category": "asset",
                "level": 3
            }
        ]

        current_assets_ids = {}
        for account in current_assets_accounts:
            existing = db_manager.execute_query(
                "SELECT id FROM accounts WHERE code = ?",
                (account["code"],),
                fetch_one=True
            )

            if not existing:
                account_id = db_manager.insert_record("accounts", account)
                current_assets_ids[account["code"]] = account_id
                logger.info(f"Current assets account '{account['name_ar']}' created with ID: {account_id}")
            else:
                current_assets_ids[account["code"]] = existing["id"]

        # Cash and Banks analytic accounts (Level 4)
        cash_banks_accounts = [
            {
                "parent_id": current_assets_ids["10101"],
                "code": "1010101",
                "name_ar": "الخزينة",
                "name_en": "Cash on Hand",
                "account_type": "assistant",
                "account_category": "asset",
                "level": 4
            },
            {
                "parent_id": current_assets_ids["10101"],
                "code": "1010102",
                "name_ar": "البنوك",
                "name_en": "Bank Accounts",
                "account_type": "assistant",
                "account_category": "asset",
                "level": 4
            }
        ]

        cash_banks_ids = {}
        for account in cash_banks_accounts:
            existing = db_manager.execute_query(
                "SELECT id FROM accounts WHERE code = ?",
                (account["code"],),
                fetch_one=True
            )

            if not existing:
                account_id = db_manager.insert_record("accounts", account)
                cash_banks_ids[account["code"]] = account_id
                logger.info(f"Cash/Banks account '{account['name_ar']}' created with ID: {account_id}")
            else:
                cash_banks_ids[account["code"]] = existing["id"]

        # Bank analytic accounts (Level 5)
        bank_accounts = [
            {
                "parent_id": cash_banks_ids["1010102"],
                "code": "101010201",
                "name_ar": "البنك الأهلي",
                "name_en": "Al Rajhi Bank",
                "account_type": "analytic",
                "account_category": "asset",
                "level": 5
            },
            {
                "parent_id": cash_banks_ids["1010102"],
                "code": "101010202",
                "name_ar": "بنك الراجحي",
                "name_en": "Riyad Bank",
                "account_type": "analytic",
                "account_category": "asset",
                "level": 5
            },
            {
                "parent_id": cash_banks_ids["1010102"],
                "code": "101010203",
                "name_ar": "البنك السعودي",
                "name_en": "SABB Bank",
                "account_type": "analytic",
                "account_category": "asset",
                "level": 5
            }
        ]

        for account in bank_accounts:
            existing = db_manager.execute_query(
                "SELECT id FROM accounts WHERE code = ?",
                (account["code"],),
                fetch_one=True
            )

            if not existing:
                account_id = db_manager.insert_record("accounts", account)
                logger.info(f"Bank account '{account['name_ar']}' created with ID: {account_id}")

        # Liability sub-accounts (Level 2)
        liability_sub_accounts = [
            {
                "parent_id": root_account_ids["2"],
                "code": "201",
                "name_ar": "الخصوم المتداولة",
                "name_en": "Current Liabilities",
                "account_type": "general",
                "account_category": "liability",
                "level": 2
            },
            {
                "parent_id": root_account_ids["2"],
                "code": "202",
                "name_ar": "الخصوم غير المتداولة",
                "name_en": "Non-Current Liabilities",
                "account_type": "general",
                "account_category": "liability",
                "level": 2
            }
        ]

        for account in liability_sub_accounts:
            existing = db_manager.execute_query(
                "SELECT id FROM accounts WHERE code = ?",
                (account["code"],),
                fetch_one=True
            )

            if not existing:
                account_id = db_manager.insert_record("accounts", account)
                logger.info(f"Liability sub-account '{account['name_ar']}' created with ID: {account_id}")

        # Expense sub-accounts (Level 2)
        expense_sub_accounts = [
            {
                "parent_id": root_account_ids["3"],
                "code": "301",
                "name_ar": "المصروفات التشغيلية",
                "name_en": "Operating Expenses",
                "account_type": "general",
                "account_category": "expense",
                "level": 2
            },
            {
                "parent_id": root_account_ids["3"],
                "code": "302",
                "name_ar": "مصروفات البيع والتسويق",
                "name_en": "Sales and Marketing Expenses",
                "account_type": "general",
                "account_category": "expense",
                "level": 2
            },
            {
                "parent_id": root_account_ids["3"],
                "code": "303",
                "name_ar": "المصروفات الإدارية والعامة",
                "name_en": "Administrative and General Expenses",
                "account_type": "general",
                "account_category": "expense",
                "level": 2
            }
        ]

        for account in expense_sub_accounts:
            existing = db_manager.execute_query(
                "SELECT id FROM accounts WHERE code = ?",
                (account["code"],),
                fetch_one=True
            )

            if not existing:
                account_id = db_manager.insert_record("accounts", account)
                logger.info(f"Expense sub-account '{account['name_ar']}' created with ID: {account_id}")

        # Revenue sub-accounts (Level 2)
        revenue_sub_accounts = [
            {
                "parent_id": root_account_ids["4"],
                "code": "401",
                "name_ar": "إيرادات المبيعات",
                "name_en": "Sales Revenue",
                "account_type": "general",
                "account_category": "revenue",
                "level": 2
            },
            {
                "parent_id": root_account_ids["4"],
                "code": "402",
                "name_ar": "إيرادات الخدمات",
                "name_en": "Service Revenue",
                "account_type": "general",
                "account_category": "revenue",
                "level": 2
            },
            {
                "parent_id": root_account_ids["4"],
                "code": "403",
                "name_ar": "إيرادات أخرى",
                "name_en": "Other Revenue",
                "account_type": "general",
                "account_category": "revenue",
                "level": 2
            }
        ]

        for account in revenue_sub_accounts:
            existing = db_manager.execute_query(
                "SELECT id FROM accounts WHERE code = ?",
                (account["code"],),
                fetch_one=True
            )

            if not existing:
                account_id = db_manager.insert_record("accounts", account)
                logger.info(f"Revenue sub-account '{account['name_ar']}' created with ID: {account_id}")

        logger.info("Chart of Accounts initial structure created successfully")

    except Exception as e:
        logger.error(f"Failed to insert Chart of Accounts: {e}")
        raise

def insert_default_reports(db_manager):
    """Insert default system reports"""

    try:
        default_reports = [
            {
                "name": "دفتر الأستاذ العام",
                "name_en": "General Ledger",
                "description": "عرض جميع الحركات للحسابات المحددة",
                "report_type": "ledger",
                "query": """
                    SELECT
                        je.entry_number,
                        je.date,
                        je.description as entry_description,
                        a.code as account_code,
                        a.name_ar as account_name,
                        jl.description as line_description,
                        jl.debit,
                        jl.credit,
                        a.opening_balance,
                        (a.opening_balance + SUM(CASE
                            WHEN jl.debit > 0 THEN jl.debit
                            WHEN jl.credit > 0 THEN -jl.credit
                            ELSE 0
                        END) OVER (PARTITION BY a.id ORDER BY je.date, jl.line_number)) as running_balance
                    FROM journal_entries je
                    JOIN journal_lines jl ON je.id = jl.entry_id
                    JOIN accounts a ON jl.account_id = a.id
                    WHERE je.status = 'posted'
                    AND a.id = ?
                    ORDER BY je.date, jl.line_number
                """,
                "parameters": '{"account_id": "integer", "start_date": "date", "end_date": "date"}',
                "is_system": True,
                "is_active": True
            },
            {
                "name": "كشف حساب التكاليف",
                "name_en": "Cost Accounts Report",
                "description": "عرض ملخص المصروفات والإيرادات",
                "report_type": "cost_accounts",
                "query": """
                    SELECT
                        a.code,
                        a.name_ar,
                        a.account_category,
                        SUM(jl.debit) as total_debit,
                        SUM(jl.credit) as total_credit,
                        (SUM(jl.debit) - SUM(jl.credit)) as net_amount
                    FROM journal_lines jl
                    JOIN journal_entries je ON jl.entry_id = je.id
                    JOIN accounts a ON jl.account_id = a.id
                    WHERE je.status = 'posted'
                    AND je.date BETWEEN ? AND ?
                    AND a.account_category IN ('expense', 'revenue')
                    GROUP BY a.id, a.code, a.name_ar, a.account_category
                    ORDER BY a.code
                """,
                "parameters": '{"start_date": "date", "end_date": "date"}',
                "is_system": True,
                "is_active": True
            },
            {
                "name": "ميزان المراجعة",
                "name_en": "Trial Balance",
                "description": "ميزان المراجعة للفترة المحددة",
                "report_type": "trial_balance",
                "query": """
                    SELECT
                        a.code,
                        a.name_ar,
                        a.account_category,
                        a.opening_balance,
                        SUM(jl.debit) as period_debit,
                        SUM(jl.credit) as period_credit,
                        (a.opening_balance + SUM(jl.debit) - SUM(jl.credit)) as closing_balance
                    FROM accounts a
                    LEFT JOIN journal_lines jl ON a.id = jl.account_id
                    LEFT JOIN journal_entries je ON jl.entry_id = je.id
                        AND je.status = 'posted'
                        AND je.date BETWEEN ? AND ?
                    WHERE a.is_active = 1
                    GROUP BY a.id, a.code, a.name_ar, a.account_category, a.opening_balance
                    HAVING a.opening_balance != 0 OR period_debit != 0 OR period_credit != 0
                    ORDER BY a.code
                """,
                "parameters": '{"start_date": "date", "end_date": "date"}',
                "is_system": True,
                "is_active": True
            }
        ]

        for report in default_reports:
            # Check if report already exists
            existing = db_manager.execute_query(
                "SELECT id FROM reports WHERE name = ?",
                (report["name"],),
                fetch_one=True
            )

            if not existing:
                report_id = db_manager.insert_record("reports", report)
                logger.info(f"Default report '{report['name']}' created with ID: {report_id}")

    except Exception as e:
        logger.error(f"Failed to insert default reports: {e}")
        raise

def create_sample_journal_entries(db_manager):
    """Create sample journal entries for testing (optional)"""

    try:
        # Get current fiscal year
        fiscal_year = db_manager.execute_query(
            "SELECT id FROM fiscal_years WHERE is_active = 1",
            fetch_one=True
        )

        if not fiscal_year:
            logger.warning("No active fiscal year found for sample entries")
            return

        # Get sample accounts
        cash_account = db_manager.execute_query(
            "SELECT id FROM accounts WHERE code LIKE '1010102%' LIMIT 1",
            fetch_one=True
        )

        revenue_account = db_manager.execute_query(
            "SELECT id FROM accounts WHERE account_category = 'revenue' LIMIT 1",
            fetch_one=True
        )

        if not cash_account or not revenue_account:
            logger.warning("Sample accounts not found for creating sample entries")
            return

        # Generate entry number
        last_entry = db_manager.execute_query(
            "SELECT entry_number FROM journal_entries ORDER BY id DESC LIMIT 1",
            fetch_one=True
        )

        if last_entry:
            last_number = int(last_entry["entry_number"].split("-")[-1])
            new_number = f"JE-{last_number + 1:06d}"
        else:
            new_number = "JE-000001"

        # Create sample journal entry
        entry_data = {
            "entry_number": new_number,
            "date": date.today(),
            "description": "مثال قيد يومية / Sample Journal Entry",
            "fiscal_year_id": fiscal_year["id"],
            "total_debit": 1000.00,
            "total_credit": 1000.00,
            "status": "posted"
        }

        entry_id = db_manager.insert_record("journal_entries", entry_data)

        # Create journal lines
        lines = [
            {
                "entry_id": entry_id,
                "account_id": cash_account["id"],
                "line_number": 1,
                "description": "نقدية مستلمة / Cash received",
                "debit": 1000.00,
                "credit": 0.00
            },
            {
                "entry_id": entry_id,
                "account_id": revenue_account["id"],
                "line_number": 2,
                "description": "إيرادات الخدمات / Service revenue",
                "debit": 0.00,
                "credit": 1000.00
            }
        ]

        for line in lines:
            db_manager.insert_record("journal_lines", line)

        logger.info(f"Sample journal entry '{new_number}' created successfully")

    except Exception as e:
        logger.error(f"Failed to create sample journal entries: {e}")

def get_initial_data_version() -> str:
    """Get initial data version for tracking updates"""
    return "1.0.0"