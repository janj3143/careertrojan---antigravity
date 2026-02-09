"""
Admin-User Portal Lockstep Integration Framework
==============================================

This module provides the technical framework for seamless integration
between the IntelliCV Admin Portal and User Portal, ensuring real-time
data synchronization and consistent user experience.
"""

import asyncio
import json
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PortalType(Enum):
    """Portal type enumeration"""
    ADMIN = "admin"
    USER = "user"

class SyncPriority(Enum):
    """Synchronization priority levels"""
    CRITICAL = "critical"    # Authentication, security
    HIGH = "high"           # Processing status, notifications  
    MEDIUM = "medium"       # Analytics, preferences
    LOW = "low"            # Logs, historical data

class NotificationType(Enum):
    """Notification types for cross-portal communication"""
    PROCESSING_COMPLETE = "processing_complete"
    SYSTEM_ALERT = "system_alert"
    PROFILE_UPDATE = "profile_update"
    AI_INSIGHTS = "ai_insights"
    MARKET_UPDATE = "market_update"
    ERROR_NOTIFICATION = "error_notification"

@dataclass
class SyncEvent:
    """Data synchronization event"""
    event_id: str
    user_id: str
    event_type: str
    data: Dict[str, Any]
    priority: SyncPriority
    source_portal: PortalType
    target_portal: PortalType
    timestamp: str
    processed: bool = False
    retry_count: int = 0

@dataclass
class UserPortalProfile:
    """User portal profile structure"""
    user_id: str
    email: str
    first_name: str
    last_name: str
    preferences: Dict[str, Any]
    processing_status: Dict[str, Any]
    last_sync: str
    active_sessions: List[str]

