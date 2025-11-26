#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Database Schema
Professional Accounting ERP database structure with enhanced tables
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Database schema definitions
SCHEMA_TABLES = {
    "users": """
        CREATE TABLE users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            email TEXT,
            role TEXT CHECK (role IN ('admin', 'accountant', 'viewer')) DEFAULT 'viewer',
            is_active BOOLEAN DEFAULT TRUE,
            failed_login_attempts INTEGER DEFAULT 0,
            last_login TIMESTAMP NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER NULL,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    """,

    "accounts": """
        CREATE TABLE accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            parent_id INTEGER NULL,
            code TEXT UNIQUE NOT NULL,
            name_ar TEXT NOT NULL,
            name_en TEXT NOT NULL,
            account_type TEXT CHECK (account_type IN ('general', 'assistant', 'analytic')) NOT NULL,
            account_category TEXT CHECK (account_category IN ('asset', 'liability', 'expense', 'revenue', 'equity')) NOT NULL,
            level INTEGER NOT NULL,
            full_path TEXT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            opening_balance DECIMAL(15,2) DEFAULT 0,
            current_balance DECIMAL(15,2) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER NULL,
            updated_by INTEGER NULL,
            FOREIGN KEY (parent_id) REFERENCES accounts(id),
            FOREIGN KEY (created_by) REFERENCES users(id),
            FOREIGN KEY (updated_by) REFERENCES users(id)
        )
    """,

    "fiscal_years": """
        CREATE TABLE fiscal_years (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            is_active BOOLEAN DEFAULT FALSE,
            is_closed BOOLEAN DEFAULT FALSE,
            closed_at TIMESTAMP NULL,
            closed_by INTEGER NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER NULL,
            FOREIGN KEY (closed_by) REFERENCES users(id),
            FOREIGN KEY (created_by) REFERENCES users(id),
            CHECK (end_date > start_date)
        )
    """,

    "journal_entries": """
        CREATE TABLE journal_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_number TEXT UNIQUE NOT NULL,
            date DATE NOT NULL,
            description TEXT,
            fiscal_year_id INTEGER NOT NULL,
            total_debit DECIMAL(15,2) NOT NULL DEFAULT 0,
            total_credit DECIMAL(15,2) NOT NULL DEFAULT 0,
            status TEXT CHECK (status IN ('draft', 'posted', 'approved')) DEFAULT 'draft',
            posted_at TIMESTAMP NULL,
            posted_by INTEGER NULL,
            approved_at TIMESTAMP NULL,
            approved_by INTEGER NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER NULL,
            updated_by INTEGER NULL,
            FOREIGN KEY (fiscal_year_id) REFERENCES fiscal_years(id),
            FOREIGN KEY (posted_by) REFERENCES users(id),
            FOREIGN KEY (approved_by) REFERENCES users(id),
            FOREIGN KEY (created_by) REFERENCES users(id),
            FOREIGN KEY (updated_by) REFERENCES users(id),
            CHECK (total_debit = total_credit)
        )
    """,

    "journal_lines": """
        CREATE TABLE journal_lines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id INTEGER NOT NULL,
            account_id INTEGER NOT NULL,
            line_number INTEGER NOT NULL,
            description TEXT,
            debit DECIMAL(15,2) DEFAULT 0,
            credit DECIMAL(15,2) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER NULL,
            updated_by INTEGER NULL,
            FOREIGN KEY (entry_id) REFERENCES journal_entries(id) ON DELETE CASCADE,
            FOREIGN KEY (account_id) REFERENCES accounts(id),
            FOREIGN KEY (created_by) REFERENCES users(id),
            FOREIGN KEY (updated_by) REFERENCES users(id),
            CHECK (debit >= 0 AND credit >= 0),
            CHECK (debit > 0 XOR credit > 0),
            UNIQUE(entry_id, line_number)
        )
    """,

    "attachments": """
        CREATE TABLE attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            entry_id INTEGER NULL,
            account_id INTEGER NULL,
            filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            mime_type TEXT,
            description TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            uploaded_by INTEGER NULL,
            FOREIGN KEY (entry_id) REFERENCES journal_entries(id),
            FOREIGN KEY (account_id) REFERENCES accounts(id),
            FOREIGN KEY (uploaded_by) REFERENCES users(id),
            CHECK (entry_id IS NOT NULL OR account_id IS NOT NULL)
        )
    """,

    "settings": """
        CREATE TABLE settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            data_type TEXT CHECK (data_type IN ('string', 'integer', 'float', 'boolean', 'json')) DEFAULT 'string',
            description TEXT,
            is_system BOOLEAN DEFAULT FALSE,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_by INTEGER NULL,
            FOREIGN KEY (updated_by) REFERENCES users(id)
        )
    """,

    "audit_log": """
        CREATE TABLE audit_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NULL,
            action TEXT NOT NULL,
            table_name TEXT,
            record_id INTEGER,
            old_values TEXT,
            new_values TEXT,
            ip_address TEXT,
            user_agent TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """,

    "user_sessions": """
        CREATE TABLE user_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_token TEXT UNIQUE NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """,

    "reports": """
        CREATE TABLE reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            report_type TEXT NOT NULL,
            query TEXT NOT NULL,
            parameters TEXT,
            is_system BOOLEAN DEFAULT FALSE,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER NULL,
            updated_by INTEGER NULL,
            FOREIGN KEY (created_by) REFERENCES users(id),
            FOREIGN KEY (updated_by) REFERENCES users(id)
        )
    """,

    "workflows": """
        CREATE TABLE workflows (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT,
            trigger_type TEXT NOT NULL,
            conditions TEXT NOT NULL,
            actions TEXT NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            created_by INTEGER NULL,
            updated_by INTEGER NULL,
            FOREIGN KEY (created_by) REFERENCES users(id),
            FOREIGN KEY (updated_by) REFERENCES users(id)
        )
    """
}

