#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
Error Handling
Comprehensive error handling and logging system
"""

import logging
import traceback
import sys
import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from functools import wraps
from enum import Enum

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class ErrorCategory(Enum):
    """Error categories"""
    DATABASE = "database"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    VALIDATION = "validation"
    BUSINESS_LOGIC = "business_logic"
    USER_INTERFACE = "user_interface"
    FILE_SYSTEM = "file_system"
    NETWORK = "network"
    SYSTEM = "system"
    UNKNOWN = "unknown"

class AccountingError(Exception):
    """Custom base exception for accounting system"""

    def __init__(self, message: str, category: ErrorCategory = ErrorCategory.UNKNOWN,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 error_code: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.now()
        self.traceback_info = traceback.format_exc()

class DatabaseError(AccountingError):
    """Database-related errors"""
    def __init__(self, message: str, error_code: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCategory.DATABASE, ErrorSeverity.HIGH,
                        error_code, details)

class AuthenticationError(AccountingError):
    """Authentication-related errors"""
    def __init__(self, message: str, error_code: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCategory.AUTHENTICATION, ErrorSeverity.HIGH,
                        error_code, details)

class AuthorizationError(AccountingError):
    """Authorization-related errors"""
    def __init__(self, message: str, error_code: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCategory.AUTHORIZATION, ErrorSeverity.MEDIUM,
                        error_code, details)

class ValidationError(AccountingError):
    """Validation-related errors"""
    def __init__(self, message: str, error_code: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCategory.VALIDATION, ErrorSeverity.LOW,
                        error_code, details)

class BusinessLogicError(AccountingError):
    """Business logic errors"""
    def __init__(self, message: str, error_code: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCategory.BUSINESS_LOGIC, ErrorSeverity.MEDIUM,
                        error_code, details)

class UserInterfaceError(AccountingError):
    """UI-related errors"""
    def __init__(self, message: str, error_code: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCategory.USER_INTERFACE, ErrorSeverity.LOW,
                        error_code, details)

class FileSystemError(AccountingError):
    """File system errors"""
    def __init__(self, message: str, error_code: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCategory.FILE_SYSTEM, ErrorSeverity.HIGH,
                        error_code, details)

class NetworkError(AccountingError):
    """Network-related errors"""
    def __init__(self, message: str, error_code: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        super().__init__(message, ErrorCategory.NETWORK, ErrorSeverity.MEDIUM,
                        error_code, details)

class ErrorHandler:
    """Centralized error handling and logging"""

    def __init__(self, log_file: str = "error_log.json"):
        """
        Initialize error handler

        Args:
            log_file: Path to error log file
        """
        self.log_file = log_file
        self.error_counts = {}
        self.last_errors = {}
        self.error_callbacks = {}

        # Setup logger
        self.setup_logger()

    def setup_logger(self):
        """Setup custom logger"""
        try:
            # Create logger
            self.logger = logging.getLogger("accounting_erp")
            self.logger.setLevel(logging.DEBUG)

            # Create formatters
            detailed_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s - %(funcName)s:%(lineno)d'
            )

            simple_formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )

            # Console handler
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_handler.setFormatter(simple_formatter)
            self.logger.addHandler(console_handler)

            # File handler
            os.makedirs("logs", exist_ok=True)
            file_handler = logging.FileHandler("logs/app_errors.log", encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(detailed_formatter)
            self.logger.addHandler(file_handler)

        except Exception as e:
            print(f"Failed to setup logger: {e}")

    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handle and log error

        Args:
            error: Exception to handle
            context: Additional context information

        Returns:
            Error information dictionary
        """
        try:
            # Determine error type and create error object if needed
            if not isinstance(error, AccountingError):
                accounting_error = AccountingError(
                    str(error),
                    ErrorCategory.UNKNOWN,
                    ErrorSeverity.MEDIUM
                )
            else:
                accounting_error = error

            # Add context
            if context:
                accounting_error.details.update(context)

            # Create error info
            error_info = {
                'message': accounting_error.message,
                'category': accounting_error.category.value,
                'severity': accounting_error.severity.value,
                'error_code': accounting_error.error_code,
                'details': accounting_error.details,
                'timestamp': accounting_error.timestamp.isoformat(),
                'traceback': accounting_error.traceback_info
            }

            # Log error
            self.log_error(accounting_error)

            # Update error statistics
            self.update_error_stats(accounting_error)

            # Trigger callbacks
            self.trigger_error_callbacks(accounting_error)

            # Check for error patterns and escalation
            self.check_error_patterns(accounting_error)

            return error_info

        except Exception as e:
            print(f"Error in error handler: {e}")
            return {
                'message': str(error),
                'category': ErrorCategory.SYSTEM.value,
                'severity': ErrorSeverity.CRITICAL.value,
                'timestamp': datetime.now().isoformat()
            }

    def log_error(self, error: AccountingError):
        """Log error to various outputs"""
        try:
            # Log to application logger
            log_level = {
                ErrorSeverity.LOW: logging.INFO,
                ErrorSeverity.MEDIUM: logging.WARNING,
                ErrorSeverity.HIGH: logging.ERROR,
                ErrorSeverity.CRITICAL: logging.CRITICAL
            }.get(error.severity, logging.ERROR)

            self.logger.log(log_level, f"[{error.category.value.upper()}] {error.message}")

            # Log to JSON file
            self.log_to_json_file(error)

            # Log to database if available
            self.log_to_database(error)

        except Exception as e:
            print(f"Failed to log error: {e}")

    def log_to_json_file(self, error: AccountingError):
        """Log error to JSON file"""
        try:
            error_log = {
                'timestamp': error.timestamp.isoformat(),
                'message': error.message,
                'category': error.category.value,
                'severity': error.severity.value,
                'error_code': error.error_code,
                'details': error.details,
                'traceback': error.traceback_info
            }

            # Read existing logs
            logs = []
            if os.path.exists(self.log_file):
                try:
                    with open(self.log_file, 'r', encoding='utf-8') as f:
                        logs = json.load(f)
                except (json.JSONDecodeError, IOError):
                    logs = []

            # Add new error
            logs.append(error_log)

            # Keep only last 1000 errors
            if len(logs) > 1000:
                logs = logs[-1000:]

            # Write back to file
            with open(self.log_file, 'w', encoding='utf-8') as f:
                json.dump(logs, f, ensure_ascii=False, indent=2)

        except Exception as e:
            print(f"Failed to log to JSON file: {e}")

    def log_to_database(self, error: AccountingError):
        """Log error to database if available"""
        try:
            # This would log to an error logs table in the database
            # Implementation depends on database manager availability
            pass
        except Exception as e:
            print(f"Failed to log to database: {e}")

    def update_error_stats(self, error: AccountingError):
        """Update error statistics"""
        try:
            error_key = f"{error.category.value}:{error.error_code or 'unknown'}"

            # Update count
            if error_key in self.error_counts:
                self.error_counts[error_key] += 1
            else:
                self.error_counts[error_key] = 1

            # Update last occurrence
            self.last_errors[error_key] = error.timestamp.isoformat()

            # Check for frequent errors
            if self.error_counts[error_key] > 10 and error.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
                self.escalate_error(error)

        except Exception as e:
            print(f"Failed to update error stats: {e}")

    def check_error_patterns(self, error: AccountingError):
        """Check for error patterns that need attention"""
        try:
            # Check for repeated errors
            error_key = f"{error.category.value}:{error.error_code or 'unknown'}"
            if self.error_counts.get(error_key, 0) >= 5:
                self.logger.warning(f"Repeated error detected: {error_key} (count: {self.error_counts[error_key]})")

            # Check for critical errors
            if error.severity == ErrorSeverity.CRITICAL:
                self.escalate_error(error)

            # Check for database errors
            if error.category == ErrorCategory.DATABASE:
                if self.error_counts.get('database:connection', 0) >= 3:
                    self.escalate_error(error)

        except Exception as e:
            print(f"Failed to check error patterns: {e}")

    def escalate_error(self, error: AccountingError):
        """Escalate error for immediate attention"""
        try:
            escalation_message = f"""
            ERROR ESCALATION REQUIRED:

            Type: {error.category.value}
            Severity: {error.severity.value}
            Code: {error.error_code}
            Message: {error.message}
            Count: {self.error_counts.get(f"{error.category.value}:{error.error_code or 'unknown'}", 1)}
            Time: {error.timestamp.isoformat()}
            Details: {error.details}

            Traceback:
            {error.traceback_info}
            """

            self.logger.critical(escalation_message)

            # Could send email, notification, etc.
            self.send_escalation_notification(error)

        except Exception as e:
            print(f"Failed to escalate error: {e}")

    def send_escalation_notification(self, error: AccountingError):
        """Send escalation notification (placeholder)"""
        try:
            # This would send email, SMS, or other notification
            pass
        except Exception as e:
            print(f"Failed to send notification: {e}")

    def register_error_callback(self, category: ErrorCategory, callback: Callable):
        """Register callback for specific error category"""
        try:
            if category not in self.error_callbacks:
                self.error_callbacks[category] = []
            self.error_callbacks[category].append(callback)
        except Exception as e:
            print(f"Failed to register callback: {e}")

    def trigger_error_callbacks(self, error: AccountingError):
        """Trigger callbacks for error category"""
        try:
            callbacks = self.error_callbacks.get(error.category, [])
            for callback in callbacks:
                try:
                    callback(error)
                except Exception as e:
                    print(f"Error in callback: {e}")
        except Exception as e:
            print(f"Failed to trigger callbacks: {e}")

    def get_error_summary(self) -> Dict[str, Any]:
        """Get error summary statistics"""
        try:
            return {
                'total_errors': sum(self.error_counts.values()),
                'error_counts': dict(self.error_counts),
                'last_errors': dict(self.last_errors),
                'categories': list(self.error_counts.keys())
            }
        except Exception as e:
            print(f"Failed to get error summary: {e}")
            return {}

    def clear_error_stats(self):
        """Clear error statistics"""
        try:
            self.error_counts.clear()
            self.last_errors.clear()
        except Exception as e:
            print(f"Failed to clear error stats: {e}")