class AdminUserBridge:
    """Main bridge class for admin-user portal integration"""
    
    def __init__(self, db_path: str = "admin_user_bridge.db"):
        self.db_path = db_path
        self.sync_queue = asyncio.Queue()
        self.active_connections = {}
        self.sync_running = False
        self.setup_database()
        
    def setup_database(self):
        """Initialize the bridge database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Sync events table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sync_events (
                    event_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    data TEXT NOT NULL,
                    priority TEXT NOT NULL,
                    source_portal TEXT NOT NULL,
                    target_portal TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    processed BOOLEAN DEFAULT FALSE,
                    retry_count INTEGER DEFAULT 0,
                    INDEX(user_id),
                    INDEX(event_type),
                    INDEX(processed),
                    INDEX(timestamp)
                )
            ''')
            
            # User portal profiles
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_portal_profiles (
                    user_id TEXT PRIMARY KEY,
                    email TEXT NOT NULL,
                    first_name TEXT,
                    last_name TEXT,
                    preferences TEXT,
                    processing_status TEXT,
                    last_sync TEXT,
                    active_sessions TEXT,
                    created_at TEXT,
                    updated_at TEXT
                )
            ''')
            
            # Cross-portal notifications
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS portal_notifications (
                    notification_id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    notification_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    data TEXT,
                    priority TEXT NOT NULL,
                    sent_at TEXT,
                    read_at TEXT,
                    portal_target TEXT NOT NULL,
                    INDEX(user_id),
                    INDEX(notification_type),
                    INDEX(sent_at)
                )
            ''')
            
            # Integration status tracking
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS integration_status (
                    user_id TEXT PRIMARY KEY,
                    admin_portal_status TEXT DEFAULT 'active',
                    user_portal_status TEXT DEFAULT 'active',
                    last_admin_sync TEXT,
                    last_user_sync TEXT,
                    sync_errors INTEGER DEFAULT 0,
                    created_at TEXT,
                    updated_at TEXT
                )
            ''')
            
            conn.commit()
            logger.info("Bridge database initialized successfully")
    
    async def start_sync_service(self):
        """Start the background synchronization service"""
        if self.sync_running:
            logger.warning("Sync service already running")
            return
            
        self.sync_running = True
        logger.info("Starting admin-user portal sync service")
        
        # Start background tasks
        await asyncio.gather(
            self.process_sync_queue(),
            self.periodic_sync_check(),
            self.cleanup_old_events()
        )
    
    async def process_sync_queue(self):
        """Process synchronization events from the queue"""
        while self.sync_running:
            try:
                # Get next sync event with timeout
                event = await asyncio.wait_for(self.sync_queue.get(), timeout=1.0)
                await self.handle_sync_event(event)
                self.sync_queue.task_done()
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing sync queue: {str(e)}")
                await asyncio.sleep(1)
    
    async def handle_sync_event(self, event: SyncEvent):
        """Handle individual synchronization event"""
        try:
            logger.info(f"Processing sync event: {event.event_type} for user {event.user_id}")
            
            # Process based on event type
            if event.event_type == "profile_update":
                await self.sync_user_profile(event)
            elif event.event_type == "processing_status":
                await self.sync_processing_status(event)
            elif event.event_type == "ai_insights":
                await self.sync_ai_insights(event)
            elif event.event_type == "market_intelligence":
                await self.sync_market_data(event)
            elif event.event_type == "notification":
                await self.send_cross_portal_notification(event)
            else:
                await self.handle_custom_sync_event(event)
            
            # Mark as processed
            await self.mark_event_processed(event.event_id)
            
        except Exception as e:
            logger.error(f"Error handling sync event {event.event_id}: {str(e)}")
            await self.retry_sync_event(event)
    
    async def sync_user_profile(self, event: SyncEvent):
        """Synchronize user profile between portals"""
        user_id = event.user_id
        profile_data = event.data
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Update or insert user profile
            cursor.execute('''
                INSERT OR REPLACE INTO user_portal_profiles 
                (user_id, email, first_name, last_name, preferences, 
                 processing_status, last_sync, active_sessions, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id,
                profile_data.get('email'),
                profile_data.get('first_name'),
                profile_data.get('last_name'),
                json.dumps(profile_data.get('preferences', {})),
                json.dumps(profile_data.get('processing_status', {})),
                datetime.now().isoformat(),
                json.dumps(profile_data.get('active_sessions', [])),
                datetime.now().isoformat()
            ))
            
            conn.commit()
            logger.info(f"User profile synchronized for user {user_id}")
    
    async def sync_processing_status(self, event: SyncEvent):
        """Synchronize CV processing status to user portal"""
        user_id = event.user_id
        status_data = event.data
        
        # Update processing status in user profile
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE user_portal_profiles 
                SET processing_status = ?, last_sync = ?, updated_at = ?
                WHERE user_id = ?
            ''', (
                json.dumps(status_data),
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                user_id
            ))
            
            conn.commit()
            
        # Send notification to user portal
        await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.PROCESSING_COMPLETE,
            title="Processing Update",
            message=f"CV processing {status_data.get('status', 'updated')}",
            data=status_data,
            priority=SyncPriority.HIGH,
            target_portal=PortalType.USER
        )
        
        logger.info(f"Processing status synchronized for user {user_id}")
    
    async def sync_ai_insights(self, event: SyncEvent):
        """Synchronize AI insights to user portal"""
        user_id = event.user_id
        insights_data = event.data
        
        # Send AI insights notification
        await self.send_notification(
            user_id=user_id,
            notification_type=NotificationType.AI_INSIGHTS,
            title="New AI Insights Available",
            message="Your profile has been enhanced with new AI insights",
            data=insights_data,
            priority=SyncPriority.HIGH,
            target_portal=PortalType.USER
        )
        
        logger.info(f"AI insights synchronized for user {user_id}")
    
    async def sync_market_data(self, event: SyncEvent):
        """Synchronize market intelligence to relevant users"""
        market_data = event.data
        target_users = market_data.get('target_users', [])
        
        for user_id in target_users:
            await self.send_notification(
                user_id=user_id,
                notification_type=NotificationType.MARKET_UPDATE,
                title="Market Intelligence Update",
                message="New market insights available for your profile",
                data=market_data,
                priority=SyncPriority.MEDIUM,
                target_portal=PortalType.USER
            )
        
        logger.info(f"Market data synchronized to {len(target_users)} users")
    
    async def send_cross_portal_notification(self, event: SyncEvent):
        """Send notification between portals"""
        notification_data = event.data
        
        await self.send_notification(
            user_id=event.user_id,
            notification_type=NotificationType(notification_data['type']),
            title=notification_data['title'],
            message=notification_data['message'],
            data=notification_data.get('data'),
            priority=SyncPriority(notification_data.get('priority', 'medium')),
            target_portal=PortalType(notification_data['target_portal'])
        )
    
    async def send_notification(self, user_id: str, notification_type: NotificationType,
                              title: str, message: str, data: Dict = None,
                              priority: SyncPriority = SyncPriority.MEDIUM,
                              target_portal: PortalType = PortalType.USER):
        """Send notification to target portal"""
        notification_id = f"notif_{int(time.time())}_{user_id}"
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO portal_notifications 
                (notification_id, user_id, notification_type, title, message, 
                 data, priority, sent_at, portal_target)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                notification_id,
                user_id,
                notification_type.value,
                title,
                message,
                json.dumps(data) if data else None,
                priority.value,
                datetime.now().isoformat(),
                target_portal.value
            ))
            
            conn.commit()
            logger.info(f"Notification sent to {target_portal.value} portal for user {user_id}")
    
    async def queue_sync_event(self, user_id: str, event_type: str, data: Dict[str, Any],
                             priority: SyncPriority = SyncPriority.MEDIUM,
                             source_portal: PortalType = PortalType.ADMIN,
                             target_portal: PortalType = PortalType.USER):
        """Add synchronization event to queue"""
        event_id = f"sync_{int(time.time())}_{user_id}_{event_type}"
        
        event = SyncEvent(
            event_id=event_id,
            user_id=user_id,
            event_type=event_type,
            data=data,
            priority=priority,
            source_portal=source_portal,
            target_portal=target_portal,
            timestamp=datetime.now().isoformat()
        )
        
        # Store in database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO sync_events 
                (event_id, user_id, event_type, data, priority, 
                 source_portal, target_portal, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                event.event_id,
                event.user_id,
                event.event_type,
                json.dumps(event.data),
                event.priority.value,
                event.source_portal.value,
                event.target_portal.value,
                event.timestamp
            ))
            conn.commit()
        
        # Add to processing queue
        await self.sync_queue.put(event)
        logger.info(f"Sync event queued: {event_type} for user {user_id}")
    
    async def get_user_notifications(self, user_id: str, portal_type: PortalType = PortalType.USER,
                                   unread_only: bool = True) -> List[Dict]:
        """Get notifications for user portal"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            where_clause = "WHERE user_id = ? AND portal_target = ?"
            params = [user_id, portal_type.value]
            
            if unread_only:
                where_clause += " AND read_at IS NULL"
            
            cursor.execute(f'''
                SELECT notification_id, notification_type, title, message, 
                       data, priority, sent_at, read_at
                FROM portal_notifications 
                {where_clause}
                ORDER BY sent_at DESC
            ''', params)
            
            notifications = []
            for row in cursor.fetchall():
                notifications.append({
                    'notification_id': row[0],
                    'type': row[1],
                    'title': row[2],
                    'message': row[3],
                    'data': json.loads(row[4]) if row[4] else None,
                    'priority': row[5],
                    'sent_at': row[6],
                    'read_at': row[7]
                })
            
            return notifications
    
    async def mark_notification_read(self, notification_id: str):
        """Mark notification as read"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE portal_notifications 
                SET read_at = ? 
                WHERE notification_id = ?
            ''', (datetime.now().isoformat(), notification_id))
            conn.commit()
    
    async def get_user_portal_status(self, user_id: str) -> Dict[str, Any]:
        """Get integration status for specific user"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get integration status
            cursor.execute('''
                SELECT admin_portal_status, user_portal_status, 
                       last_admin_sync, last_user_sync, sync_errors
                FROM integration_status 
                WHERE user_id = ?
            ''', (user_id,))
            
            status_row = cursor.fetchone()
            if not status_row:
                return {"status": "not_initialized"}
            
            # Get recent sync events
            cursor.execute('''
                SELECT COUNT(*) as pending_events
                FROM sync_events 
                WHERE user_id = ? AND processed = FALSE
            ''', (user_id,))
            
            pending_events = cursor.fetchone()[0]
            
            # Get user profile
            cursor.execute('''
                SELECT email, first_name, last_name, last_sync
                FROM user_portal_profiles 
                WHERE user_id = ?
            ''', (user_id,))
            
            profile_row = cursor.fetchone()
            
            return {
                "admin_status": status_row[0],
                "user_status": status_row[1],
                "last_admin_sync": status_row[2],
                "last_user_sync": status_row[3],
                "sync_errors": status_row[4],
                "pending_events": pending_events,
                "profile": {
                    "email": profile_row[0] if profile_row else None,
                    "name": f"{profile_row[1]} {profile_row[2]}" if profile_row else None,
                    "last_sync": profile_row[3] if profile_row else None
                } if profile_row else None
            }
    
    async def periodic_sync_check(self):
        """Periodic check for sync integrity"""
        while self.sync_running:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                
                # Check for failed sync events
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    cursor.execute('''
                        SELECT event_id, user_id, event_type, retry_count
                        FROM sync_events 
                        WHERE processed = FALSE 
                        AND timestamp < ? 
                        AND retry_count < 3
                    ''', (
                        (datetime.now() - timedelta(minutes=10)).isoformat(),
                    ))
                    
                    failed_events = cursor.fetchall()
                    
                    for event_row in failed_events:
                        logger.warning(f"Retrying failed sync event: {event_row[0]}")
                        # Could implement retry logic here
                
            except Exception as e:
                logger.error(f"Error in periodic sync check: {str(e)}")
    
    async def cleanup_old_events(self):
        """Clean up old processed events"""
        while self.sync_running:
            try:
                await asyncio.sleep(3600)  # Clean every hour
                
                cutoff_time = (datetime.now() - timedelta(days=7)).isoformat()
                
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Clean old processed events
                    cursor.execute('''
                        DELETE FROM sync_events 
                        WHERE processed = TRUE AND timestamp < ?
                    ''', (cutoff_time,))
                    
                    # Clean old read notifications
                    cursor.execute('''
                        DELETE FROM portal_notifications 
                        WHERE read_at IS NOT NULL AND sent_at < ?
                    ''', (cutoff_time,))
                    
                    deleted_events = cursor.rowcount
                    conn.commit()
                    
                    if deleted_events > 0:
                        logger.info(f"Cleaned up {deleted_events} old sync records")
                
            except Exception as e:
                logger.error(f"Error in cleanup: {str(e)}")
    
    async def stop_sync_service(self):
        """Stop the synchronization service"""
        self.sync_running = False
        logger.info("Admin-user portal sync service stopped")
    
    # High-level API methods for common operations
    
    async def user_uploaded_cv(self, user_id: str, cv_data: Dict[str, Any]):
        """Handle user CV upload event"""
        await self.queue_sync_event(
            user_id=user_id,
            event_type="processing_status",
            data={
                "status": "uploaded",
                "filename": cv_data.get("filename"),
                "upload_time": datetime.now().isoformat(),
                "processing_queue_position": cv_data.get("queue_position", 1)
            },
            priority=SyncPriority.HIGH,
            source_portal=PortalType.USER,
            target_portal=PortalType.ADMIN
        )
    
    async def admin_processed_cv(self, user_id: str, processing_result: Dict[str, Any]):
        """Handle admin CV processing completion"""
        await self.queue_sync_event(
            user_id=user_id,
            event_type="processing_status",
            data={
                "status": "completed",
                "result": processing_result,
                "processed_time": datetime.now().isoformat()
            },
            priority=SyncPriority.HIGH,
            source_portal=PortalType.ADMIN,
            target_portal=PortalType.USER
        )
    
    async def share_ai_insights(self, user_id: str, insights: Dict[str, Any]):
        """Share AI insights with user portal"""
        await self.queue_sync_event(
            user_id=user_id,
            event_type="ai_insights",
            data=insights,
            priority=SyncPriority.HIGH,
            source_portal=PortalType.ADMIN,
            target_portal=PortalType.USER
        )
    
    async def broadcast_market_intelligence(self, market_data: Dict[str, Any], target_users: List[str]):
        """Broadcast market intelligence to relevant users"""
        market_data['target_users'] = target_users
        
        await self.queue_sync_event(
            user_id="system",
            event_type="market_intelligence",
            data=market_data,
            priority=SyncPriority.MEDIUM,
            source_portal=PortalType.ADMIN,
            target_portal=PortalType.USER
        )

