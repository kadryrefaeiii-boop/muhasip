#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Journal Manager
Journal entries and double-entry validation
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date
import uuid

logger = logging.getLogger(__name__)

class JournalManager:
    """Journal entries and double-entry validation"""

    def __init__(self, db_manager):
        """
        Initialize Journal Manager

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        logger.info("Journal Manager initialized")

    def create_entry(
        self,
        entry_date: date,
        description: str,
        lines: List[Dict[str, Any]],
        fiscal_year_id: int,
        created_by: Optional[int] = None,
        attachments: Optional[List[Dict[str, Any]]] = None
    ) -> Optional[int]:
        """
        Create new journal entry with double-entry validation

        Args:
            entry_date: Entry date
            description: Entry description
            lines: List of journal lines
            fiscal_year_id: Fiscal year ID
            created_by: User ID who created the entry
            attachments: List of file attachments

        Returns:
            New entry ID or None if failed
        """
        try:
            # Validate journal entry
            validation_result = self.validate_entry(lines)
            if not validation_result['valid']:
                logger.error(f"Journal entry validation failed: {validation_result['error']}")
                return None

            # Generate entry number
            entry_number = self.generate_entry_number(fiscal_year_id)

            # Calculate totals
            totals = self._calculate_entry_totals(lines)

            # Create journal entry
            entry_data = {
                "entry_number": entry_number,
                "date": entry_date,
                "description": description,
                "fiscal_year_id": fiscal_year_id,
                "total_debit": totals['debit'],
                "total_credit": totals['credit'],
                "status": "draft",
                "created_by": created_by
            }

            with self.db_manager.transaction() as conn:
                # Insert journal entry
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO journal_entries (
                        entry_number, date, description, fiscal_year_id,
                        total_debit, total_credit, status, created_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entry_number, entry_date, description, fiscal_year_id,
                    totals['debit'], totals['credit'], "draft", created_by
                ))

                entry_id = cursor.lastrowid

                # Insert journal lines
                for i, line in enumerate(lines, 1):
                    line_data = {
                        "entry_id": entry_id,
                        "account_id": line['account_id'],
                        "line_number": i,
                        "description": line.get('description', ''),
                        "debit": line.get('debit', 0),
                        "credit": line.get('credit', 0),
                        "created_by": created_by
                    }

                    cursor.execute("""
                        INSERT INTO journal_lines (
                            entry_id, account_id, line_number, description,
                            debit, credit, created_by
                        ) VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        entry_id, line_data['account_id'], line_data['line_number'],
                        line_data['description'], line_data['debit'],
                        line_data['credit'], created_by
                    ))

                # Handle attachments
                if attachments:
                    self._save_attachments(entry_id, None, attachments, created_by, conn)

                cursor.close()

            logger.info(f"Journal entry '{entry_number}' created successfully with ID: {entry_id}")

            # Log the action
            self._log_journal_action("CREATE", entry_id, None, entry_data, created_by)

            return entry_id

        except Exception as e:
            logger.error(f"Failed to create journal entry: {e}")
            return None

    def validate_entry(self, lines: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validate journal entry for double-entry compliance

        Args:
            lines: List of journal lines

        Returns:
            Validation result with validity status and error message
        """
        try:
            if not lines or len(lines) < 2:
                return {"valid": False, "error": "Journal entry must have at least 2 lines"}

            totals = self._calculate_entry_totals(lines)

            # Check if debit equals credit
            if abs(totals['debit'] - totals['credit']) > 0.01:  # Allow for floating point precision
                return {
                    "valid": False,
                    "error": f"Debit ({totals['debit']}) must equal Credit ({totals['credit']})"
                }

            # Validate each line
            for i, line in enumerate(lines):
                line_validation = self._validate_journal_line(line)
                if not line_validation['valid']:
                    return {
                        "valid": False,
                        "error": f"Line {i+1}: {line_validation['error']}"
                    }

            return {"valid": True, "error": None}

        except Exception as e:
            logger.error(f"Journal entry validation failed: {e}")
            return {"valid": False, "error": f"Validation error: {str(e)}"}

    def _validate_journal_line(self, line: Dict[str, Any]) -> Dict[str, Any]:
        """Validate individual journal line"""

        try:
            # Check required fields
            if 'account_id' not in line:
                return {"valid": False, "error": "Account ID is required"}

            # Check if account exists
            account = self.db_manager.get_record_by_id("accounts", line['account_id'])
            if not account:
                return {"valid": False, "error": f"Account {line['account_id']} not found"}

            if not account['is_active']:
                return {"valid": False, "error": "Account is not active"}

            # Check debit/credit values
            debit = line.get('debit', 0)
            credit = line.get('credit', 0)

            if debit < 0 or credit < 0:
                return {"valid": False, "error": "Debit and Credit cannot be negative"}

            if debit > 0 and credit > 0:
                return {"valid": False, "error": "Line cannot have both Debit and Credit values"}

            if debit == 0 and credit == 0:
                return {"valid": False, "error": "Line must have either Debit or Credit value"}

            return {"valid": True, "error": None}

        except Exception as e:
            return {"valid": False, "error": f"Line validation error: {str(e)}"}

    def _calculate_entry_totals(self, lines: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate total debit and credit for entry"""

        total_debit = 0.0
        total_credit = 0.0

        for line in lines:
            total_debit += line.get('debit', 0)
            total_credit += line.get('credit', 0)

        return {"debit": total_debit, "credit": total_credit}

    def generate_entry_number(self, fiscal_year_id: int) -> str:
        """Generate unique journal entry number"""

        try:
            # Get last entry number for this fiscal year
            query = """
                SELECT entry_number FROM journal_entries
                WHERE fiscal_year_id = ?
                ORDER BY id DESC
                LIMIT 1
            """
            last_entry = self.db_manager.execute_query(query, (fiscal_year_id,), fetch_one=True)

            if last_entry:
                # Extract numeric part and increment
                last_number = int(last_entry['entry_number'].split('-')[-1])
                new_number = last_number + 1
            else:
                new_number = 1

            return f"JE-{new_number:06d}"

        except Exception as e:
            logger.error(f"Failed to generate entry number: {e}")
            # Fallback to timestamp-based number
            import time
            timestamp = int(time.time())
            return f"JE-{timestamp}"

    def update_entry(self, entry_id: int, **kwargs) -> bool:
        """
        Update journal entry

        Args:
            entry_id: Entry ID to update
            **kwargs: Fields to update

        Returns:
            True if update successful
        """
        try:
            # Get current entry data for logging
            current_data = self.get_entry_details(entry_id)
            if not current_data:
                logger.error(f"Journal entry not found: {entry_id}")
                return False

            # Check if entry can be updated (not posted)
            if current_data['status'] in ['posted', 'approved']:
                logger.error(f"Cannot update {current_data['status']} journal entry")
                return False

            # Validate update data
            if not self._validate_entry_update(entry_id, kwargs):
                return False

            # Update entry
            affected_rows = self.db_manager.update_record(
                "journal_entries",
                kwargs,
                "id = ?",
                (entry_id,)
            )

            if affected_rows > 0:
                logger.info(f"Journal entry {entry_id} updated successfully")

                # Log the action
                self._log_journal_action("UPDATE", entry_id, current_data, kwargs, kwargs.get('updated_by'))

                return True

            return False

        except Exception as e:
            logger.error(f"Failed to update journal entry: {e}")
            return False

    def _validate_entry_update(self, entry_id: int, update_data: Dict[str, Any]) -> bool:
        """Validate journal entry update"""

        # Cannot change fiscal year if entry has lines
        if 'fiscal_year_id' in update_data:
            lines = self.get_entry_lines(entry_id)
            if lines:
                logger.error("Cannot change fiscal year of entry with existing lines")
                return False

        # Validate date range
        if 'date' in update_data:
            entry = self.get_entry_details(entry_id)
            if entry:
                fiscal_year = self.db_manager.get_record_by_id("fiscal_years", entry['fiscal_year_id'])
                if fiscal_year:
                    if not (fiscal_year['start_date'] <= update_data['date'] <= fiscal_year['end_date']):
                        logger.error("Entry date must be within fiscal year range")
                        return False

        return True

    def delete_entry(self, entry_id: int, reason: Optional[str] = None, deleted_by: Optional[int] = None) -> bool:
        """
        Delete journal entry with validation

        Args:
            entry_id: Entry ID to delete
            reason: Reason for deletion
            deleted_by: User ID who deleted the entry

        Returns:
            True if deletion successful
        """
        try:
            entry = self.get_entry_details(entry_id)
            if not entry:
                logger.error(f"Journal entry not found: {entry_id}")
                return False

            # Check if entry can be deleted
            if entry['status'] in ['posted', 'approved']:
                logger.error(f"Cannot delete {entry['status']} journal entry")
                return False

            with self.db_manager.transaction() as conn:
                # Delete attachments first
                cursor = conn.cursor()
                cursor.execute("DELETE FROM attachments WHERE entry_id = ?", (entry_id,))

                # Delete journal lines
                cursor.execute("DELETE FROM journal_lines WHERE entry_id = ?", (entry_id,))

                # Delete journal entry
                cursor.execute("DELETE FROM journal_entries WHERE id = ?", (entry_id,))

                cursor.close()

            logger.info(f"Journal entry {entry_id} deleted successfully")

            # Log the action
            delete_data = {"reason": reason} if reason else {}
            self._log_journal_action("DELETE", entry_id, entry, delete_data, deleted_by)

            return True

        except Exception as e:
            logger.error(f"Failed to delete journal entry: {e}")
            return False

    def get_entry_details(self, entry_id: int) -> Optional[Dict[str, Any]]:
        """Get complete journal entry details"""

        try:
            query = """
                SELECT
                    je.*,
                    fy.name as fiscal_year_name,
                    u1.username as created_by_name,
                    u2.username as posted_by_name,
                    u3.username as approved_by_name
                FROM journal_entries je
                LEFT JOIN fiscal_years fy ON je.fiscal_year_id = fy.id
                LEFT JOIN users u1 ON je.created_by = u1.id
                LEFT JOIN users u2 ON je.posted_by = u2.id
                LEFT JOIN users u3 ON je.approved_by = u3.id
                WHERE je.id = ?
            """
            result = self.db_manager.execute_query(query, (entry_id,), fetch_one=True)
            return result

        except Exception as e:
            logger.error(f"Failed to get entry details: {e}")
            return None

    def get_entry_lines(self, entry_id: int) -> List[Dict[str, Any]]:
        """Get journal lines for entry"""

        try:
            query = """
                SELECT
                    jl.*,
                    a.code as account_code,
                    a.name_ar as account_name,
                    a.name_en as account_name_en,
                    a.account_category
                FROM journal_lines jl
                JOIN accounts a ON jl.account_id = a.id
                WHERE jl.entry_id = ?
                ORDER BY jl.line_number
            """
            result = self.db_manager.execute_query(query, (entry_id,), fetch_all=True)
            return result or []

        except Exception as e:
            logger.error(f"Failed to get entry lines: {e}")
            return []

    def get_entries(
        self,
        filters: Optional[Dict[str, Any]] = None,
        pagination: Optional[Dict[str, int]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get journal entries with optional filtering

        Args:
            filters: Dictionary of filter criteria
            pagination: Dictionary with limit and offset

        Returns:
            List of journal entries
        """
        try:
            query = """
                SELECT
                    je.*,
                    fy.name as fiscal_year_name,
                    u1.username as created_by_name,
                    COUNT(jl.id) as line_count
                FROM journal_entries je
                LEFT JOIN fiscal_years fy ON je.fiscal_year_id = fy.id
                LEFT JOIN users u1 ON je.created_by = u1.id
                LEFT JOIN journal_lines jl ON je.id = jl.entry_id
            """

            params = []
            where_conditions = []

            if filters:
                if 'status' in filters:
                    where_conditions.append("je.status = ?")
                    params.append(filters['status'])

                if 'fiscal_year_id' in filters:
                    where_conditions.append("je.fiscal_year_id = ?")
                    params.append(filters['fiscal_year_id'])

                if 'date_from' in filters:
                    where_conditions.append("je.date >= ?")
                    params.append(filters['date_from'])

                if 'date_to' in filters:
                    where_conditions.append("je.date <= ?")
                    params.append(filters['date_to'])

                if 'entry_number' in filters:
                    where_conditions.append("je.entry_number LIKE ?")
                    params.append(f"%{filters['entry_number']}%")

                if 'created_by' in filters:
                    where_conditions.append("je.created_by = ?")
                    params.append(filters['created_by'])

            if where_conditions:
                query += " WHERE " + " AND ".join(where_conditions)

            query += " GROUP BY je.id ORDER BY je.date DESC, je.entry_number DESC"

            if pagination:
                query += " LIMIT ? OFFSET ?"
                params.extend([pagination['limit'], pagination['offset']])

            result = self.db_manager.execute_query(query, tuple(params), fetch_all=True)
            return result or []

        except Exception as e:
            logger.error(f"Failed to get journal entries: {e}")
            return []

    def post_entry(self, entry_id: int, posted_by: int) -> bool:
        """
        Post journal entry (mark as posted)

        Args:
            entry_id: Entry ID to post
            posted_by: User ID posting the entry

        Returns:
            True if posting successful
        """
        try:
            entry = self.get_entry_details(entry_id)
            if not entry:
                logger.error(f"Journal entry not found: {entry_id}")
                return False

            if entry['status'] != 'draft':
                logger.error(f"Cannot post entry with status: {entry['status']}")
                return False

            # Update account balances
            if not self._update_account_balances(entry_id):
                return False

            # Update entry status
            update_data = {
                "status": "posted",
                "posted_at": datetime.now(),
                "posted_by": posted_by
            }

            affected_rows = self.db_manager.update_record(
                "journal_entries",
                update_data,
                "id = ?",
                (entry_id,)
            )

            if affected_rows > 0:
                logger.info(f"Journal entry {entry_id} posted successfully")

                # Log the action
                self._log_journal_action("POST", entry_id, entry, update_data, posted_by)

                return True

            return False

        except Exception as e:
            logger.error(f"Failed to post journal entry: {e}")
            return False

    def approve_entry(self, entry_id: int, approved_by: int) -> bool:
        """
        Approve journal entry

        Args:
            entry_id: Entry ID to approve
            approved_by: User ID approving the entry

        Returns:
            True if approval successful
        """
        try:
            entry = self.get_entry_details(entry_id)
            if not entry:
                logger.error(f"Journal entry not found: {entry_id}")
                return False

            if entry['status'] != 'posted':
                logger.error(f"Cannot approve entry with status: {entry['status']}")
                return False

            # Update entry status
            update_data = {
                "status": "approved",
                "approved_at": datetime.now(),
                "approved_by": approved_by
            }

            affected_rows = self.db_manager.update_record(
                "journal_entries",
                update_data,
                "id = ?",
                (entry_id,)
            )

            if affected_rows > 0:
                logger.info(f"Journal entry {entry_id} approved successfully")

                # Log the action
                self._log_journal_action("APPROVE", entry_id, entry, update_data, approved_by)

                return True

            return False

        except Exception as e:
            logger.error(f"Failed to approve journal entry: {e}")
            return False

    def _update_account_balances(self, entry_id: int) -> bool:
        """Update account balances for posted entry"""

        try:
            lines = self.get_entry_lines(entry_id)
            from .account_manager import AccountManager
            account_manager = AccountManager(self.db_manager)

            for line in lines:
                account = account_manager.get_account_by_id(line['account_id'])
                if not account:
                    continue

                # Update current balance based on account category and line type
                current_balance = account['current_balance'] or 0

                if account['account_category'] in ['asset', 'expense']:
                    # Assets and expenses increase with debit, decrease with credit
                    new_balance = current_balance + line['debit'] - line['credit']
                else:
                    # Liabilities, revenue, and equity decrease with debit, increase with credit
                    new_balance = current_balance - line['debit'] + line['credit']

                self.db_manager.update_record(
                    "accounts",
                    {"current_balance": new_balance},
                    "id = ?",
                    (line['account_id'],)
                )

            return True

        except Exception as e:
            logger.error(f"Failed to update account balances: {e}")
            return False

    def _save_attachments(
        self,
        entry_id: Optional[int],
        account_id: Optional[int],
        attachments: List[Dict[str, Any]],
        uploaded_by: int,
        conn
    ):
        """Save file attachments"""

        try:
            for attachment in attachments:
                attachment_data = {
                    "entry_id": entry_id,
                    "account_id": account_id,
                    "filename": attachment.get('filename', ''),
                    "original_filename": attachment.get('original_filename', ''),
                    "file_path": attachment.get('file_path', ''),
                    "file_size": attachment.get('file_size', 0),
                    "mime_type": attachment.get('mime_type', ''),
                    "description": attachment.get('description', ''),
                    "uploaded_by": uploaded_by
                }

                conn.execute("""
                    INSERT INTO attachments (
                        entry_id, account_id, filename, original_filename,
                        file_path, file_size, mime_type, description, uploaded_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    attachment_data['entry_id'], attachment_data['account_id'],
                    attachment_data['filename'], attachment_data['original_filename'],
                    attachment_data['file_path'], attachment_data['file_size'],
                    attachment_data['mime_type'], attachment_data['description'],
                    attachment_data['uploaded_by']
                ))

        except Exception as e:
            logger.error(f"Failed to save attachments: {e}")
            raise

    def _log_journal_action(self, action: str, entry_id: int, old_data: Optional[Dict], new_data: Optional[Dict], user_id: Optional[int]):
        """Log journal-related actions"""

        try:
            import json

            audit_data = {
                "user_id": user_id,
                "action": f"JOURNAL_{action}",
                "table_name": "journal_entries",
                "record_id": entry_id,
                "old_values": json.dumps(old_data) if old_data else None,
                "new_values": json.dumps(new_data) if new_data else None,
                "timestamp": datetime.now()
            }

            self.db_manager.insert_record("audit_log", audit_data, return_id=False)

        except Exception as e:
            logger.error(f"Failed to log journal action: {e}")

    def get_entry_attachments(self, entry_id: int) -> List[Dict[str, Any]]:
        """Get attachments for journal entry"""

        try:
            query = """
                SELECT
                    a.*,
                    u.username as uploaded_by_name
                FROM attachments a
                LEFT JOIN users u ON a.uploaded_by = u.id
                WHERE a.entry_id = ?
                ORDER BY a.uploaded_at
            """
            result = self.db_manager.execute_query(query, (entry_id,), fetch_all=True)
            return result or []

        except Exception as e:
            logger.error(f"Failed to get entry attachments: {e}")
            return []

    def get_fiscal_year_entries(self, fiscal_year_id: int) -> List[Dict[str, Any]]:
        """Get all entries for a fiscal year"""

        return self.get_entries({"fiscal_year_id": fiscal_year_id})