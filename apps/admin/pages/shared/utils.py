"""
Shared Utilities for IntelliCV Admin Portal
==========================================

Common utility functions used across admin modules.
"""

import streamlit as st
import pandas as pd
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

# Configure logging
logger = logging.getLogger(__name__)

def get_session_state(key: str, default: Any = None) -> Any:
    """Get session state - alias for compatibility"""
    return get_admin_session_state(key, default)

def set_session_state(key: str, value: Any) -> None:
    """Set session state - alias for compatibility"""
    return set_admin_session_state(key, value)

def get_admin_session_state(key: str, default: Any = None) -> Any:
    """Get admin session state with consistent key naming"""
    admin_key = f"admin_{key}"
    if admin_key not in st.session_state:
        st.session_state[admin_key] = default
    return st.session_state[admin_key]

def set_admin_session_state(key: str, value: Any) -> None:
    """Set admin session state with consistent key naming"""
    admin_key = f"admin_{key}"
    st.session_state[admin_key] = value

def log_admin_action(action: str, user: str = "admin", details: str = "") -> None:
    """Log admin actions for audit trail"""
    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] {user}: {action}"
    if details:
        log_entry += f" - {details}"
    
    logger.info(log_entry)
    
    # Store in session state for recent activity
    recent_actions = get_admin_session_state("recent_actions", [])
    recent_actions.insert(0, {
        "timestamp": timestamp,
        "user": user,
        "action": action,
        "details": details
    })
    
    # Keep only last 50 actions
    if len(recent_actions) > 50:
        recent_actions = recent_actions[:50]
    
    set_admin_session_state("recent_actions", recent_actions)

def format_datetime(dt: datetime, format_type: str = "default") -> str:
    """Format datetime with consistent formatting across modules"""
    formats = {
        "default": "%Y-%m-%d %H:%M:%S",
        "date_only": "%Y-%m-%d",
        "time_only": "%H:%M:%S",
        "friendly": "%B %d, %Y at %I:%M %p",
        "relative": "relative"  # Special case handled below
    }
    
    if format_type == "relative":
        now = datetime.now()
        diff = now - dt
        
        if diff.days > 0:
            return f"{diff.days} days ago"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            return f"{hours} hours ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            return f"{minutes} minutes ago"
        else:
            return "Just now"
    
    format_str = formats.get(format_type, formats["default"])
    return dt.strftime(format_str)

def generate_sample_data(data_type: str, count: int = 10) -> List[Dict[str, Any]]:
    """Generate sample data for testing and demonstration"""
    
    if data_type == "users":
        return [
            {
                "id": i + 1,
                "name": f"User {i + 1}",
                "email": f"user{i + 1}@company.com",
                "status": random.choice(["Active", "Inactive", "Pending"]),
                "last_login": datetime.now() - timedelta(days=random.randint(0, 30)),
                "role": random.choice(["Admin", "User", "Manager"])
            }
            for i in range(count)
        ]
    
    elif data_type == "jobs":
        return [
            {
                "id": i + 1,
                "name": f"Job {i + 1}",
                "status": random.choice(["Running", "Completed", "Failed", "Queued"]),
                "progress": random.randint(0, 100),
                "started": datetime.now() - timedelta(hours=random.randint(1, 24)),
                "type": random.choice(["Processing", "Analysis", "Export", "Import"])
            }
            for i in range(count)
        ]
    
    elif data_type == "metrics":
        return [
            {
                "date": datetime.now() - timedelta(days=i),
                "users": 100 + random.randint(-20, 50),
                "processes": 50 + random.randint(-10, 30),
                "errors": random.randint(0, 10),
                "success_rate": 90 + random.uniform(-10, 10)
            }
            for i in range(count)
        ]
    
    elif data_type == "activities":
        activities = [
            "User login", "Data processed", "Report generated", "System backup",
            "Cache cleared", "Configuration updated", "User created", "Job completed"
        ]
        return [
            {
                "id": i + 1,
                "activity": random.choice(activities),
                "user": f"user{random.randint(1, 10)}@company.com",
                "timestamp": datetime.now() - timedelta(minutes=random.randint(1, 1440)),
                "status": random.choice(["Success", "Warning", "Error"])
            }
            for i in range(count)
        ]
    
    else:
        return []

