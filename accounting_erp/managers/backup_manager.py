#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Backup Manager
Automated backup and restore functionality
"""

import logging
import os
import shutil
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
from pathlib import Path
import zipfile
import hashlib

logger = logging.getLogger(__name__)

class BackupManager:
    """Automated backup and restore functionality"""

    def __init__(self, db_manager):
        """
        Initialize Backup Manager

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.backup_dir = "backups"
        self.max_backup_files = 50
        self.default_retention_days = 30

        # Ensure backup directory exists
        os.makedirs(self.backup_dir, exist_ok=True)

        logger.info("Backup Manager initialized")

    def create_backup(self, backup_path: Optional[str] = None, encrypt: bool = True,
                     compress: bool = True) -> Optional[str]:
        """
        Create database backup

        Args:
            backup_path: Custom backup file path
            encrypt: Whether to encrypt backup
            compress: Whether to compress backup

        Returns:
            Path to created backup file or None if failed
        """
        try:
            # Generate backup filename if not provided
            if not backup_path:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = os.path.join(self.backup_dir, f"backup_{timestamp}.db")

            # Create backup directory if needed
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)

            # Close existing connection
            original_connection = self.db_manager.connection
            self.db_manager.close_connection()

            try:
                # Create backup
                source_db = self.db_manager.db_path
                shutil.copy2(source_db, backup_path)

                # Create backup metadata
                metadata = self.create_backup_metadata(backup_path, encrypt, compress)

                # Compress if requested
                if compress:
                    backup_path = self.compress_backup(backup_path, metadata)

                # Encrypt if requested
                if encrypt:
                    backup_path = self.encrypt_backup(backup_path, metadata)

                # Log backup creation
                self.log_backup_action("CREATE", backup_path, metadata)

                logger.info(f"Backup created successfully: {backup_path}")
                return backup_path

            finally:
                # Restore connection
                self.db_manager._initialize_connection()

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None

    def create_backup_metadata(self, backup_path: str, encrypt: bool, compress: bool) -> Dict[str, Any]:
        """Create backup metadata"""
        try:
            # Get database stats
            db_stats = self.get_database_stats()

            metadata = {
                "version": "1.0.0",
                "created_at": datetime.now().isoformat(),
                "created_by": self.db_manager.execute_query(
                    "SELECT username FROM users WHERE is_active = 1 LIMIT 1",
                    fetch_one=True
                ).get('username') if self.db_manager.table_exists('users') else 'system',
                "file_path": backup_path,
                "file_size": os.path.getsize(backup_path),
                "encrypted": encrypt,
                "compressed": compress,
                "database_stats": db_stats,
                "checksum": self.calculate_checksum(backup_path),
                "schema_version": "1.0.0"
            }

            # Save metadata to JSON file
            metadata_path = backup_path.replace('.db', '_metadata.json')
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            return metadata

        except Exception as e:
            logger.error(f"Failed to create backup metadata: {e}")
            return {}

    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            stats = {}

            # Get table counts
            tables = ['users', 'accounts', 'fiscal_years', 'journal_entries',
                     'journal_lines', 'settings', 'audit_log']

            for table in tables:
                if self.db_manager.table_exists(table):
                    count = self.db_manager.execute_query(
                        f"SELECT COUNT(*) as count FROM {table}",
                        fetch_one=True
                    )
                    stats[f"{table}_count"] = count['count'] if count else 0
                else:
                    stats[f"{table}_count"] = 0

            # Get total size
            stats['database_size'] = os.path.getsize(self.db_manager.db_path)

            # Get last entry date
            if self.db_manager.table_exists('journal_entries'):
                last_entry = self.db_manager.execute_query(
                    "SELECT MAX(date) as last_date FROM journal_entries",
                    fetch_one=True
                )
                stats['last_entry_date'] = last_entry['last_date'] if last_entry else None

            return stats

        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {}

    def calculate_checksum(self, file_path: str) -> str:
        """Calculate file checksum"""
        try:
            hash_md5 = hashlib.md5()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_md5.update(chunk)
            return hash_md5.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate checksum: {e}")
            return ""

    def compress_backup(self, backup_path: str, metadata: Dict[str, Any]) -> str:
        """Compress backup file"""
        try:
            compressed_path = backup_path.replace('.db', '.zip')

            with zipfile.ZipFile(compressed_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(backup_path, os.path.basename(backup_path))

                # Add metadata
                metadata_path = backup_path.replace('.db', '_metadata.json')
                if os.path.exists(metadata_path):
                    zipf.write(metadata_path, os.path.basename(metadata_path))

            # Remove original files
            os.remove(backup_path)
            if os.path.exists(metadata_path):
                os.remove(metadata_path)

            logger.info(f"Backup compressed: {compressed_path}")
            return compressed_path

        except Exception as e:
            logger.error(f"Failed to compress backup: {e}")
            return backup_path

    def encrypt_backup(self, backup_path: str, metadata: Dict[str, Any]) -> str:
        """Encrypt backup file (placeholder implementation)"""
        try:
            # For now, just return the original path
            # In a real implementation, you would use proper encryption
            logger.info(f"Backup encryption requested for: {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Failed to encrypt backup: {e}")
            return backup_path

    def restore_backup(self, backup_path: str, password: Optional[str] = None,
                       verify_before_restore: bool = True) -> bool:
        """
        Restore database from backup

        Args:
            backup_path: Path to backup file
            password: Backup password if encrypted
            verify_before_restore: Verify backup before restoring

        Returns:
            True if restore successful
        """
        try:
            # Validate backup file
            if not os.path.exists(backup_path):
                logger.error(f"Backup file not found: {backup_path}")
                return False

            # Decompress if needed
            if backup_path.endswith('.zip'):
                backup_path = self.decompress_backup(backup_path)

            # Load metadata
            metadata_path = backup_path.replace('.db', '_metadata.json')
            if os.path.exists(metadata_path):
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            else:
                metadata = {}

            # Verify backup if requested
            if verify_before_restore:
                if not self.verify_backup(backup_path, metadata):
                    logger.error("Backup verification failed")
                    return False

            # Confirm restore
            from tkinter import messagebox
            if not messagebox.askyesno(
                "Confirm Restore",
                "Are you sure you want to restore from backup?\n"
                "This will replace the current database.\n\n"
                "هل أنت متأكد من استعادة النسخة الاحتياطية؟\n"
                "سيؤدي هذا إلى استبدال قاعدة البيانات الحالية."
            ):
                return False

            # Create current backup before restore
            current_backup = self.create_backup(
                f"{self.backup_dir}/pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
            )

            # Close database connection
            original_connection = self.db_manager.connection
            self.db_manager.close_connection()

            try:
                # Restore database
                shutil.copy2(backup_path, self.db_manager.db_path)

                # Reinitialize connection
                self.db_manager._initialize_connection()

                # Validate restored database
                if not self.validate_restored_database():
                    logger.error("Restored database validation failed")
                    return False

                # Log restore action
                self.log_backup_action("RESTORE", backup_path, metadata, current_backup)

                logger.info(f"Database restored successfully from: {backup_path}")
                return True

            except Exception as e:
                # If restore fails, try to restore from current backup
                if current_backup and os.path.exists(current_backup):
                    try:
                        shutil.copy2(current_backup, self.db_manager.db_path)
                        self.db_manager._initialize_connection()
                        logger.info("Rollback to pre-restore state successful")
                    except Exception as rollback_e:
                        logger.error(f"Rollback failed: {rollback_e}")

                raise e

            finally:
                # Ensure connection is restored
                try:
                    if not self.db_manager.connection:
                        self.db_manager._initialize_connection()
                except:
                    pass

        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            return False

    def decompress_backup(self, backup_path: str) -> str:
        """Decompress backup file"""
        try:
            with zipfile.ZipFile(backup_path, 'r') as zipf:
                # Extract to backup directory
                extract_path = os.path.join(self.backup_dir, 'temp_extract')
                os.makedirs(extract_path, exist_ok=True)
                zipf.extractall(extract_path)

                # Find the database file
                for filename in os.listdir(extract_path):
                    if filename.endswith('.db'):
                        extracted_path = os.path.join(extract_path, filename)
                        # Move to backup directory with original name
                        final_path = backup_path.replace('.zip', '.db')
                        shutil.move(extracted_path, final_path)

                        # Clean up temp directory
                        shutil.rmtree(extract_path)
                        return final_path

            # If no .db file found, return original path
            return backup_path

        except Exception as e:
            logger.error(f"Failed to decompress backup: {e}")
            return backup_path

    def verify_backup(self, backup_path: str, metadata: Dict[str, Any]) -> bool:
        """Verify backup file integrity"""
        try:
            # Check file exists
            if not os.path.exists(backup_path):
                logger.error("Backup file does not exist")
                return False

            # Verify checksum if metadata exists
            if metadata and 'checksum' in metadata:
                current_checksum = self.calculate_checksum(backup_path)
                if current_checksum != metadata['checksum']:
                    logger.error("Backup checksum mismatch")
                    return False

            # Try to open database file
            try:
                import sqlite3
                conn = sqlite3.connect(backup_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                conn.close()

                # Check if essential tables exist
                essential_tables = {'accounts', 'journal_entries', 'users'}
                existing_tables = {table[0] for table in tables}

                if not essential_tables.issubset(existing_tables):
                    logger.error("Backup missing essential tables")
                    return False

            except Exception as db_e:
                logger.error(f"Backup database verification failed: {db_e}")
                return False

            logger.info("Backup verification successful")
            return True

        except Exception as e:
            logger.error(f"Failed to verify backup: {e}")
            return False

    def validate_restored_database(self) -> bool:
        """Validate restored database"""
        try:
            # Check if database is accessible
            result = self.db_manager.execute_query("SELECT 1", fetch_one=True)
            if not result:
                return False

            # Check essential tables
            essential_tables = ['accounts', 'journal_entries', 'users']
            for table in essential_tables:
                if not self.db_manager.table_exists(table):
                    logger.error(f"Missing essential table: {table}")
                    return False

            logger.info("Restored database validation successful")
            return True

        except Exception as e:
            logger.error(f"Restored database validation failed: {e}")
            return False

    def schedule_backup(self, schedule: str, retention_days: int = None) -> bool:
        """
        Schedule automatic backups

        Args:
            schedule: Schedule type ('daily', 'weekly', 'monthly')
            retention_days: Days to retain backups

        Returns:
            True if scheduling successful
        """
        try:
            if retention_days is None:
                retention_days = self.default_retention_days

            # Save backup schedule to settings
            self.db_manager.insert_record("settings", {
                "key": "backup_schedule",
                "value": json.dumps({
                    "schedule": schedule,
                    "retention_days": retention_days,
                    "enabled": True,
                    "last_run": datetime.now().isoformat()
                }),
                "data_type": "json",
                "description": "Automatic backup schedule configuration",
                "is_system": False
            }, return_id=False)

            # Clean up old backups
            self.cleanup_old_backups(retention_days)

            logger.info(f"Backup schedule set: {schedule}, retention: {retention_days} days")
            return True

        except Exception as e:
            logger.error(f"Failed to schedule backup: {e}")
            return False

    def cleanup_old_backups(self, retention_days: int = None) -> int:
        """
        Clean up old backup files

        Args:
            retention_days: Days to retain backups

        Returns:
            Number of files deleted
        """
        try:
            if retention_days is None:
                retention_days = self.default_retention_days

            cutoff_date = datetime.now() - timedelta(days=retention_days)
            deleted_count = 0

            # Get all backup files
            backup_files = []
            for file_path in Path(self.backup_dir).glob("backup_*.db"):
                backup_files.append(file_path)

            for file_path in Path(self.backup_dir).glob("backup_*.zip"):
                backup_files.append(file_path)

            # Delete old files
            for file_path in backup_files:
                try:
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_date:
                        # Delete metadata file too
                        metadata_path = str(file_path).replace('.db', '_metadata.json')
                        if os.path.exists(metadata_path):
                            os.remove(metadata_path)

                        os.remove(file_path)
                        deleted_count += 1
                        logger.info(f"Deleted old backup: {file_path}")

                except Exception as e:
                    logger.error(f"Failed to delete backup file {file_path}: {e}")

            logger.info(f"Cleanup completed. Deleted {deleted_count} old backup files")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}")
            return 0

    def get_backup_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get backup history"""
        try:
            backups = []

            # Get backup files
            for file_path in Path(self.backup_dir).glob("backup_*.db"):
                try:
                    metadata_path = str(file_path).replace('.db', '_metadata.json')
                    metadata = {}

                    if os.path.exists(metadata_path):
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)

                    backup_info = {
                        "filename": file_path.name,
                        "path": str(file_path),
                        "size": file_path.stat().st_size,
                        "created_at": metadata.get("created_at",
                                         datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()),
                        "checksum": metadata.get("checksum", ""),
                        "metadata": metadata
                    }
                    backups.append(backup_info)

                except Exception as e:
                    logger.error(f"Failed to process backup file {file_path}: {e}")

            # Sort by creation date (newest first)
            backups.sort(key=lambda x: x["created_at"], reverse=True)

            return backups[:limit]

        except Exception as e:
            logger.error(f"Failed to get backup history: {e}")
            return []

    def log_backup_action(self, action: str, backup_path: str, metadata: Dict[str, Any],
                         additional_info: Optional[str] = None):
        """Log backup-related actions"""
        try:
            import json

            audit_data = {
                "user_id": getattr(self.db_manager, 'current_user_id', None),
                "action": f"BACKUP_{action}",
                "table_name": "backups",
                "record_id": backup_path,
                "old_values": None,
                "new_values": json.dumps({
                    "action": action,
                    "backup_path": backup_path,
                    "metadata": metadata,
                    "additional_info": additional_info
                }),
                "timestamp": datetime.now()
            }

            if self.db_manager.table_exists('audit_log'):
                self.db_manager.insert_record("audit_log", audit_data, return_id=False)

        except Exception as e:
            logger.error(f"Failed to log backup action: {e}")