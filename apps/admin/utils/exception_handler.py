"""
Comprehensive Exception Handling System for IntelliCV Admin Portal
Provides structured exception management with proper error recovery and user feedback
"""

import traceback
import sys
from typing import Optional, Dict, Any, Callable, Type, Union
from functools import wraps
from datetime import datetime
from pathlib import Path
import streamlit as st

from utils.logging_config import LoggingMixin, admin_logger


# =====================================================================
# CUSTOM EXCEPTION CLASSES
# =====================================================================

class AdminPortalException(Exception):
    """Base exception for admin portal operations"""
    
    def __init__(self, message: str, error_code: Optional[str] = None, 
                 details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.now()
        super().__init__(message)


class AuthenticationError(AdminPortalException):
    """Authentication and authorization related errors"""
    pass


class DataProcessingError(AdminPortalException):
    """Data processing and file handling errors"""
    pass


class ConfigurationError(AdminPortalException):
    """Configuration and setup related errors"""
    pass


class ValidationError(AdminPortalException):
    """Input validation and data integrity errors"""
    pass


class ResourceError(AdminPortalException):
    """Resource availability and access errors"""
    pass


class NetworkError(AdminPortalException):
    """Network and external service errors"""
    pass


class DatabaseError(AdminPortalException):
    """Database connection and query errors"""
    pass


# =====================================================================
# ERROR RECOVERY STRATEGIES
# =====================================================================

class ErrorRecoveryStrategy:
    """Base class for error recovery strategies"""
    
    def can_recover(self, exception: Exception) -> bool:
        """Check if this strategy can recover from the exception"""
        return False
    
    def recover(self, exception: Exception, context: Dict[str, Any]) -> Any:
        """Attempt recovery from the exception"""
        raise NotImplementedError


class FileSystemRecoveryStrategy(ErrorRecoveryStrategy):
    """Recovery strategy for file system related errors"""
    
    def can_recover(self, exception: Exception) -> bool:
        return isinstance(exception, (FileNotFoundError, PermissionError, OSError))
    
    def recover(self, exception: Exception, context: Dict[str, Any]) -> Any:
        """Attempt to recover from file system errors"""
        if isinstance(exception, FileNotFoundError):
            # Try to create missing directories
            if 'file_path' in context:
                file_path = Path(context['file_path'])
                if not file_path.parent.exists():
                    file_path.parent.mkdir(parents=True, exist_ok=True)
                    admin_logger.info("Created missing directory", 
                                    directory=str(file_path.parent))
                    return True
        
        elif isinstance(exception, PermissionError):
            # Log permission error and suggest alternative
            admin_logger.error("Permission denied - check file/directory permissions",
                             path=context.get('file_path'))
            return False
        
        return False


class NetworkRecoveryStrategy(ErrorRecoveryStrategy):
    """Recovery strategy for network related errors"""
    
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
    
    def can_recover(self, exception: Exception) -> bool:
        import requests
        return isinstance(exception, (requests.RequestException, ConnectionError, TimeoutError))
    
    def recover(self, exception: Exception, context: Dict[str, Any]) -> Any:
        """Attempt to recover from network errors with retry logic"""
        retry_count = context.get('retry_count', 0)
        
        if retry_count < self.max_retries:
            import time
            time.sleep(self.retry_delay * (retry_count + 1))
            admin_logger.warning("Retrying network operation", 
                               attempt=retry_count + 1, 
                               max_attempts=self.max_retries)
            return {'retry': True, 'retry_count': retry_count + 1}
        
        return False


class DatabaseRecoveryStrategy(ErrorRecoveryStrategy):
    """Recovery strategy for database related errors"""
    
    def can_recover(self, exception: Exception) -> bool:
        import sqlite3
        return isinstance(exception, (sqlite3.Error, DatabaseError))
    
    def recover(self, exception: Exception, context: Dict[str, Any]) -> Any:
        """Attempt to recover from database errors"""
        if "database is locked" in str(exception).lower():
            # Try to wait and retry for locked database
            import time
            time.sleep(0.5)
            admin_logger.warning("Database locked - retrying after delay")
            return {'retry': True}
        
        elif "no such table" in str(exception).lower():
            # Try to recreate missing tables
            admin_logger.error("Missing database table detected", 
                             error=str(exception))
            return {'recreate_schema': True}
        
        return False


# =====================================================================
# EXCEPTION HANDLER CLASS
# =====================================================================

class ExceptionHandler(LoggingMixin):
    """Centralized exception handling with recovery strategies"""
    
    def __init__(self):
        super().__init__()
        self.recovery_strategies = [
            FileSystemRecoveryStrategy(),
            NetworkRecoveryStrategy(),
            DatabaseRecoveryStrategy()
        ]
        self.error_counts = {}
        self.last_errors = {}
    
    def handle_exception(self, exception: Exception, 
                        context: Optional[Dict[str, Any]] = None,
                        show_user_message: bool = True,
                        attempt_recovery: bool = True) -> Dict[str, Any]:
        """
        Handle exception with logging, user feedback, and recovery attempts
        
        Returns:
            Dict with keys: recovered, retry, user_message, error_code
        """
        context = context or {}
        error_type = type(exception).__name__
        
        # Update error tracking
        self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1
        self.last_errors[error_type] = {
            'exception': exception,
            'timestamp': datetime.now(),
            'context': context
        }
        
        # Log the exception
        self.log_error(
            f"Exception occurred: {error_type}",
            exc_info=True,
            error_type=error_type,
            error_message=str(exception),
            context=context,
            stack_trace=traceback.format_exc()
        )
        
        result = {
            'recovered': False,
            'retry': False,
            'user_message': self._get_user_friendly_message(exception),
            'error_code': getattr(exception, 'error_code', error_type)
        }
        
        # Attempt recovery if enabled
        if attempt_recovery:
            recovery_result = self._attempt_recovery(exception, context)
            if recovery_result:
                if isinstance(recovery_result, dict):
                    result.update(recovery_result)
                else:
                    result['recovered'] = bool(recovery_result)
        
        # Show user message if requested
        if show_user_message and not result['recovered']:
            self._show_user_error_message(exception, result['user_message'])
        
        return result
    
    def _attempt_recovery(self, exception: Exception, 
                         context: Dict[str, Any]) -> Union[bool, Dict[str, Any]]:
        """Attempt recovery using available strategies"""
        for strategy in self.recovery_strategies:
            if strategy.can_recover(exception):
                try:
                    recovery_result = strategy.recover(exception, context)
                    if recovery_result:
                        self.log_info("Recovery attempt successful", 
                                    strategy=strategy.__class__.__name__,
                                    exception_type=type(exception).__name__)
                        return recovery_result
                except Exception as recovery_exception:
                    self.log_error("Recovery strategy failed", 
                                 strategy=strategy.__class__.__name__,
                                 recovery_error=str(recovery_exception),
                                 exc_info=True)
        
        return False
    
    def _get_user_friendly_message(self, exception: Exception) -> str:
        """Generate user-friendly error message"""
        if isinstance(exception, AuthenticationError):
            return "🔒 Authentication required. Please log in to continue."
        
        elif isinstance(exception, ValidationError):
            return f"❌ Input validation failed: {exception.message}"
        
        elif isinstance(exception, DataProcessingError):
            return "📊 There was an issue processing your data. Please try again or contact support."
        
        elif isinstance(exception, ResourceError):
            return "🚫 Required resource is currently unavailable. Please try again later."
        
        elif isinstance(exception, NetworkError):
            return "🌐 Network connection issue. Please check your internet connection."
        
        elif isinstance(exception, DatabaseError):
            return "🗄️ Database temporarily unavailable. Please try again in a moment."
        
        elif isinstance(exception, FileNotFoundError):
            return "📁 Required file not found. Please check your file paths."
        
        elif isinstance(exception, PermissionError):
            return "🚫 Permission denied. Please check file/folder permissions."
        
        else:
            return f"⚠️ An unexpected error occurred. Error type: {type(exception).__name__}"
    
    def _show_user_error_message(self, exception: Exception, message: str) -> None:
        """Display error message to user in Streamlit"""
        if isinstance(exception, (AuthenticationError, ValidationError)):
            st.error(message)
        elif isinstance(exception, (ResourceError, NetworkError)):
            st.warning(message)
        elif isinstance(exception, ConfigurationError):
            st.info(f"ℹ️ Configuration issue: {message}")
        else:
            st.error(message)
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get error statistics for monitoring"""
        return {
            'error_counts': self.error_counts.copy(),
            'total_errors': sum(self.error_counts.values()),
            'unique_error_types': len(self.error_counts),
            'last_errors': {
                error_type: {
                    'message': str(error_info['exception']),
                    'timestamp': error_info['timestamp'].isoformat()
                }
                for error_type, error_info in self.last_errors.items()
            }
        }


# =====================================================================
# DECORATORS FOR EXCEPTION HANDLING
# =====================================================================

def handle_exceptions(exception_handler: Optional[ExceptionHandler] = None,
                     show_user_message: bool = True,
                     attempt_recovery: bool = True,
                     reraise_on_failure: bool = False):
    """
    Decorator for automatic exception handling
    
    Args:
        exception_handler: Custom exception handler instance
        show_user_message: Whether to show error message to user
        attempt_recovery: Whether to attempt automatic recovery
        reraise_on_failure: Whether to reraise exception if recovery fails
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            handler = exception_handler or _get_global_exception_handler()
            
            try:
                return func(*args, **kwargs)
            except Exception as e:
                context = {
                    'function': func.__name__,
                    'module': func.__module__,
                    'args_count': len(args),
                    'kwargs_keys': list(kwargs.keys())
                }
                
                result = handler.handle_exception(
                    e, context, show_user_message, attempt_recovery
                )
                
                if result['recovered'] or result['retry']:
                    # If recovery successful or retry requested, try again
                    if result['retry']:
                        # Add retry context
                        context.update(result)
                        return func(*args, **kwargs)
                    else:
                        return None  # Recovered successfully
                
                elif reraise_on_failure:
                    raise
                
                return None
        
        return wrapper
    return decorator


def safe_execute(func: Callable, *args, 
                default_return: Any = None, 
                context: Optional[Dict[str, Any]] = None,
                **kwargs) -> Any:
    """
    Safely execute a function with exception handling
    
    Args:
        func: Function to execute
        *args: Function arguments
        default_return: Value to return on failure
        context: Additional context for error handling
        **kwargs: Function keyword arguments
    
    Returns:
        Function result or default_return on failure
    """
    handler = _get_global_exception_handler()
    
    try:
        return func(*args, **kwargs)
    except Exception as e:
        execution_context = {
            'function': func.__name__ if hasattr(func, '__name__') else str(func),
            'args_count': len(args),
            'kwargs_keys': list(kwargs.keys())
        }
        
        if context:
            execution_context.update(context)
        
        result = handler.handle_exception(e, execution_context)
        
        if result['recovered']:
            try:
                return func(*args, **kwargs)
            except:
                pass  # Return default if retry also fails
        
        return default_return


# =====================================================================
# STREAMLIT INTEGRATION
# =====================================================================

def create_error_display_component():
    """Create Streamlit component for displaying error information"""
    
    handler = _get_global_exception_handler()
    stats = handler.get_error_statistics()
    
    if stats['total_errors'] > 0:
        with st.expander("🚨 Error Summary", expanded=False):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Errors", stats['total_errors'])
            
            with col2:
                st.metric("Error Types", stats['unique_error_types'])
            
            with col3:
                most_common = max(stats['error_counts'].items(), 
                                key=lambda x: x[1]) if stats['error_counts'] else ('None', 0)
                st.metric("Most Common", f"{most_common[0]} ({most_common[1]})")
            
            if stats['last_errors']:
                st.subheader("Recent Errors")
                for error_type, error_info in stats['last_errors'].items():
                    st.text(f"• {error_type}: {error_info['message'][:100]}...")


def setup_global_error_handler():
    """Set up global error handler in Streamlit session state"""
    if 'exception_handler' not in st.session_state:
        st.session_state.exception_handler = ExceptionHandler()


# =====================================================================
# GLOBAL INSTANCE MANAGEMENT
# =====================================================================

_global_exception_handler = None

def _get_global_exception_handler() -> ExceptionHandler:
    """Get or create global exception handler instance"""
    global _global_exception_handler
    
    if _global_exception_handler is None:
        _global_exception_handler = ExceptionHandler()
    
    return _global_exception_handler


def set_global_exception_handler(handler: ExceptionHandler) -> None:
    """Set custom global exception handler"""
    global _global_exception_handler
    _global_exception_handler = handler


# Initialize global handler
setup_global_error_handler()

class SafeOperationsMixin:
    '''Mixin class to add safe operations capabilities to any class'''
    
    def safe_read_file(self, file_path, default=''):
        '''Safely read a file with error handling'''
        try:
            from pathlib import Path
            if isinstance(file_path, str):
                file_path = Path(file_path)
            if not file_path.exists():
                return default
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f'Error reading file {file_path}: {e}')
            return default
    
    def safe_create_directory(self, dir_path):
        '''Safely create a directory with error handling'''
        try:
            from pathlib import Path
            if isinstance(dir_path, str):
                dir_path = Path(dir_path)
            dir_path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            if hasattr(self, 'logger'):
                self.logger.error(f'Error creating directory {dir_path}: {e}')
            return False