def create_sample_dataframe(data_type: str, count: int = 30) -> pd.DataFrame:
    """Create sample pandas DataFrame for charts and analytics"""
    
    if data_type == "time_series":
        dates = pd.date_range(start=datetime.now() - timedelta(days=count), 
                             end=datetime.now(), freq='D')
        return pd.DataFrame({
            'Date': dates,
            'Value': [100 + i + random.randint(-20, 20) for i in range(len(dates))],
            'Secondary': [50 + i*0.5 + random.randint(-10, 10) for i in range(len(dates))]
        })
    
    elif data_type == "categories":
        categories = ["Category A", "Category B", "Category C", "Category D", "Category E"]
        return pd.DataFrame({
            'Category': categories,
            'Count': [random.randint(10, 100) for _ in categories],
            'Percentage': [random.uniform(10, 30) for _ in categories]
        })
    
    elif data_type == "performance":
        hours = [f"{i:02d}:00" for i in range(24)]
        return pd.DataFrame({
            'Hour': hours,
            'CPU': [random.uniform(10, 80) for _ in hours],
            'Memory': [random.uniform(30, 90) for _ in hours],
            'Network': [random.uniform(5, 50) for _ in hours]
        })
    
    return pd.DataFrame()

def validate_admin_permissions(required_role: str = "admin") -> bool:
    """Validate admin permissions for sensitive operations"""
    current_role = get_admin_session_state("user_role", "guest")
    
    role_hierarchy = {
        "guest": 0,
        "user": 1, 
        "manager": 2,
        "admin": 3,
        "superadmin": 4
    }
    
    required_level = role_hierarchy.get(required_role, 3)
    current_level = role_hierarchy.get(current_role, 0)
    
    return current_level >= required_level

def sanitize_input(input_text: str, max_length: int = 1000) -> str:
    """Sanitize user input for security"""
    if not input_text:
        return ""
    
    # Basic sanitization
    sanitized = str(input_text).strip()
    
    # Limit length
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized

def format_file_size(size_bytes: int) -> str:
    """Format file size in human readable format"""
    if size_bytes == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    i = int(math.floor(math.log(size_bytes, 1024)))
    p = math.pow(1024, i)
    s = round(size_bytes / p, 2)
    return f"{s} {size_names[i]}"

def get_system_status() -> Dict[str, Any]:
    """Get mock system status for demonstration"""
    return {
        "database": {"status": "operational", "connections": 45, "queries_per_sec": 127},
        "api": {"status": "operational", "requests_per_min": 234, "avg_response": "245ms"},
        "ai_services": {"status": "operational", "models_loaded": 3, "queue_size": 12},
        "storage": {"status": "warning", "used_percentage": 78, "available_gb": 2100},
        "memory": {"status": "operational", "used_percentage": 67, "available_gb": 16},
        "cpu": {"status": "operational", "usage_percentage": 23, "cores_active": 8}
    }

def export_data_to_csv(data: List[Dict[str, Any]], filename: str) -> bytes:
    """Export data to CSV format for download"""
    if not data:
        return b""
    
    df = pd.DataFrame(data)
    return df.to_csv(index=False).encode('utf-8')

def calculate_trend(values: List[float]) -> str:
    """Calculate trend direction from a list of values"""
    if len(values) < 2:
        return "stable"
    
    start_avg = sum(values[:len(values)//3]) / (len(values)//3)
    end_avg = sum(values[-len(values)//3:]) / (len(values)//3)
    
    change_percent = ((end_avg - start_avg) / start_avg) * 100 if start_avg != 0 else 0
    
    if change_percent > 5:
        return "increasing"
    elif change_percent < -5:
        return "decreasing"
    else:
        return "stable"