# Global bridge instance
_bridge_instance: Optional[AdminUserBridge] = None

def get_bridge() -> AdminUserBridge:
    """Get global bridge instance"""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = AdminUserBridge()
    return _bridge_instance

# Convenience functions for common operations
async def sync_user_profile_update(user_id: str, profile_data: Dict[str, Any]):
    """Convenience function for profile updates"""
    bridge = get_bridge()
    await bridge.queue_sync_event(
        user_id=user_id,
        event_type="profile_update",
        data=profile_data,
        priority=SyncPriority.HIGH
    )

async def notify_processing_complete(user_id: str, processing_result: Dict[str, Any]):
    """Convenience function for processing completion"""
    bridge = get_bridge()
    await bridge.admin_processed_cv(user_id, processing_result)

async def send_system_alert(user_id: str, alert_message: str, alert_data: Dict = None):
    """Convenience function for system alerts"""
    bridge = get_bridge()
    await bridge.send_notification(
        user_id=user_id,
        notification_type=NotificationType.SYSTEM_ALERT,
        title="System Alert",
        message=alert_message,
        data=alert_data,
        priority=SyncPriority.CRITICAL
    )

# Example usage and testing functions
async def example_usage():
    """Example of how to use the bridge system"""
    bridge = get_bridge()
    
    # Start the sync service
    asyncio.create_task(bridge.start_sync_service())
    
    # Example: User uploads CV
    await bridge.user_uploaded_cv("user123", {
        "filename": "john_doe_cv.pdf",
        "queue_position": 1
    })
    
    # Example: Admin processes CV
    await bridge.admin_processed_cv("user123", {
        "success": True,
        "extracted_data": {"name": "John Doe", "skills": ["Python", "AI"]},
        "confidence": 0.95
    })
    
    # Example: Share AI insights
    await bridge.share_ai_insights("user123", {
        "career_recommendations": ["Data Scientist", "AI Engineer"],
        "skill_gaps": ["Machine Learning", "Deep Learning"],
        "market_fit": 0.87
    })
    
    # Example: Get user notifications
    notifications = await bridge.get_user_notifications("user123")
    print(f"User has {len(notifications)} notifications")

if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())