# Global error handler instance
error_handler = ErrorHandler()

def handle_errors(category: ErrorCategory = ErrorCategory.UNKNOWN,
                severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                reraise: bool = True):
    """Decorator for error handling"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except AccountingError as e:
                error_handler.handle_error(e, {
                    'function': func.__name__,
                    'args': str(args)[:100],  # Limit args size
                    'kwargs': str(kwargs)[:100]  # Limit kwargs size
                })
                if reraise:
                    raise
            except Exception as e:
                accounting_error = AccountingError(
                    str(e),
                    category,
                    severity,
                    details={
                        'function': func.__name__,
                        'args': str(args)[:100],
                        'kwargs': str(kwargs)[:100]
                    }
                )
                error_handler.handle_error(accounting_error)
                if reraise:
                    raise
        return wrapper
    return decorator

def safe_execute(func: Callable, *args, default=None, **kwargs):
    """Safely execute function with error handling"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        error_handler.handle_error(e, {
            'function': func.__name__ if hasattr(func, '__name__') else str(func),
            'args': str(args)[:100],
            'kwargs': str(kwargs)[:100]
        })
        return default

# Global exception handler
def setup_global_exception_handler():
    """Setup global exception handler"""
    def handle_exception(exc_type, exc_value, exc_traceback):
        """Handle uncaught exceptions"""
        if issubclass(exc_type, KeyboardInterrupt):
            # Let KeyboardInterrupt exit normally
            return

        error_info = {
            'type': exc_type.__name__,
            'value': str(exc_value),
            'traceback': ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        }

        accounting_error = AccountingError(
            f"Unhandled exception: {error_info['value']}",
            ErrorCategory.SYSTEM,
            ErrorSeverity.CRITICAL,
            details=error_info
        )

        error_handler.handle_error(accounting_error)

    sys.excepthook = handle_exception

def get_error_statistics() -> Dict[str, Any]:
    """Get current error statistics"""
    return error_handler.get_error_summary()

def create_error_report() -> str:
    """Create comprehensive error report"""
    try:
        stats = error_handler.get_error_summary()

        report = f"""
        Accounting ERP Error Report
        Generated: {datetime.now().isoformat()}

        Summary:
        --------
        Total Errors: {stats.get('total_errors', 0)}
        Error Categories: {len(stats.get('categories', []))}

        Error Breakdown:
        -----------------
        """

        for error_key, count in stats.get('error_counts', {}).items():
            last_occurrence = stats.get('last_errors', {}).get(error_key, 'Unknown')
            report += f"\n  {error_key}: {count} (Last: {last_occurrence})"

        return report

    except Exception as e:
        return f"Failed to generate error report: {e}"