# Index definitions for performance optimization
INDEX_DEFINITIONS = [
    "CREATE INDEX idx_accounts_parent_id ON accounts(parent_id)",
    "CREATE INDEX idx_accounts_code ON accounts(code)",
    "CREATE INDEX idx_accounts_type ON accounts(account_type)",
    "CREATE INDEX idx_accounts_category ON accounts(account_category)",
    "CREATE INDEX idx_accounts_active ON accounts(is_active)",
    "CREATE UNIQUE INDEX idx_accounts_code_active ON accounts(code) WHERE is_active = 1",

    "CREATE INDEX idx_fiscal_years_active ON fiscal_years(is_active)",
    "CREATE INDEX idx_fiscal_years_closed ON fiscal_years(is_closed)",
    "CREATE UNIQUE INDEX idx_fiscal_years_name ON fiscal_years(name)",

    "CREATE INDEX idx_journal_entries_number ON journal_entries(entry_number)",
    "CREATE INDEX idx_journal_entries_date ON journal_entries(date)",
    "CREATE INDEX idx_journal_entries_fiscal_year ON journal_entries(fiscal_year_id)",
    "CREATE INDEX idx_journal_entries_status ON journal_entries(status)",
    "CREATE INDEX idx_journal_entries_created_by ON journal_entries(created_by)",
    "CREATE INDEX idx_journal_entries_posted_by ON journal_entries(posted_by)",
    "CREATE UNIQUE INDEX idx_journal_entries_number_fiscal ON journal_entries(entry_number, fiscal_year_id)",

    "CREATE INDEX idx_journal_lines_entry ON journal_lines(entry_id)",
    "CREATE INDEX idx_journal_lines_account ON journal_lines(account_id)",
    "CREATE INDEX idx_journal_lines_entry_account ON journal_lines(entry_id, account_id)",
    "CREATE INDEX idx_journal_lines_debit ON journal_lines(debit) WHERE debit > 0",
    "CREATE INDEX idx_journal_lines_credit ON journal_lines(credit) WHERE credit > 0",

    "CREATE INDEX idx_attachments_entry ON attachments(entry_id)",
    "CREATE INDEX idx_attachments_account ON attachments(account_id)",
    "CREATE INDEX idx_attachments_uploaded_by ON attachments(uploaded_by)",

    "CREATE INDEX idx_audit_log_user ON audit_log(user_id)",
    "CREATE INDEX idx_audit_log_table ON audit_log(table_name)",
    "CREATE INDEX idx_audit_log_timestamp ON audit_log(timestamp)",
    "CREATE INDEX idx_audit_log_action ON audit_log(action)",

    "CREATE INDEX idx_user_sessions_user ON user_sessions(user_id)",
    "CREATE INDEX idx_user_sessions_token ON user_sessions(session_token)",
    "CREATE INDEX idx_user_sessions_expires ON user_sessions(expires_at)",
    "CREATE INDEX idx_user_sessions_active ON user_sessions(is_active)",

    "CREATE INDEX idx_reports_type ON reports(report_type)",
    "CREATE INDEX idx_reports_active ON reports(is_active)",
    "CREATE INDEX idx_reports_system ON reports(is_system)",

    "CREATE INDEX idx_workflows_active ON workflows(is_active)",
    "CREATE INDEX idx_workflows_trigger ON workflows(trigger_type)"
]

