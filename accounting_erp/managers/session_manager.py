#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Session Manager
User session management with token-based authentication
"""

import logging
import secrets
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class SessionManager:
    """User session management"""

    def __init__(self, db_manager):
        """
        Initialize Session Manager

        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager
        self.session_duration_hours = 8  # Default 8 hours
        self.token_length = 64
        logger.info("Session Manager initialized")

    def create_session(self, user_id: int, ip_address: str = None, user_agent: str = None) -> str:
        """
        Create new user session

        Args:
            user_id: User ID
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Session token
        """
        try:
            # Generate secure session token
            session_token = secrets.token_urlsafe(self.token_length)

            # Calculate expiry time
            expires_at = datetime.now() + timedelta(hours=self.session_duration_hours)

            # Clean up old sessions for this user
            self._cleanup_user_sessions(user_id)

            # Create session
            session_data = {
                "user_id": user_id,
                "session_token": session_token,
                "ip_address": ip_address,
                "user_agent": user_agent,
                "expires_at": expires_at,
                "is_active": True
            }

            session_id = self.db_manager.insert_record("user_sessions", session_data)

            if session_id:
                logger.info(f"Session created for user {user_id} with token: {session_token[:20]}...")
                return session_token

            logger.error("Failed to create session")
            return ""

        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            return ""

    def validate_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """
        Validate session token and return user data

        Args:
            session_token: Session token to validate

        Returns:
            User session data if valid, None otherwise
        """
        try:
            if not session_token:
                return None

            # Get session from database
            query = """
                SELECT
                    us.*,
                    u.username,
                    u.full_name,
                    u.email,
                    u.role,
                    u.is_active as user_active
                FROM user_sessions us
                JOIN users u ON us.user_id = u.id
                WHERE us.session_token = ? AND us.is_active = 1
            """
            result = self.db_manager.execute_query(query, (session_token,), fetch_one=True)

            if not result:
                logger.warning(f"Invalid session token: {session_token[:20]}...")
                return None

            # Check if user is active
            if not result['user_active']:
                logger.warning(f"Session for inactive user: {result['username']}")
                self.deactivate_session(session_token)
                return None

            # Check if session has expired
            if datetime.now() > result['expires_at']:
                logger.warning(f"Session expired for user: {result['username']}")
                self.deactivate_session(session_token)
                return None

            # Update last activity (optional)
            self._update_session_activity(session_token)

            logger.debug(f"Session validated for user: {result['username']}")
            return result

        except Exception as e:
            logger.error(f"Session validation failed: {e}")
            return None

    def _update_session_activity(self, session_token: str):
        """Update session last activity timestamp"""

        try:
            # This could extend the session expiry time
            # For now, we'll just log the activity
            pass

        except Exception as e:
            logger.error(f"Failed to update session activity: {e}")

    def get_user_sessions(self, user_id: int, active_only: bool = True) -> list:
        """Get all sessions for a user"""

        try:
            query = """
                SELECT
                    id, session_token, ip_address, user_agent,
                    created_at, expires_at, is_active
                FROM user_sessions
                WHERE user_id = ?
            """

            if active_only:
                query += " AND is_active = 1 AND expires_at > ?"

            query += " ORDER BY created_at DESC"

            params = (user_id, datetime.now()) if active_only else (user_id,)

            result = self.db_manager.execute_query(query, params, fetch_all=True)
            return result or []

        except Exception as e:
            logger.error(f"Failed to get user sessions: {e}")
            return []

    def deactivate_session(self, session_token: str) -> bool:
        """Deactivate a specific session"""

        try:
            affected_rows = self.db_manager.update_record(
                "user_sessions",
                {"is_active": False},
                "session_token = ?",
                (session_token,)
            )

            if affected_rows > 0:
                logger.info(f"Session deactivated: {session_token[:20]}...")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to deactivate session: {e}")
            return False

    def clear_session(self, session_token: str) -> bool:
        """Clear/Remove a session from database"""

        try:
            affected_rows = self.db_manager.delete_record(
                "user_sessions",
                "session_token = ?",
                (session_token,)
            )

            if affected_rows > 0:
                logger.info(f"Session cleared: {session_token[:20]}...")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to clear session: {e}")
            return False

    def clear_user_sessions(self, user_id: int) -> bool:
        """Clear all sessions for a user"""

        try:
            affected_rows = self.db_manager.delete_record(
                "user_sessions",
                "user_id = ?",
                (user_id,)
            )

            if affected_rows > 0:
                logger.info(f"Cleared {affected_rows} sessions for user {user_id}")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to clear user sessions: {e}")
            return False

    def _cleanup_user_sessions(self, user_id: int, keep_latest: int = 3):
        """Clean up old sessions for user, keeping only the latest N sessions"""

        try:
            # Get all active sessions for user
            sessions = self.get_user_sessions(user_id, active_only=True)

            if len(sessions) <= keep_latest:
                return

            # Sort by created_at and keep only the latest N
            sessions.sort(key=lambda x: x['created_at'], reverse=True)
            sessions_to_remove = sessions[keep_latest:]

            # Remove old sessions
            for session in sessions_to_remove:
                self.deactivate_session(session['session_token'])

            logger.info(f"Cleaned up {len(sessions_to_remove)} old sessions for user {user_id}")

        except Exception as e:
            logger.error(f"Failed to cleanup user sessions: {e}")

    def cleanup_expired_sessions(self) -> int:
        """Clean up all expired sessions in the system"""

        try:
            affected_rows = self.db_manager.delete_record(
                "user_sessions",
                "expires_at < ? OR is_active = 0",
                (datetime.now(),)
            )

            if affected_rows > 0:
                logger.info(f"Cleaned up {affected_rows} expired sessions")

            return affected_rows

        except Exception as e:
            logger.error(f"Failed to cleanup expired sessions: {e}")
            return 0

    def extend_session(self, session_token: str, hours: int = None) -> bool:
        """Extend session expiry time"""

        try:
            if hours is None:
                hours = self.session_duration_hours

            new_expiry = datetime.now() + timedelta(hours=hours)

            affected_rows = self.db_manager.update_record(
                "user_sessions",
                {"expires_at": new_expiry},
                "session_token = ? AND is_active = 1",
                (session_token,)
            )

            if affected_rows > 0:
                logger.info(f"Session extended: {session_token[:20]}...")
                return True

            return False

        except Exception as e:
            logger.error(f"Failed to extend session: {e}")
            return False

    def get_active_sessions_count(self) -> int:
        """Get count of active sessions"""

        try:
            query = """
                SELECT COUNT(*) as count
                FROM user_sessions
                WHERE is_active = 1 AND expires_at > ?
            """
            result = self.db_manager.execute_query(query, (datetime.now(),), fetch_one=True)
            return result['count'] if result else 0

        except Exception as e:
            logger.error(f"Failed to get active sessions count: {e}")
            return 0

    def get_session_info(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Get detailed session information"""

        try:
            query = """
                SELECT
                    us.*,
                    u.username,
                    u.full_name,
                    u.role
                FROM user_sessions us
                JOIN users u ON us.user_id = u.id
                WHERE us.session_token = ?
            """
            result = self.db_manager.execute_query(query, (session_token,), fetch_one=True)
            return result

        except Exception as e:
            logger.error(f"Failed to get session info: {e}")
            return None

    def force_logout_user(self, user_id: int, performed_by: int = None) -> bool:
        """Force logout a user by deactivating all their sessions"""

        try:
            # Get user sessions before clearing for logging
            sessions = self.get_user_sessions(user_id)

            # Clear all sessions
            success = self.clear_user_sessions(user_id)

            if success and sessions:
                logger.info(f"Force logout user {user_id}: cleared {len(sessions)} sessions")

                # Log the action
                import json
                audit_data = {
                    "user_id": performed_by,
                    "action": "FORCE_LOGOUT",
                    "table_name": "user_sessions",
                    "record_id": user_id,
                    "new_values": json.dumps({"sessions_cleared": len(sessions)}),
                    "timestamp": datetime.now()
                }
                self.db_manager.insert_record("audit_log", audit_data, return_id=False)

            return success

        except Exception as e:
            logger.error(f"Failed to force logout user: {e}")
            return False

    def get_user_from_session(self, session_token: str) -> Optional[Dict[str, Any]]:
        """Get user information from session token"""

        try:
            session = self.validate_session(session_token)
            if not session:
                return None

            # Return user data without sensitive information
            user_data = {
                "id": session['user_id'],
                "username": session['username'],
                "full_name": session['full_name'],
                "email": session['email'],
                "role": session['role']
            }

            return user_data

        except Exception as e:
            logger.error(f"Failed to get user from session: {e}")
            return None

    def is_session_valid(self, session_token: str) -> bool:
        """Check if session token is valid without returning user data"""

        try:
            if not session_token:
                return False

            session = self.validate_session(session_token)
            return session is not None

        except Exception as e:
            logger.error(f"Session validation check failed: {e}")
            return False

    def update_session_duration(self, hours: int):
        """Update default session duration for new sessions"""

        try:
            if hours < 1 or hours > 168:  # Max 1 week
                logger.warning(f"Invalid session duration: {hours}. Using default.")
                return

            self.session_duration_hours = hours
            logger.info(f"Session duration updated to {hours} hours")

        except Exception as e:
            logger.error(f"Failed to update session duration: {e}")

    def get_sessions_by_ip(self, ip_address: str) -> list:
        """Get all sessions from a specific IP address"""

        try:
            query = """
                SELECT
                    us.*,
                    u.username,
                    u.full_name
                FROM user_sessions us
                JOIN users u ON us.user_id = u.id
                WHERE us.ip_address = ? AND us.is_active = 1 AND us.expires_at > ?
                ORDER BY us.created_at DESC
            """
            result = self.db_manager.execute_query(query, (ip_address, datetime.now()), fetch_all=True)
            return result or []

        except Exception as e:
            logger.error(f"Failed to get sessions by IP: {e}")
            return []