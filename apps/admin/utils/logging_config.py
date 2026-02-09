"""
Centralized logging configuration for IntelliCV Admin Portal
Provides structured logging with proper formatting, handlers, and context
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import json


class AdminPortalFormatter(logging.Formatter):
    """Custom formatter for structured logging with JSON output"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno
        }
        
        # Add extra context if available
        if hasattr(record, 'user_id'):
            log_data['user_id'] = record.user_id
        if hasattr(record, 'session_id'):
            log_data['session_id'] = record.session_id
        if hasattr(record, 'request_id'):
            log_data['request_id'] = record.request_id
        if hasattr(record, 'component'):
            log_data['component'] = record.component
            
        return json.dumps(log_data, default=str)


class AdminPortalLogger:
    """Centralized logger for the Admin Portal"""
    
    def __init__(self, name: str, log_dir: Optional[Path] = None):
        self.name = name
        self.log_dir = log_dir or Path("logs")
        self.logger = logging.getLogger(name)
        self._setup_logger()
    
    def _setup_logger(self) -> None:
        """Configure logger with appropriate handlers and formatting"""
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # Set log level
        self.logger.setLevel(logging.INFO)
        
        # Create log directory if it doesn't exist
        self.log_dir.mkdir(exist_ok=True)
        
        # Console handler with structured format
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = AdminPortalFormatter()
        console_handler.setFormatter(console_formatter)
        
        # File handler for persistent logging
        log_file = self.log_dir / f"{self.name}_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(console_formatter)
        
        # Error file handler for errors only
        error_file = self.log_dir / f"{self.name}_errors_{datetime.now().strftime('%Y%m%d')}.log"
        error_handler = logging.FileHandler(error_file)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(console_formatter)
        
        # Add handlers to logger
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
        self.logger.addHandler(error_handler)
        
        # Prevent propagation to root logger
        self.logger.propagate = False
    
    def info(self, message: str, **context) -> None:
        """Log info message with optional context"""
        self._log_with_context(logging.INFO, message, **context)
    
    def warning(self, message: str, **context) -> None:
        """Log warning message with optional context"""
        self._log_with_context(logging.WARNING, message, **context)
    
    def error(self, message: str, exc_info: bool = False, **context) -> None:
        """Log error message with optional context and exception info"""
        self._log_with_context(logging.ERROR, message, exc_info=exc_info, **context)
    
    def debug(self, message: str, **context) -> None:
        """Log debug message with optional context"""
        self._log_with_context(logging.DEBUG, message, **context)
    
    def critical(self, message: str, exc_info: bool = True, **context) -> None:
        """Log critical message with optional context and exception info"""
        self._log_with_context(logging.CRITICAL, message, exc_info=exc_info, **context)
    
    def _log_with_context(self, level: int, message: str, exc_info: bool = False, **context) -> None:
        """Internal method to log with context"""
        # Create a LogRecord with extra context
        record = self.logger.makeRecord(
            name=self.logger.name,
            level=level,
            fn="",
            lno=0,
            msg=message,
            args=(),
            exc_info=exc_info if exc_info else None
        )
        
        # Add context attributes to the record
        for key, value in context.items():
            setattr(record, key, value)
        
        self.logger.handle(record)


# Global logger instances
admin_logger = AdminPortalLogger("admin_portal")
auth_logger = AdminPortalLogger("authentication") 
data_logger = AdminPortalLogger("data_processing")
api_logger = AdminPortalLogger("api")


def setup_logging(log_level: str = "INFO", log_dir: Optional[Path] = None) -> None:
    """
    Initialize logging configuration for the entire application
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Optional custom log directory
    """
    # Set root logger level
    logging.root.setLevel(getattr(logging, log_level.upper()))
    
    # Create logs directory if it doesn't exist
    logs_dir = log_dir or Path("logs")
    logs_dir.mkdir(parents=True, exist_ok=True)


def get_logger(component: str) -> AdminPortalLogger:
    """Get a logger instance for a specific component"""
    return AdminPortalLogger(f"admin_portal.{component}")


class LoggingMixin:
    """Mixin class to add logging capabilities to any class"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._logger = get_logger(self.__class__.__name__.lower())
    
    def log_info(self, message: str, **context) -> None:
        """Log info message"""
        self._logger.info(message, component=self.__class__.__name__, **context)
    
    def log_warning(self, message: str, **context) -> None:
        """Log warning message"""
        self._logger.warning(message, component=self.__class__.__name__, **context)
    
    def log_error(self, message: str, exc_info: bool = False, **context) -> None:
        """Log error message"""
        self._logger.error(message, exc_info=exc_info, component=self.__class__.__name__, **context)
    
    def log_debug(self, message: str, **context) -> None:
        """Log debug message"""
        self._logger.debug(message, component=self.__class__.__name__, **context)


def log_function_call(func):
    """Decorator to log function calls with parameters and execution time"""
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        start_time = datetime.now()
        
        logger.debug(
            f"Calling function {func.__name__}",
            function=func.__name__,
            module=func.__module__,
            args_count=len(args),
            kwargs_keys=list(kwargs.keys())
        )
        
        try:
            result = func(*args, **kwargs)
            execution_time = (datetime.now() - start_time).total_seconds()
            
            logger.debug(
                f"Function {func.__name__} completed successfully",
                function=func.__name__,
                execution_time_seconds=execution_time
            )
            
            return result
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds()
            
            logger.error(
                f"Function {func.__name__} failed with error: {str(e)}",
                function=func.__name__,
                execution_time_seconds=execution_time,
                error_type=type(e).__name__,
                exc_info=True
            )
            raise
    
    return wrapper


# Request context for web applications
class RequestContext:
    """Context manager for request-specific logging"""
    
    def __init__(self, request_id: str, user_id: Optional[str] = None, session_id: Optional[str] = None):
        self.request_id = request_id
        self.user_id = user_id
        self.session_id = session_id
        self.start_time = datetime.now()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        execution_time = (datetime.now() - self.start_time).total_seconds()
        
        if exc_type is None:
            admin_logger.info(
                "Request completed successfully",
                request_id=self.request_id,
                user_id=self.user_id,
                session_id=self.session_id,
                execution_time_seconds=execution_time
            )
        else:
            admin_logger.error(
                f"Request failed with {exc_type.__name__}: {exc_val}",
                request_id=self.request_id,
                user_id=self.user_id,
                session_id=self.session_id,
                execution_time_seconds=execution_time,
                error_type=exc_type.__name__,
                exc_info=True
            )
    
    def log(self, level: str, message: str, **context) -> None:
        """Log a message within the request context"""
        context.update({
            'request_id': self.request_id,
            'user_id': self.user_id,
            'session_id': self.session_id
        })
        
        if level.lower() == 'info':
            admin_logger.info(message, **context)
        elif level.lower() == 'warning':
            admin_logger.warning(message, **context)
        elif level.lower() == 'error':
            admin_logger.error(message, **context)
        elif level.lower() == 'debug':
            admin_logger.debug(message, **context)