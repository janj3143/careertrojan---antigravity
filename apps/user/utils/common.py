"""
Common utilities for User Portal.
Provides logging, configuration, error handling, and UI helper functions.
"""

import logging
import os
import streamlit as st
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime
import json
import hashlib
from pathlib import Path
from functools import wraps
import time
import traceback

def setup_logging(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    format_string: Optional[str] = None
) -> logging.Logger:
    """
    Set up logging configuration for User Portal.
    
    Args:
        name: Logger name
        level: Logging level
        log_file: Optional log file path
        format_string: Custom format string
        
    Returns:
        Configured logger
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Default format
    if not format_string:
        format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    formatter = logging.Formatter(format_string)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        try:
            # Ensure log directory exists
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
        except Exception as e:
            logger.warning(f"Could not create file handler: {str(e)}")
    
    return logger

def get_env_variable(key: str, default: Any = None, required: bool = False) -> Any:
    """
    Get environment variable with proper error handling.
    
    Args:
        key: Environment variable key
        default: Default value if not found
        required: Whether the variable is required
        
    Returns:
        Environment variable value or default
        
    Raises:
        ValueError: If required variable is missing
    """
    value = os.getenv(key, default)
    
    if required and value is None:
        raise ValueError(f"Required environment variable '{key}' is not set")
    
    return value

def handle_error(
    error: Exception,
    context: str = "",
    show_user: bool = True,
    logger: Optional[logging.Logger] = None
) -> Dict[str, Any]:
    """
    Handle errors with consistent logging and user feedback.
    
    Args:
        error: Exception that occurred
        context: Context information
        show_user: Whether to show error to user via Streamlit
        logger: Logger instance to use
        
    Returns:
        Error information dictionary
    """
    if not logger:
        logger = logging.getLogger("user_portal.error")
    
    error_info = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "context": context,
        "timestamp": datetime.now().isoformat(),
        "traceback": traceback.format_exc()
    }
    
    # Log the error
    logger.error(f"Error in {context}: {str(error)}")
    logger.debug(f"Full traceback: {error_info['traceback']}")
    
    # Show user-friendly message
    if show_user and context:
        st.error(f"An error occurred in {context}. Please try again or contact support.")
    
    return error_info

def validate_streamlit_input(
    value: Any,
    input_type: str,
    required: bool = False,
    min_length: Optional[int] = None,
    max_length: Optional[int] = None
) -> bool:
    """
    Validate Streamlit user input.
    
    Args:
        value: Input value to validate
        input_type: Type of input ('text', 'email', 'number', etc.)
        required: Whether input is required
        min_length: Minimum length for text inputs
        max_length: Maximum length for text inputs
        
    Returns:
        True if valid, False otherwise
    """
    if required and (value is None or value == ""):
        st.error(f"This field is required")
        return False
    
    if value is None or value == "":
        return True  # Optional field, empty is OK
    
    if input_type == "email":
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, str(value)):
            st.error("Please enter a valid email address")
            return False
    
    if input_type == "text" and isinstance(value, str):
        if min_length and len(value) < min_length:
            st.error(f"Text must be at least {min_length} characters long")
            return False
        
        if max_length and len(value) > max_length:
            st.error(f"Text must not exceed {max_length} characters")
            return False
    
    return True

def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    Safely parse JSON string.
    
    Args:
        json_str: JSON string to parse
        default: Default value if parsing fails
        
    Returns:
        Parsed JSON or default value
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default

def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format datetime to string.
    
    Args:
        dt: Datetime object
        format_str: Format string
        
    Returns:
        Formatted datetime string
    """
    return dt.strftime(format_str)

def calculate_file_hash(file_path: str, algorithm: str = "md5") -> str:
    """
    Calculate hash of a file.
    
    Args:
        file_path: Path to file
        algorithm: Hash algorithm ('md5', 'sha1', 'sha256')
        
    Returns:
        File hash as hex string
    """
    hash_obj = hashlib.new(algorithm)
    
    try:
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception as e:
        logging.getLogger("user_portal.utils").error(f"Error calculating file hash: {str(e)}")
        return ""