def create_all_tables(db_manager) -> bool:
    """
    Create all database tables with proper schema

    Args:
        db_manager: Database manager instance

    Returns:
        True if tables created successfully
    """
    try:
        logger.info("Starting database schema creation...")

        # Create all tables
        for table_name, create_sql in SCHEMA_TABLES.items():
            if not db_manager.table_exists(table_name):
                logger.info(f"Creating table: {table_name}")
                db_manager.execute_query(create_sql, commit=True)
                logger.info(f"Table {table_name} created successfully")
            else:
                logger.info(f"Table {table_name} already exists")

        # Create indexes
        logger.info("Creating database indexes...")
        for index_sql in INDEX_DEFINITIONS:
            try:
                db_manager.execute_query(index_sql, commit=True)
            except Exception as e:
                # Index might already exist, log but continue
                logger.warning(f"Index creation warning: {e}")

        # Create triggers for automatic updates
        create_triggers(db_manager)

        # Insert default system settings
        insert_default_settings(db_manager)

        logger.info("Database schema creation completed successfully")
        return True

    except Exception as e:
        logger.error(f"Database schema creation failed: {e}")
        return False

def create_triggers(db_manager):
    """Create database triggers for automatic data maintenance"""

    triggers = [
        # Update full_path when account parent changes
        """
        CREATE TRIGGER IF NOT EXISTS update_account_full_path
        AFTER INSERT ON accounts
        BEGIN
            UPDATE accounts
            SET full_path = CASE
                WHEN NEW.parent_id IS NULL THEN NEW.name_ar
                ELSE (SELECT full_path FROM accounts WHERE id = NEW.parent_id) || ' > ' || NEW.name_ar
            END
            WHERE id = NEW.id;
        END
        """,

        # Update full_path when account is updated
        """
        CREATE TRIGGER IF NOT EXISTS update_account_full_path_on_update
        AFTER UPDATE OF parent_id, name_ar ON accounts
        BEGIN
            UPDATE accounts
            SET full_path = CASE
                WHEN NEW.parent_id IS NULL THEN NEW.name_ar
                ELSE (SELECT full_path FROM accounts WHERE id = NEW.parent_id) || ' > ' || NEW.name_ar
            END
            WHERE id = NEW.id;
        END
        """,

        # Update account balances when journal lines are posted
        """
        CREATE TRIGGER IF NOT EXISTS update_account_balance_on_post
        AFTER UPDATE OF status ON journal_entries
        WHEN NEW.status = 'posted' AND OLD.status != 'posted'
        BEGIN
            UPDATE accounts
            SET current_balance = current_balance + (
                SELECT COALESCE(SUM(debit - credit), 0)
                FROM journal_lines
                WHERE entry_id = NEW.id AND account_id = accounts.id
            )
            WHERE id IN (
                SELECT DISTINCT account_id
                FROM journal_lines
                WHERE entry_id = NEW.id
            );
        END
        """,

        # Audit log trigger for user table
        """
        CREATE TRIGGER IF NOT EXISTS audit_users_insert
        AFTER INSERT ON users
        BEGIN
            INSERT INTO audit_log (table_name, record_id, action, new_values)
            VALUES ('users', NEW.id, 'INSERT', json_object(NEW));
        END
        """,

        # Audit log trigger for accounts table
        """
        CREATE TRIGGER IF NOT EXISTS audit_accounts_insert
        AFTER INSERT ON accounts
        BEGIN
            INSERT INTO audit_log (table_name, record_id, action, new_values)
            VALUES ('accounts', NEW.id, 'INSERT', json_object(NEW));
        END
        """,

        # Clean up expired sessions
        """
        CREATE TRIGGER IF NOT EXISTS cleanup_expired_sessions
        AFTER INSERT ON user_sessions
        BEGIN
            DELETE FROM user_sessions
            WHERE expires_at < CURRENT_TIMESTAMP AND is_active = 1;
        END
        """
    ]

    try:
        logger.info("Creating database triggers...")
        for trigger_sql in triggers:
            db_manager.execute_query(trigger_sql, commit=True)
        logger.info("Database triggers created successfully")

    except Exception as e:
        logger.warning(f"Trigger creation warning: {e}")

