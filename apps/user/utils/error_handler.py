#!/usr/bin/env python3
"""
🛠️ Error Handler Utilities for IntelliCV-AI
Provides error handling, logging, and user notification functions
"""

import streamlit as st
import logging
import traceback
from datetime import datetime
from functools import wraps
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def handle_exceptions(func):
    """Decorator to handle exceptions gracefully"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            show_error(f"An error occurred in {func.__name__}: {str(e)}")
            return None
    return wrapper

def log_user_action(action: str, user_id: str = None, details: dict = None):
    """Log user actions for analytics and debugging"""
    try:
        user = user_id or st.session_state.get('user_id', 'anonymous')
        timestamp = datetime.now().isoformat()

        log_entry = {
            'timestamp': timestamp,
            'user_id': user,
            'action': action,
            'details': details or {}
        }

        logger.info(f"USER_ACTION: {log_entry}")

        # Store in session state for analytics
        if 'user_actions' not in st.session_state:
            st.session_state.user_actions = []

        st.session_state.user_actions.append(log_entry)

    except Exception as e:
        logger.error(f"Failed to log user action: {e}")

def show_error(message: str, details: str = None):
    """Display error message to user"""
    st.error(f"❌ {message}")

    if details:
        with st.expander("Show Details"):
            st.code(details)

    # Log the error
    logger.error(f"USER_ERROR: {message} | Details: {details}")

def show_success(message: str, details: str = None):
    """Display success message to user"""
    st.success(f"✅ {message}")

    if details:
        st.info(details)

    # Log the success
    logger.info(f"USER_SUCCESS: {message} | Details: {details}")

def show_warning(message: str, details: str = None):
    """Display warning message to user"""
    st.warning(f"⚠️ {message}")

    if details:
        with st.expander("Show Details"):
            st.info(details)

    # Log the warning
    logger.warning(f"USER_WARNING: {message} | Details: {details}")

def show_info(message: str, details: str = None):
    """Display info message to user"""
    st.info(f"ℹ️ {message}")

    if details:
        with st.expander("Show Details"):
            st.write(details)

def safe_execute(func, *args, default_return=None, error_message="Operation failed", **kwargs):
    """Safely execute a function with error handling"""
    try:
        return func(*args, **kwargs)
    except Exception as e:
        logger.error(f"Safe execute failed: {str(e)}")
        show_error(error_message, str(e))
        return default_return

def validate_input(value, validation_type: str, field_name: str = "Field"):
    """Validate user input with helpful error messages"""
    try:
        if validation_type == "email":
            import re
            email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            if not re.match(email_pattern, value):
                show_error(f"{field_name} must be a valid email address")
                return False

        elif validation_type == "phone":
            import re
            phone_pattern = r'^[\+]?[1-9][\d]{0,15}$'
            clean_phone = value.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
            if not re.match(phone_pattern, clean_phone):
                show_error(f"{field_name} must be a valid phone number")
                return False

        elif validation_type == "required":
            if not value or str(value).strip() == "":
                show_error(f"{field_name} is required")
                return False

        elif validation_type == "password":
            if len(value) < 8:
                show_error(f"{field_name} must be at least 8 characters long")
                return False

        return True

    except Exception as e:
        logger.error(f"Validation error: {e}")
        show_error(f"Validation failed for {field_name}")
        return False

def get_error_stats():
    """Get error statistics for admin dashboard"""
    try:
        # No mock/demo data. Use real session-tracked error events when present.
        events = st.session_state.get('error_events', [])
        if not isinstance(events, list):
            events = []

        total_errors = len(events)
        today = datetime.now().date()
        errors_today = 0
        error_types = []

        for ev in events:
            if not isinstance(ev, dict):
                continue
            ts = ev.get('timestamp')
            try:
                if isinstance(ts, str):
                    ev_dt = datetime.fromisoformat(ts)
                elif isinstance(ts, datetime):
                    ev_dt = ts
                else:
                    ev_dt = None
            except Exception:
                ev_dt = None

            if ev_dt and ev_dt.date() == today:
                errors_today += 1
            et = ev.get('type') or ev.get('error_type')
            if isinstance(et, str) and et.strip():
                error_types.append(et.strip())

        most_common_error = 'None'
        if error_types:
            most_common_error = max(set(error_types), key=error_types.count)

        return {
            'total_errors': total_errors,
            'errors_today': errors_today,
            'most_common_error': most_common_error,
            'error_rate': 0.0,
            'source': 'session'
        }
    except Exception as e:
        logger.error(f"Failed to get error stats: {e}")
        return {}

def clear_error_logs():
    """Clear error logs (admin function)"""
    try:
        if 'user_actions' in st.session_state:
            st.session_state.user_actions = []
        show_success("Error logs cleared successfully")
        logger.info("Error logs cleared by admin")
    except Exception as e:
        logger.error(f"Failed to clear error logs: {e}")
        show_error("Failed to clear error logs")

# Context manager for error handling
class ErrorContext:
    """Context manager for handling errors in code blocks"""

    def __init__(self, operation_name: str, show_errors: bool = True):
        self.operation_name = operation_name
        self.show_errors = show_errors

    def __enter__(self):
        logger.info(f"Starting operation: {self.operation_name}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            error_msg = f"Error in {self.operation_name}: {str(exc_val)}"
            logger.error(error_msg)
            logger.error(f"Traceback: {traceback.format_exc()}")

            if self.show_errors:
                show_error(error_msg)

            return True  # Suppress the exception
        else:
            logger.info(f"Completed operation: {self.operation_name}")

        return False

# Utility functions for common operations
def safe_file_operation(file_path: str, operation: str, content: str = None):
    """Safely perform file operations"""
    try:
        path = Path(file_path)

        if operation == "read":
            if path.exists():
                return path.read_text(encoding='utf-8')
            else:
                show_warning(f"File not found: {file_path}")
                return None

        elif operation == "write":
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content or "", encoding='utf-8')
            return True

        elif operation == "delete":
            if path.exists():
                path.unlink()
                return True
            else:
                show_warning(f"File not found: {file_path}")
                return False

    except Exception as e:
        logger.error(f"File operation failed: {e}")
        show_error(f"File operation '{operation}' failed", str(e))
        return None

# Export main functions
__all__ = [
    'handle_exceptions',
    'log_user_action',
    'show_error',
    'show_success',
    'show_warning',
    'show_info',
    'safe_execute',
    'validate_input',
    'get_error_stats',
    'clear_error_logs',
    'ErrorContext',
    'safe_file_operation'
]