def performance_monitor(func: Callable) -> Callable:
    """
    Decorator to monitor function performance.
    
    Args:
        func: Function to monitor
        
    Returns:
        Wrapped function with performance monitoring
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        logger = logging.getLogger("user_portal.performance")
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.info(f"{func.__name__} executed in {execution_time:.3f} seconds")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{func.__name__} failed after {execution_time:.3f} seconds: {str(e)}")
            raise
    
    return wrapper

def retry_with_backoff(
    max_retries: int = 3,
    backoff_factor: float = 1.0,
    exceptions: tuple = (Exception,)
) -> Callable:
    """
    Decorator for retry logic with exponential backoff.
    
    Args:
        max_retries: Maximum number of retries
        backoff_factor: Backoff multiplier
        exceptions: Exceptions to catch and retry
        
    Returns:
        Decorator function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger("user_portal.retry")
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries:
                        logger.error(f"{func.__name__} failed after {max_retries} retries")
                        raise
                    
                    wait_time = backoff_factor * (2 ** attempt)
                    logger.warning(f"{func.__name__} attempt {attempt + 1} failed, retrying in {wait_time}s")
                    time.sleep(wait_time)
            
            return None
        return wrapper
    return decorator

# Streamlit-specific utilities
def init_session_state(key: str, default_value: Any) -> Any:
    """
    Initialize session state variable if it doesn't exist.
    
    Args:
        key: Session state key
        default_value: Default value to set
        
    Returns:
        Current value of session state variable
    """
    if key not in st.session_state:
        st.session_state[key] = default_value
    return st.session_state[key]

def clear_session_state(keys: Optional[List[str]] = None) -> None:
    """
    Clear session state variables.
    
    Args:
        keys: Specific keys to clear, or None to clear all
    """
    if keys is None:
        st.session_state.clear()
    else:
        for key in keys:
            if key in st.session_state:
                del st.session_state[key]

def show_success_message(message: str, duration: int = 3) -> None:
    """
    Show success message with auto-dismiss.
    
    Args:
        message: Success message
        duration: Duration in seconds before auto-dismiss
    """
    success_placeholder = st.empty()
    success_placeholder.success(message)
    
    # Auto-dismiss after duration
    time.sleep(duration)
    success_placeholder.empty()

def show_loading_spinner(message: str = "Loading..."):
    """
    Context manager for showing loading spinner.
    
    Args:
        message: Loading message
        
    Returns:
        Streamlit spinner context manager
    """
    return st.spinner(message)

def validate_file_upload(
    uploaded_file,
    allowed_types: List[str],
    max_size_mb: float = 10.0
) -> bool:
    """
    Validate uploaded file.
    
    Args:
        uploaded_file: Streamlit uploaded file object
        allowed_types: List of allowed file extensions
        max_size_mb: Maximum file size in MB
        
    Returns:
        True if valid, False otherwise
    """
    if uploaded_file is None:
        return False
    
    # Check file extension
    file_extension = uploaded_file.name.split('.')[-1].lower()
    if file_extension not in allowed_types:
        st.error(f"File type '.{file_extension}' not allowed. Allowed types: {', '.join(allowed_types)}")
        return False
    
    # Check file size
    file_size_mb = uploaded_file.size / (1024 * 1024)
    if file_size_mb > max_size_mb:
        st.error(f"File size ({file_size_mb:.1f}MB) exceeds maximum allowed size ({max_size_mb}MB)")
        return False
    
    return True

def create_download_link(data: Any, filename: str, mime_type: str = "application/octet-stream") -> None:
    """
    Create download link for data.
    
    Args:
        data: Data to download (string, bytes, or JSON-serializable object)
        filename: Filename for download
        mime_type: MIME type for the file
    """
    if isinstance(data, (dict, list)):
        data = json.dumps(data, indent=2)
    
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    st.download_button(
        label=f"📥 Download {filename}",
        data=data,
        file_name=filename,
        mime=mime_type
    )