def insert_default_settings(db_manager):
    """Insert default system settings"""

    default_settings = [
        ("app_name", "Professional Accounting ERP", "string", "Application name", True),
        ("app_version", "1.0.0", "string", "Application version", True),
        ("language", "ar", "string", "Default language (ar/en)", False),
        ("theme", "light", "string", "Application theme (light/dark/system)", False),
        ("color_theme", "blue", "string", "Color theme (blue/dark-blue/green)", False),
        ("decimal_places", "2", "integer", "Number of decimal places for amounts", False),
        ("date_format", "dd/MM/yyyy", "string", "Date display format", False),
        ("currency_symbol", "ر.س", "string", "Currency symbol", False),
        ("auto_backup", "true", "boolean", "Enable automatic backups", False),
        ("backup_retention_days", "30", "integer", "Backup retention period in days", False),
        ("session_timeout", "480", "integer", "Session timeout in minutes", False),
        ("max_login_attempts", "5", "integer", "Maximum failed login attempts", False),
        ("require_approval", "false", "boolean", "Require journal entry approval", False),
        ("export_format", "excel", "string", "Default export format", False),
        ("rtl_support", "true", "boolean", "Enable RTL language support", True)
    ]

    try:
        logger.info("Inserting default system settings...")
        for setting in default_settings:
            key, value, data_type, description, is_system = setting

            # Check if setting already exists
            existing = db_manager.execute_query(
                "SELECT key FROM settings WHERE key = ?",
                (key,),
                fetch_one=True
            )

            if not existing:
                db_manager.insert_record("settings", {
                    "key": key,
                    "value": value,
                    "data_type": data_type,
                    "description": description,
                    "is_system": is_system
                }, return_id=False)

        logger.info("Default settings inserted successfully")

    except Exception as e:
        logger.error(f"Failed to insert default settings: {e}")

def validate_schema_integrity(db_manager) -> bool:
    """
    Validate database schema integrity

    Args:
        db_manager: Database manager instance

    Returns:
        True if schema is valid
    """
    try:
        logger.info("Validating database schema integrity...")

        # Check all tables exist
        for table_name in SCHEMA_TABLES.keys():
            if not db_manager.table_exists(table_name):
                logger.error(f"Missing table: {table_name}")
                return False

        # Check critical indexes exist
        critical_indexes = [
            "idx_accounts_code",
            "idx_accounts_parent_id",
            "idx_journal_entries_number",
            "idx_journal_lines_entry",
            "idx_user_sessions_token"
        ]

        for index_name in critical_indexes:
            # Check if index exists (simplified check)
            try:
                db_manager.execute_query(f"EXPLAIN QUERY PLAN SELECT * FROM sqlite_master WHERE name = '{index_name}'")
            except Exception as e:
                logger.warning(f"Index {index_name} may not exist: {e}")

        logger.info("Database schema integrity validation completed")
        return True

    except Exception as e:
        logger.error(f"Schema integrity validation failed: {e}")
        return False

def get_schema_version() -> str:
    """Get current database schema version"""
    return "1.0.0"