#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
User Manager
User authentication and authorization
"""

import logging
import hashlib
import secrets
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class UserManager:
    """User authentication and authorization"""

    def __init__(self, db_manager):
        """
        Initialize User Manager

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.max_login_attempts = 5
        self.session_timeout_minutes = 480  # 8 hours
        logger.info("User Manager initialized")

    def create_user(
        self,
        username: str,
        password: str,
        full_name: str,
        email: Optional[str] = None,
        role: str = "viewer",
        created_by: Optional[int] = None
    ) -> Optional[int]:
        """
        Create new user

        Args:
            username: Unique username
            password: Plain text password
            full_name: User's full name
            email: User's email address
            role: User role (admin, accountant, viewer)
            created_by: User ID creating this user

        Returns:
            New user ID or None if failed
        """
        try:
            # Validate inputs
            if not self._validate_user_inputs(username, password, full_name, role):
                return None

            # Check if username already exists
            if self.username_exists(username):
                logger.error(f"Username '{username}' already exists")
                return None

            # Hash password
            password_hash = self._hash_password(password)

            user_data = {
                "username": username,
                "password_hash": password_hash,
                "full_name": full_name,
                "email": email,
                "role": role,
                "is_active": True,
                "failed_login_attempts": 0,
                "created_by": created_by
            }

            user_id = self.db_manager.insert_record("users", user_data)

            if user_id:
                logger.info(f"User '{username}' created successfully with ID: {user_id}")

                # Log the action
                self._log_user_action("CREATE", user_id, None, user_data, created_by)

            return user_id

        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            return None

    def _validate_user_inputs(self, username: str, password: str, full_name: str, role: str) -> bool:
        """Validate user creation inputs"""

        # Validate required fields
        if not username or not password or not full_name:
            logger.error("Username, password, and full name are required")
            return False

        # Validate username format
        if len(username) < 3 or len(username) > 50:
            logger.error("Username must be between 3 and 50 characters")
            return False

        if not username.replace('_', '').replace('-', '').isalnum():
            logger.error("Username can only contain letters, numbers, underscores, and hyphens")
            return False

        # Validate password strength
        if len(password) < 6:
            logger.error("Password must be at least 6 characters long")
            return False

        # Validate role
        if role not in ['admin', 'accountant', 'viewer']:
            logger.error(f"Invalid role: {role}")
            return False

        return True

    def username_exists(self, username: str) -> bool:
        """Check if username already exists"""

        try:
            query = "SELECT id FROM users WHERE username = ?"
            result = self.db_manager.execute_query(query, (username,), fetch_one=True)
            return result is not None

        except Exception as e:
            logger.error(f"Failed to check username existence: {e}")
            return False

    def _hash_password(self, password: str) -> str:
        """Hash password using SHA-256 (in production, use bcrypt or argon2)"""

        # For now using SHA-256, but in production use bcrypt
        salt = secrets.token_hex(32)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"

    def _verify_password(self, password: str, stored_hash: str) -> bool:
        """Verify password against stored hash"""

        try:
            if ':' not in stored_hash:
                # Legacy hash without salt
                return hashlib.sha256(password.encode()).hexdigest() == stored_hash

            salt, hash_value = stored_hash.split(':', 1)
            computed_hash = hashlib.sha256((password + salt).encode()).hexdigest()
            return computed_hash == hash_value

        except Exception as e:
            logger.error(f"Password verification failed: {e}")
            return False

    def authenticate_user(self, username: str, password: str, ip_address: str = None, user_agent: str = None) -> Optional[Dict[str, Any]]:
        """
        Authenticate user with username and password

        Args:
            username: User username
            password: User password
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            User data if authentication successful, None otherwise
        """
        try:
            # Get user by username
            user = self.get_user_by_username(username)
            if not user:
                logger.warning(f"Login attempt with non-existent username: {username}")
                return None

            # Check if user is active
            if not user['is_active']:
                logger.warning(f"Login attempt for inactive user: {username}")
                return None

            # Check failed login attempts
            if user['failed_login_attempts'] >= self.max_login_attempts:
                logger.warning(f"Account locked due to too many failed attempts: {username}")
                return None

            # Verify password
            if not self._verify_password(password, user['password_hash']):
                # Increment failed attempts
                self._increment_failed_attempts(user['id'])
                logger.warning(f"Invalid password for user: {username}")
                return None

            # Reset failed attempts on successful login
            self._reset_failed_attempts(user['id'])

            # Update last login
            self._update_last_login(user['id'], ip_address, user_agent)

            logger.info(f"User '{username}' authenticated successfully")

            # Return user data (without password hash)
            user_data = dict(user)
            del user_data['password_hash']
            return user_data

        except Exception as e:
            logger.error(f"Authentication failed: {e}")
            return None

    def _increment_failed_attempts(self, user_id: int):
        """Increment failed login attempts"""

        try:
            current_attempts = self.db_manager.execute_query(
                "SELECT failed_login_attempts FROM users WHERE id = ?",
                (user_id,),
                fetch_one=True
            )

            if current_attempts:
                new_attempts = current_attempts['failed_login_attempts'] + 1
                self.db_manager.update_record(
                    "users",
                    {"failed_login_attempts": new_attempts},
                    "id = ?",
                    (user_id,)
                )

                # Lock account if max attempts reached
                if new_attempts >= self.max_login_attempts:
                    self.db_manager.update_record(
                        "users",
                        {"is_active": False},
                        "id = ?",
                        (user_id,)
                    )
                    logger.warning(f"User account {user_id} locked due to too many failed attempts")

        except Exception as e:
            logger.error(f"Failed to increment failed attempts: {e}")

    def _reset_failed_attempts(self, user_id: int):
        """Reset failed login attempts after successful login"""

        try:
            self.db_manager.update_record(
                "users",
                {"failed_login_attempts": 0},
                "id = ?",
                (user_id,)
            )

        except Exception as e:
            logger.error(f"Failed to reset failed attempts: {e}")

    def _update_last_login(self, user_id: int, ip_address: str = None, user_agent: str = None):
        """Update user's last login information"""

        try:
            update_data = {"last_login": datetime.now()}

            # Store IP address and user agent in audit log
            if ip_address or user_agent:
                audit_data = {
                    "user_id": user_id,
                    "action": "LOGIN",
                    "ip_address": ip_address,
                    "user_agent": user_agent,
                    "timestamp": datetime.now()
                }
                self.db_manager.insert_record("audit_log", audit_data, return_id=False)

            # Note: We don't update the users table with IP/user agent for privacy
            # This information is kept in audit logs

        except Exception as e:
            logger.error(f"Failed to update last login: {e}")

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username"""

        try:
            query = "SELECT * FROM users WHERE username = ?"
            result = self.db_manager.execute_query(query, (username,), fetch_one=True)
            return result

        except Exception as e:
            logger.error(f"Failed to get user by username: {e}")
            return None

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""

        try:
            query = "SELECT * FROM users WHERE id = ?"
            result = self.db_manager.execute_query(query, (user_id,), fetch_one=True)
            return result

        except Exception as e:
            logger.error(f"Failed to get user by ID: {e}")
            return None

    def update_user(self, user_id: int, **kwargs) -> bool:
        """
        Update user information

        Args:
            user_id: User ID to update
            **kwargs: Fields to update

        Returns:
            True if update successful
        """
        try:
            # Get current user data for logging
            current_data = self.get_user_by_id(user_id)
            if not current_data:
                logger.error(f"User not found: {user_id}")
                return False

            # Validate update data
            if not self._validate_user_update(user_id, kwargs):
                return False

            # Hash new password if provided
            if 'password' in kwargs:
                kwargs['password_hash'] = self._hash_password(kwargs['password'])
                del kwargs['password']

            # Update user
            affected_rows = self.db_manager.update_record(
                "users",
                kwargs,
                "id = ?",
                (user_id,)
            )

            if affected_rows > 0:
                logger.info(f"User {user_id} updated successfully")

                # Log the action
                self._log_user_action("UPDATE", user_id, current_data, kwargs, kwargs.get('updated_by'))

                return True

            return False

        except Exception as e:
            logger.error(f"Failed to update user: {e}")
            return False

    def _validate_user_update(self, user_id: int, update_data: Dict[str, Any]) -> bool:
        """Validate user update data"""

        # Cannot change username if it's already used
        if 'username' in update_data:
            existing_user = self.get_user_by_username(update_data['username'])
            if existing_user and existing_user['id'] != user_id:
                logger.error("Username already in use")
                return False

        # Validate role
        if 'role' in update_data and update_data['role'] not in ['admin', 'accountant', 'viewer']:
            logger.error("Invalid role")
            return False

        return True

    def delete_user(self, user_id: int, deleted_by: Optional[int] = None) -> bool:
        """
        Delete user with validation

        Args:
            user_id: User ID to delete
            deleted_by: User ID performing the deletion

        Returns:
            True if deletion successful
        """
        try:
            user = self.get_user_by_id(user_id)
            if not user:
                logger.error(f"User not found: {user_id}")
                return False

            # Cannot delete the last admin user
            if user['role'] == 'admin':
                admin_count = self.db_manager.execute_query(
                    "SELECT COUNT(*) as count FROM users WHERE role = 'admin' AND is_active = 1",
                    fetch_one=True
                )
                if admin_count and admin_count['count'] <= 1:
                    logger.error("Cannot delete the last admin user")
                    return False

            # Check for dependent records (sessions, audit logs, etc.)
            if not self._validate_user_deletion(user_id):
                return False

            # Log before deletion
            self._log_user_action("DELETE", user_id, user, None, deleted_by)

            # Delete user sessions first
            self.db_manager.delete_record("user_sessions", "user_id = ?", (user_id,))

            # Delete user
            affected_rows = self.db_manager.delete_record("users", "id = ?", (user_id,))

            if affected_rows > 0:
                logger.info(f"User {user_id} deleted successfully")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to delete user: {e}")
            return False

    def _validate_user_deletion(self, user_id: int) -> bool:
        """Validate if user can be deleted"""

        try:
            # Check for created journal entries
            entry_count = self.db_manager.execute_query(
                "SELECT COUNT(*) as count FROM journal_entries WHERE created_by = ?",
                (user_id,),
                fetch_one=True
            )

            if entry_count and entry_count['count'] > 0:
                logger.error("Cannot delete user with created journal entries")
                return False

            # Check for created accounts
            account_count = self.db_manager.execute_query(
                "SELECT COUNT(*) as count FROM accounts WHERE created_by = ?",
                (user_id,),
                fetch_one=True
            )

            if account_count and account_count['count'] > 0:
                logger.error("Cannot delete user with created accounts")
                return False

            return True

        except Exception as e:
            logger.error(f"User deletion validation failed: {e}")
            return False

    def get_user_permissions(self, user_id: int) -> List[str]:
        """Get user permissions based on role"""

        try:
            user = self.get_user_by_id(user_id)
            if not user or not user['is_active']:
                return []

            role_permissions = {
                'admin': [
                    'user.create', 'user.update', 'user.delete', 'user.view',
                    'account.create', 'account.update', 'account.delete', 'account.view',
                    'journal.create', 'journal.update', 'journal.delete', 'journal.view', 'journal.post', 'journal.approve',
                    'report.view', 'report.create', 'report.export',
                    'settings.update', 'settings.view',
                    'backup.create', 'backup.restore',
                    'system.admin'
                ],
                'accountant': [
                    'account.view',
                    'journal.create', 'journal.update', 'journal.view', 'journal.post',
                    'report.view', 'report.export',
                    'settings.view'
                ],
                'viewer': [
                    'account.view',
                    'journal.view',
                    'report.view'
                ]
            }

            return role_permissions.get(user['role'], [])

        except Exception as e:
            logger.error(f"Failed to get user permissions: {e}")
            return []

    def check_permission(self, user_id: int, required_permission: str) -> bool:
        """Check if user has specific permission"""

        try:
            user_permissions = self.get_user_permissions(user_id)
            return required_permission in user_permissions

        except Exception as e:
            logger.error(f"Permission check failed: {e}")
            return False

    def get_all_users(self, include_inactive: bool = False) -> List[Dict[str, Any]]:
        """Get all users"""

        try:
            query = "SELECT * FROM users"
            if not include_inactive:
                query += " WHERE is_active = 1"

            query += " ORDER BY username"

            result = self.db_manager.execute_query(query, fetch_all=True)
            return result or []

        except Exception as e:
            logger.error(f"Failed to get all users: {e}")
            return []

    def reset_password(self, user_id: int, new_password: str, reset_by: Optional[int] = None) -> bool:
        """
        Reset user password

        Args:
            user_id: User ID to reset password for
            new_password: New plain text password
            reset_by: User ID performing the reset

        Returns:
            True if reset successful
        """
        try:
            # Validate password
            if len(new_password) < 6:
                logger.error("Password must be at least 6 characters long")
                return False

            user = self.get_user_by_id(user_id)
            if not user:
                logger.error(f"User not found: {user_id}")
                return False

            # Hash new password
            password_hash = self._hash_password(new_password)

            # Update password
            update_data = {
                "password_hash": password_hash,
                "failed_login_attempts": 0,  # Reset failed attempts
                "is_active": True  # Reactivate account if locked
            }

            affected_rows = self.db_manager.update_record(
                "users",
                update_data,
                "id = ?",
                (user_id,)
            )

            if affected_rows > 0:
                logger.info(f"Password reset successfully for user {user_id}")

                # Log the action
                self._log_user_action("PASSWORD_RESET", user_id, user, {"reset_by": reset_by}, reset_by)

                return True

            return False

        except Exception as e:
            logger.error(f"Failed to reset password: {e}")
            return False

    def _log_user_action(self, action: str, user_id: int, old_data: Optional[Dict], new_data: Optional[Dict], performed_by: Optional[int]):
        """Log user-related actions"""

        try:
            import json

            audit_data = {
                "user_id": performed_by,
                "action": f"USER_{action}",
                "table_name": "users",
                "record_id": user_id,
                "old_values": json.dumps(old_data) if old_data else None,
                "new_values": json.dumps(new_data) if new_data else None,
                "timestamp": datetime.now()
            }

            self.db_manager.insert_record("audit_log", audit_data, return_id=False)

        except Exception as e:
            logger.error(f"Failed to log user action: {e}")

    def get_user_activity(self, user_id: int, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent user activity from audit log"""

        try:
            query = """
                SELECT * FROM audit_log
                WHERE user_id = ? OR record_id = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """
            result = self.db_manager.execute_query(query, (user_id, user_id, limit), fetch_all=True)
            return result or []

        except Exception as e:
            logger.error(f"Failed to get user activity: {e}")
            return []

    def lock_user(self, user_id: int, locked_by: Optional[int] = None) -> bool:
        """Lock user account"""

        try:
            affected_rows = self.db_manager.update_record(
                "users",
                {"is_active": False},
                "id = ?",
                (user_id,)
            )

            if affected_rows > 0:
                logger.info(f"User {user_id} locked successfully")
                self._log_user_action("LOCK", user_id, None, {"locked_by": locked_by}, locked_by)
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to lock user: {e}")
            return False

    def unlock_user(self, user_id: int, unlocked_by: Optional[int] = None) -> bool:
        """Unlock user account"""

        try:
            update_data = {
                "is_active": True,
                "failed_login_attempts": 0
            }

            affected_rows = self.db_manager.update_record(
                "users",
                update_data,
                "id = ?",
                (user_id,)
            )

            if affected_rows > 0:
                logger.info(f"User {user_id} unlocked successfully")
                self._log_user_action("UNLOCK", user_id, None, {"unlocked_by": unlocked_by}, unlocked_by)
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to unlock user: {e}")
            return False