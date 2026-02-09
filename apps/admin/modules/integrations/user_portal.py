
# Enhanced Sidebar Integration
import sys
from pathlib import Path
shared_path = Path(__file__).parent.parent / "shared"
if str(shared_path) not in sys.path:
    sys.path.insert(0, str(shared_path))

try:
    from enhanced_sidebar import render_enhanced_sidebar, inject_sidebar_css
    ENHANCED_SIDEBAR_AVAILABLE = True
except ImportError:
    ENHANCED_SIDEBAR_AVAILABLE = False

"""
User Portal Integration Module
=============================

This module handles all integration with the User Portal Final,
including data synchronization, user preferences, and activity tracking.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List

import streamlit as st


class UserPortalIntegration:
    """Integration hooks for User Portal Final synchronization."""
    
    def __init__(self):
        """Initialize user portal integration."""
        self.sync_enabled = True
        self.last_sync = datetime.now()
        self.api_endpoints = {
            "user_profiles": "/api/users",
            "preferences": "/api/preferences", 
            "activity_feed": "/api/activity",
            "notifications": "/api/notifications",
            "search_history": "/api/search-history"
        }
    
    def sync_user_data(self, user_id: str, data: Dict[str, Any]) -> bool:
        """Sync user data with User Portal Final."""
        try:
            # Get user data from normalized profiles
            normalized_path = Path(__file__).resolve().parents[3] / "ai_data" / "normalized" / f"{user_id}.json"
            user_portal_path = Path(__file__).resolve().parents[3] / "frontend" / "data" / "users" / f"{user_id}.json"
            
            if normalized_path.exists():
                with open(normalized_path, 'r', encoding='utf-8') as f:
                    user_data = json.load(f)
                
                # Merge with provided data
                if data:
                    user_data.update(data)
                
                # Ensure user portal directory exists
                os.makedirs(os.path.dirname(user_portal_path), exist_ok=True)
                
                # Sync to user portal with additional metadata
                portal_data = {
                    **user_data,
                    "last_sync": datetime.now().isoformat(),
                    "sync_source": "admin_portal",
                    "version": user_data.get("version", 1) + 0.1
                }
                
                with open(user_portal_path, 'w', encoding='utf-8') as f:
                    json.dump(portal_data, f, indent=2, ensure_ascii=False)
                

# Activate Enhanced Sidebar
if ENHANCED_SIDEBAR_AVAILABLE:
    inject_sidebar_css()
    render_enhanced_sidebar()

                st.success(f"✅ User data synced for {user_id} - {len(user_data.keys())} fields")
                return True
            else:
                st.warning(f"⚠️ User data not found for {user_id}")
                return False
                
        except Exception as e:
            st.error(f"❌ Sync error: {str(e)}")
            return False
    
    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        """Get user preferences from User Portal Final."""
        try:
            preferences_path = Path(__file__).resolve().parents[3] / "frontend" / "data" / "user_preferences" / f"{user_id}.json"
            
            if preferences_path.exists():
                with open(preferences_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                # Return default preferences and save them
                default_prefs = {
                    "theme": "dark",
                    "notifications_enabled": True,
                    "search_filters": ["location", "industry", "skills"],
                    "dashboard_layout": "modern",
                    "auto_sync": True,
                    "email_notifications": False,
                    "ai_suggestions": True,
                    "resume_format": "modern",
                    "privacy_level": "standard",
                    "created": datetime.now().isoformat()
                }
                
                # Save default preferences
                os.makedirs(os.path.dirname(preferences_path), exist_ok=True)
                with open(preferences_path, 'w', encoding='utf-8') as f:
                    json.dump(default_prefs, f, indent=2)
                
                return default_prefs
                
        except Exception as e:
            st.error(f"❌ Error loading preferences: {str(e)}")
            return {"error": str(e)}
    
    def push_admin_updates(self, update_type: str, data: Dict[str, Any]) -> bool:
        """Push admin updates to User Portal Final."""
        try:
            updates_path = Path(__file__).resolve().parents[3] / "frontend" / "data" / "admin_updates.json"
            
            # Load existing updates
            if updates_path.exists():
                with open(updates_path, 'r', encoding='utf-8') as f:
                    updates = json.load(f)
                    if "updates" not in updates:
                        updates["updates"] = []
            else:
                updates = {"updates": [], "last_updated": ""}
            
            # Add new update
            new_update = {
                "id": len(updates["updates"]) + 1,
                "timestamp": datetime.now().isoformat(),
                "type": update_type,
                "title": data.get("title", f"{update_type.title()} Update"),
                "message": data.get("message", ""),
                "priority": data.get("priority", "medium"),
                "read": False,
                "target_users": data.get("target_users", "all"),
                "data": data
            }
            
            updates["updates"].insert(0, new_update)  # Most recent first
            updates["last_updated"] = datetime.now().isoformat()
            
            # Keep only last 50 updates
            updates["updates"] = updates["updates"][:50]
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(updates_path), exist_ok=True)
            
            # Save updates
            with open(updates_path, 'w', encoding='utf-8') as f:
                json.dump(updates, f, indent=2, ensure_ascii=False)
            
            st.success(f"📤 Admin update pushed: {update_type} (ID: {new_update['id']})")
            return True
            
        except Exception as e:
            st.error(f"❌ Update push failed: {str(e)}")
            return False
    
    def get_user_activity_feed(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user activity feed from User Portal Final."""
        try:
            activity_path = Path(__file__).resolve().parents[3] / "frontend" / "data" / "user_activity" / f"{user_id}.json"
            
            if activity_path.exists():
                with open(activity_path, 'r', encoding='utf-8') as f:
                    activity_data = json.load(f)
                    activities = activity_data.get("activities", [])
                    return sorted(activities, key=lambda x: x.get("timestamp", ""), reverse=True)[:limit]
            else:
                # Generate activity from file modifications and system events
                activities = []
                base_path = Path(__file__).resolve().parents[3]
                
                # Check for recent file modifications
                user_files = [
                    base_path / "ai_data" / "normalized" / f"{user_id}.json",
                    base_path / "ai_data" / "enriched" / f"{user_id}.json",
                    base_path / "frontend" / "data" / "users" / f"{user_id}.json"
                ]
                
                for file_path in user_files:
                    if file_path.exists():
                        stat = file_path.stat()
                        activities.append({
                            "timestamp": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                            "action": f"data_updated",
                            "details": f"{file_path.name} modified",
                            "type": "file_update",
                            "size": stat.st_size
                        })
                
                # Add some system activities if no file activities
                if not activities:
                    activities = [
                        {"timestamp": datetime.now().isoformat(), "action": "profile_created", "details": "Initial profile setup", "type": "system"},
                        {"timestamp": (datetime.now() - timedelta(hours=1)).isoformat(), "action": "system_access", "details": "User accessed system", "type": "access"}
                    ]
                
                # Sort by timestamp (most recent first)
                activities.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
                return activities[:limit]
                
        except Exception as e:
            st.error(f"❌ Error loading activity feed: {str(e)}")
            return [{"timestamp": datetime.now().isoformat(), "action": "error", "details": str(e), "type": "error"}]
    
    def create_notification(self, user_id: str, message: str, notification_type: str = "info") -> bool:
        """Create notification for user in User Portal Final."""
        try:
            notifications_path = Path(__file__).resolve().parents[3] / "frontend" / "data" / "notifications" / f"{user_id}.json"
            
            # Load existing notifications
            if notifications_path.exists():
                with open(notifications_path, 'r', encoding='utf-8') as f:
                    notifications = json.load(f)
                    if "notifications" not in notifications:
                        notifications["notifications"] = []
            else:
                notifications = {"notifications": [], "last_updated": ""}
            
            # Create new notification
            new_notification = {
                "id": len(notifications["notifications"]) + 1,
                "message": message,
                "type": notification_type,
                "timestamp": datetime.now().isoformat(),
                "read": False,
                "priority": "normal",
                "source": "admin_portal"
            }
            
            notifications["notifications"].insert(0, new_notification)  # Most recent first
            notifications["last_updated"] = datetime.now().isoformat()
            
            # Keep only last 25 notifications per user
            notifications["notifications"] = notifications["notifications"][:25]
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(notifications_path), exist_ok=True)
            
            # Save notifications
            with open(notifications_path, 'w', encoding='utf-8') as f:
                json.dump(notifications, f, indent=2, ensure_ascii=False)
            
            st.success(f"🔔 Notification created for user {user_id} (ID: {new_notification['id']})")
            return True
            
        except Exception as e:
            st.error(f"❌ Notification creation failed: {str(e)}")
            return False