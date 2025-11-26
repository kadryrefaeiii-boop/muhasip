#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Database Manager
Centralized database connection and query management
"""

import sqlite3
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager
import threading

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Centralized database connection and query management"""

    def __init__(self, db_path: str = "database/accounting_erp.db"):
        """
        Initialize database manager

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.connection = None
        self.lock = threading.Lock()

        # Ensure database directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)

        # Initialize connection
        self._initialize_connection()

        logger.info(f"Database Manager initialized with path: {db_path}")

    def _initialize_connection(self):
        """Initialize database connection with proper settings"""
        try:
            self.connection = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                timeout=30.0
            )

            # Enable foreign keys
            self.connection.execute("PRAGMA foreign_keys = ON")

            # Set WAL mode for better concurrency
            self.connection.execute("PRAGMA journal_mode = WAL")

            # Optimize performance
            self.connection.execute("PRAGMA synchronous = NORMAL")
            self.connection.execute("PRAGMA cache_size = 10000")
            self.connection.execute("PRAGMA temp_store = MEMORY")

            # Set row factory for dictionary access
            self.connection.row_factory = sqlite3.Row

            logger.info("Database connection initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database connection: {e}")
            raise DatabaseError(f"Database connection failed: {e}")

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        if not self.connection:
            self._initialize_connection()
        return self.connection

    def execute_query(
        self,
        query: str,
        params: Optional[Tuple] = None,
        fetch_one: bool = False,
        fetch_all: bool = False,
        commit: bool = False
    ) -> Any:
        """
        Execute database query with parameters

        Args:
            query: SQL query string
            params: Query parameters tuple
            fetch_one: Return single result
            fetch_all: Return all results
            commit: Commit transaction after query

        Returns:
            Query result based on fetch parameters
        """
        with self.lock:
            try:
                cursor = self.connection.cursor()

                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)

                result = None

                if fetch_one:
                    result = cursor.fetchone()
                    if result:
                        result = dict(result)

                elif fetch_all:
                    result = cursor.fetchall()
                    result = [dict(row) for row in result]

                if commit:
                    self.connection.commit()

                cursor.close()
                return result

            except sqlite3.Error as e:
                logger.error(f"Query execution failed: {e}")
                logger.error(f"Query: {query}")
                logger.error(f"Params: {params}")

                if commit:
                    self.connection.rollback()

                raise DatabaseError(f"Query execution failed: {e}")

    def execute_many(
        self,
        query: str,
        params_list: List[Tuple],
        commit: bool = True
    ) -> int:
        """
        Execute query multiple times with different parameters

        Args:
            query: SQL query string
            params_list: List of parameter tuples
            commit: Commit transaction after execution

        Returns:
            Number of affected rows
        """
        with self.lock:
            try:
                cursor = self.connection.cursor()
                cursor.executemany(query, params_list)

                affected_rows = cursor.rowcount

                if commit:
                    self.connection.commit()

                cursor.close()
                return affected_rows

            except sqlite3.Error as e:
                logger.error(f"Multiple query execution failed: {e}")
                logger.error(f"Query: {query}")

                if commit:
                    self.connection.rollback()

                raise DatabaseError(f"Multiple query execution failed: {e}")

    @contextmanager
    def transaction(self):
        """Context manager for database transactions"""
        try:
            with self.lock:
                self.connection.execute("BEGIN")
                yield self.connection
                self.connection.commit()
        except Exception as e:
            logger.error(f"Transaction failed: {e}")
            self.connection.rollback()
            raise DatabaseError(f"Transaction failed: {e}")

    def begin_transaction(self):
        """Begin explicit transaction"""
        with self.lock:
            self.connection.execute("BEGIN")
        logger.info("Transaction begun")

    def commit_transaction(self):
        """Commit current transaction"""
        with self.lock:
            self.connection.commit()
        logger.info("Transaction committed")

    def rollback_transaction(self):
        """Rollback current transaction"""
        with self.lock:
            self.connection.rollback()
        logger.info("Transaction rolled back")

    def insert_record(
        self,
        table: str,
        data: Dict[str, Any],
        return_id: bool = True
    ) -> Optional[int]:
        """
        Insert record into table

        Args:
            table: Table name
            data: Dictionary of column values
            return_id: Return inserted record ID

        Returns:
            Inserted record ID if return_id=True
        """
        try:
            columns = list(data.keys())
            values = list(data.values())
            placeholders = ["?" for _ in values]

            query = f"""
                INSERT INTO {table} ({', '.join(columns)})
                VALUES ({', '.join(placeholders)})
            """

            if return_id:
                query += " RETURNING id"

            with self.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(query, values)

                if return_id:
                    result = cursor.fetchone()
                    inserted_id = result['id'] if result else None
                else:
                    inserted_id = None

                cursor.close()
                return inserted_id

        except Exception as e:
            logger.error(f"Insert record failed: {e}")
            raise DatabaseError(f"Insert record failed: {e}")

    def update_record(
        self,
        table: str,
        data: Dict[str, Any],
        where_clause: str,
        where_params: Optional[Tuple] = None
    ) -> int:
        """
        Update record in table

        Args:
            table: Table name
            data: Dictionary of column values to update
            where_clause: WHERE clause for update
            where_params: Parameters for WHERE clause

        Returns:
            Number of affected rows
        """
        try:
            set_clauses = [f"{column} = ?" for column in data.keys()]
            values = list(data.values())

            query = f"""
                UPDATE {table}
                SET {', '.join(set_clauses)}
                WHERE {where_clause}
            """

            if where_params:
                values.extend(where_params)

            with self.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(query, values)
                affected_rows = cursor.rowcount
                cursor.close()

                return affected_rows

        except Exception as e:
            logger.error(f"Update record failed: {e}")
            raise DatabaseError(f"Update record failed: {e}")

    def delete_record(
        self,
        table: str,
        where_clause: str,
        where_params: Optional[Tuple] = None
    ) -> int:
        """
        Delete record from table

        Args:
            table: Table name
            where_clause: WHERE clause for delete
            where_params: Parameters for WHERE clause

        Returns:
            Number of affected rows
        """
        try:
            query = f"DELETE FROM {table} WHERE {where_clause}"

            with self.transaction() as conn:
                cursor = conn.cursor()
                cursor.execute(query, where_params or ())
                affected_rows = cursor.rowcount
                cursor.close()

                return affected_rows

        except Exception as e:
            logger.error(f"Delete record failed: {e}")
            raise DatabaseError(f"Delete record failed: {e}")

    def get_record_by_id(
        self,
        table: str,
        record_id: int,
        id_column: str = "id"
    ) -> Optional[Dict[str, Any]]:
        """
        Get record by ID

        Args:
            table: Table name
            record_id: Record ID
            id_column: ID column name

        Returns:
            Record dictionary or None
        """
        try:
            query = f"SELECT * FROM {table} WHERE {id_column} = ?"
            result = self.execute_query(query, (record_id,), fetch_one=True)
            return result

        except Exception as e:
            logger.error(f"Get record by ID failed: {e}")
            raise DatabaseError(f"Get record by ID failed: {e}")

    def get_records(
        self,
        table: str,
        where_clause: Optional[str] = None,
        where_params: Optional[Tuple] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get records from table with optional filtering

        Args:
            table: Table name
            where_clause: WHERE clause for filtering
            where_params: Parameters for WHERE clause
            order_by: ORDER BY clause
            limit: LIMIT clause

        Returns:
            List of record dictionaries
        """
        try:
            query = f"SELECT * FROM {table}"
            params = []

            if where_clause:
                query += f" WHERE {where_clause}"
                if where_params:
                    params.extend(where_params)

            if order_by:
                query += f" ORDER BY {order_by}"

            if limit:
                query += f" LIMIT {limit}"

            result = self.execute_query(query, tuple(params) if params else None, fetch_all=True)
            return result or []

        except Exception as e:
            logger.error(f"Get records failed: {e}")
            raise DatabaseError(f"Get records failed: {e}")

    def table_exists(self, table_name: str) -> bool:
        """Check if table exists in database"""
        try:
            query = """
                SELECT name FROM sqlite_master
                WHERE type='table' AND name=?
            """
            result = self.execute_query(query, (table_name,), fetch_one=True)
            return result is not None

        except Exception as e:
            logger.error(f"Table existence check failed: {e}")
            return False

    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """Get table schema information"""
        try:
            query = f"PRAGMA table_info({table_name})"
            result = self.execute_query(query, fetch_all=True)
            return result or []

        except Exception as e:
            logger.error(f"Get table info failed: {e}")
            raise DatabaseError(f"Get table info failed: {e}")

    def backup_database(self, backup_path: str, encrypt: bool = False) -> bool:
        """
        Create database backup

        Args:
            backup_path: Path for backup file
            encrypt: Whether to encrypt backup

        Returns:
            True if backup successful
        """
        try:
            if encrypt:
                from .backup_manager import BackupManager
                backup_manager = BackupManager(self)
                return backup_manager.create_backup(backup_path, encrypt=True)
            else:
                # Simple file copy for unencrypted backup
                import shutil
                shutil.copy2(self.db_path, backup_path)
                logger.info(f"Database backed up to: {backup_path}")
                return True

        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return False

    def restore_database(self, backup_path: str, password: Optional[str] = None) -> bool:
        """
        Restore database from backup

        Args:
            backup_path: Path to backup file
            password: Password for encrypted backup

        Returns:
            True if restore successful
        """
        try:
            if password:
                from .backup_manager import BackupManager
                backup_manager = BackupManager(self)
                return backup_manager.restore_backup(backup_path, password)
            else:
                # Simple file copy for unencrypted backup
                import shutil
                self.close_connection()
                shutil.copy2(backup_path, self.db_path)
                self._initialize_connection()
                logger.info(f"Database restored from: {backup_path}")
                return True

        except Exception as e:
            logger.error(f"Database restore failed: {e}")
            return False

    def get_database_size(self) -> int:
        """Get database file size in bytes"""
        try:
            if os.path.exists(self.db_path):
                return os.path.getsize(self.db_path)
            return 0

        except Exception as e:
            logger.error(f"Get database size failed: {e}")
            return 0

    def vacuum_database(self) -> bool:
        """Optimize database with VACUUM command"""
        try:
            with self.lock:
                self.connection.execute("VACUUM")
                logger.info("Database vacuum completed")
                return True

        except Exception as e:
            logger.error(f"Database vacuum failed: {e}")
            return False

    def close_connection(self):
        """Close database connection"""
        try:
            if self.connection:
                self.connection.close()
                self.connection = None
                logger.info("Database connection closed")

        except Exception as e:
            logger.error(f"Failed to close database connection: {e}")

    def __del__(self):
        """Cleanup on object deletion"""
        self.close_connection()

class DatabaseError(Exception):
    """Custom database error exception"""
    pass