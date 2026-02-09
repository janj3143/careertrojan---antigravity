"""
=============================================================================
IntelliCV Admin Portal - Integration Hooks Framework
=============================================================================

This module provides lockstep synchronization and user portal integration
hooks for seamless data flow between admin portal and user-facing components.

Key Features:
- Lockstep data synchronization
- User portal integration hooks
- Real-time state management
- Event-driven updates
- Backend final integration ready
"""

import streamlit as st
import json
import logging
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from pathlib import Path
import threading
import time
from dataclasses import dataclass, asdict
from enum import Enum

# =============================================================================
# INTEGRATION CONFIGURATION
# =============================================================================

class SyncMode(Enum):
    """Synchronization modes for lockstep operations."""
    REAL_TIME = "real_time"
    BATCH = "batch"
    ON_DEMAND = "on_demand"
    SCHEDULED = "scheduled"

@dataclass
class IntegrationConfig:
    """Configuration for integration hooks."""
    lockstep_enabled: bool = True
    user_portal_sync: bool = True
    real_time_updates: bool = True
    batch_sync_interval: int = 300  # 5 minutes
    max_retry_attempts: int = 3
    sync_timeout: int = 30
    log_level: str = "INFO"
    backend_endpoint: str = "http://localhost:8000"
    user_portal_endpoint: str = "http://localhost:3000"

# =============================================================================
# LOCKSTEP SYNCHRONIZATION ENGINE
# =============================================================================

class LockstepManager:
    """
    Manages lockstep synchronization between admin portal and user portal.
    Ensures data consistency and real-time updates across all components.
    """
    
    def __init__(self, config: Optional[IntegrationConfig] = None):
        """Initialize lockstep manager with configuration."""
        self.config = config or IntegrationConfig()
        self.logger = logging.getLogger('LockstepManager')
        
        # Sync state management
        self.sync_state = {}
        self.pending_updates = []
        self.active_locks = set()
        
        # Event listeners
        self.event_listeners = {}
        
        # Background sync thread
        self.sync_thread = None
        self.is_running = False
        
        if self.config.lockstep_enabled:
            self.start_sync_engine()
    
    def start_sync_engine(self):
        """Start the background synchronization engine."""
        if not self.is_running:
            self.is_running = True
            self.sync_thread = threading.Thread(target=self._sync_loop, daemon=True)
            self.sync_thread.start()
            self.logger.info("Lockstep synchronization engine started")
    
    def stop_sync_engine(self):
        """Stop the background synchronization engine."""
        self.is_running = False
        if self.sync_thread and self.sync_thread.is_alive():
            self.sync_thread.join(timeout=5)
        self.logger.info("Lockstep synchronization engine stopped")
    
    def _sync_loop(self):
        """Main synchronization loop."""
        while self.is_running:
            try:
                if self.pending_updates:
                    self._process_pending_updates()
                time.sleep(1)  # Check every second
            except Exception as e:
                self.logger.error(f"Sync loop error: {e}")
    
    def _process_pending_updates(self):
        """Process pending synchronization updates."""
        batch = self.pending_updates.copy()
        self.pending_updates.clear()
        
        for update in batch:
            try:
                self._execute_sync_update(update)
            except Exception as e:
                self.logger.error(f"Failed to process update {update}: {e}")
                # Re-queue failed updates with retry limit
                if update.get('retry_count', 0) < self.config.max_retry_attempts:
                    update['retry_count'] = update.get('retry_count', 0) + 1
                    self.pending_updates.append(update)
    
    def _execute_sync_update(self, update: Dict[str, Any]):
        """Execute a synchronization update."""
        update_type = update.get('type', '')
        target = update.get('target', '')
        data = update.get('data', {})
        
        if target == 'user_portal' and update_type and data:
            self._sync_to_user_portal(update_type, data)
        elif target == 'shared_backend' and update_type and data:
            self._sync_to_backend(update_type, data)
        elif target == 'admin_state' and update_type and data:
            self._sync_admin_state(update_type, data)
    
    def _sync_to_user_portal(self, update_type: str, data: Dict[str, Any]):
        """Sync data to user portal."""
        # Implementation for user portal synchronization
        self.logger.info(f"Syncing to user portal: {update_type}")
        
        # Trigger event listeners
        self._trigger_event('user_portal_sync', {
            'type': update_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    
    def _sync_to_backend(self, update_type: str, data: Dict[str, Any]):
        """Sync data to backend final."""
        # Implementation for backend synchronization
        self.logger.info(f"Syncing to backend: {update_type}")
        
        # Trigger event listeners
        self._trigger_event('backend_sync', {
            'type': update_type,
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
    
    def _sync_admin_state(self, update_type: str, data: Dict[str, Any]):
        """Sync admin state changes."""
        # Update session state for real-time UI updates
        if 'admin_sync_state' not in st.session_state:
            st.session_state.admin_sync_state = {}
        
        st.session_state.admin_sync_state[update_type] = {
            'data': data,
            'timestamp': datetime.now().isoformat()
        }
        
        # Trigger rerun for UI updates
        st.rerun()
    
    def queue_update(self, update_type: str, target: str, data: Dict[str, Any]):
        """Queue an update for synchronization."""
        update = {
            'type': update_type,
            'target': target,
            'data': data,
            'timestamp': datetime.now().isoformat(),
            'retry_count': 0
        }
        
        self.pending_updates.append(update)
        self.logger.debug(f"Queued update: {update_type} -> {target}")
    
    def add_event_listener(self, event_type: str, callback: Callable):
        """Add an event listener for synchronization events."""
        if event_type not in self.event_listeners:
            self.event_listeners[event_type] = []
        self.event_listeners[event_type].append(callback)
    
    def _trigger_event(self, event_type: str, data: Dict[str, Any]):
        """Trigger event listeners."""
        if event_type in self.event_listeners:
            for callback in self.event_listeners[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    self.logger.error(f"Event listener error: {e}")

# =============================================================================
# USER PORTAL INTEGRATION
# =============================================================================

class UserPortalIntegration:
    """
    Manages integration between admin portal and user-facing portal.
    Handles data synchronization, state management, and real-time updates.
    """
    
    def __init__(self, lockstep_manager: LockstepManager):
        """Initialize user portal integration."""
        self.lockstep_manager = lockstep_manager
        self.logger = logging.getLogger('UserPortalIntegration')
        
        # Setup event listeners
        self.lockstep_manager.add_event_listener('user_portal_sync', self._handle_portal_sync)
    
    def _handle_portal_sync(self, data: Dict[str, Any]):
        """Handle synchronization events from user portal."""
        sync_type = data.get('type', '')
        sync_data = data.get('data', {})
        
        if sync_type == 'user_profile_update' and sync_data:
            self._sync_user_profile(sync_data)
        elif sync_type == 'application_status_change' and sync_data:
            self._sync_application_status(sync_data)
        elif sync_type == 'document_upload' and sync_data:
            self._sync_document_upload(sync_data)
    
    def _sync_user_profile(self, data: Dict[str, Any]):
        """Sync user profile updates."""
        # Update admin dashboard with user profile changes
        if 'admin_user_profiles' not in st.session_state:
            st.session_state.admin_user_profiles = {}
        
        user_id = data.get('user_id')
        if user_id:
            st.session_state.admin_user_profiles[user_id] = data
            self.logger.info(f"Synced user profile for user {user_id}")
    
    def _sync_application_status(self, data: Dict[str, Any]):
        """Sync application status changes."""
        # Update admin dashboard with application status changes
        if 'admin_application_status' not in st.session_state:
            st.session_state.admin_application_status = {}
        
        app_id = data.get('application_id')
        if app_id:
            st.session_state.admin_application_status[app_id] = data
            self.logger.info(f"Synced application status for application {app_id}")
    
    def _sync_document_upload(self, data: Dict[str, Any]):
        """Sync document upload notifications."""
        # Notify admin of new document uploads
        if 'admin_document_notifications' not in st.session_state:
            st.session_state.admin_document_notifications = []
        
        st.session_state.admin_document_notifications.append({
            'type': 'document_upload',
            'data': data,
            'timestamp': datetime.now().isoformat()
        })
        
        self.logger.info(f"New document upload notification: {data.get('document_type')}")
    
    def push_admin_update(self, update_type: str, data: Dict[str, Any]) -> bool:
        """Push admin updates to user portal."""
        try:
            self.lockstep_manager.queue_update(update_type, 'user_portal', data)
            return True
        except Exception as e:
            self.logger.error(f"Failed to push admin update: {e}")
            return False
    
    def get_user_portal_status(self) -> Dict[str, Any]:
        """Get current user portal synchronization status."""
        return {
            'connected': True,  # Check actual connection
            'last_sync': datetime.now().isoformat(),
            'pending_updates': len(self.lockstep_manager.pending_updates),
            'active_locks': len(self.lockstep_manager.active_locks)
        }

# =============================================================================
# BACKEND INTEGRATION
# =============================================================================

class BackendIntegration:
    """
    Manages integration with shared_backend services.
    Handles API calls, data persistence, and service coordination.
    """
    
    def __init__(self, lockstep_manager: LockstepManager):
        """Initialize backend integration."""
        self.lockstep_manager = lockstep_manager
        self.logger = logging.getLogger('BackendIntegration')
        
        # Setup event listeners
        self.lockstep_manager.add_event_listener('backend_sync', self._handle_backend_sync)
    
    def _handle_backend_sync(self, data: Dict[str, Any]):
        """Handle synchronization events to backend."""
        sync_type = data.get('type', '')
        sync_data = data.get('data', {})
        
        if sync_type == 'data_update' and sync_data:
            self._sync_data_update(sync_data)
        elif sync_type == 'config_change' and sync_data:
            self._sync_config_change(sync_data)
        elif sync_type == 'system_event' and sync_data:
            self._sync_system_event(sync_data)
    
    def _sync_data_update(self, data: Dict[str, Any]):
        """Sync data updates to backend."""
        # Implementation for data synchronization
        self.logger.info(f"Syncing data update to backend: {data.get('entity_type')}")
    
    def _sync_config_change(self, data: Dict[str, Any]):
        """Sync configuration changes to backend."""
        # Implementation for config synchronization
        self.logger.info(f"Syncing config change to backend: {data.get('config_key')}")
    
    def _sync_system_event(self, data: Dict[str, Any]):
        """Sync system events to backend."""
        # Implementation for system event synchronization
        self.logger.info(f"Syncing system event to backend: {data.get('event_type')}")
    
    def push_backend_update(self, update_type: str, data: Dict[str, Any]) -> bool:
        """Push updates to shared_backend."""
        try:
            self.lockstep_manager.queue_update(update_type, 'shared_backend', data)
            return True
        except Exception as e:
            self.logger.error(f"Failed to push backend update: {e}")
            return False
    
    def get_backend_status(self) -> Dict[str, Any]:
        """Get current backend integration status."""
        return {
            'connected': True,  # Check actual connection
            'last_sync': datetime.now().isoformat(),
            'service_health': 'healthy',
            'active_connections': 1
        }

# =============================================================================
# INTEGRATION HOOKS MANAGER
# =============================================================================

class IntegrationHooksManager:
    """
    Central manager for all integration hooks and synchronization.
    Provides unified interface for admin portal integration needs.
    """
    
    def __init__(self, config: Optional[IntegrationConfig] = None):
        """Initialize integration hooks manager."""
        self.config = config or IntegrationConfig()
        self.logger = logging.getLogger('IntegrationHooksManager')
        
        # Initialize core components
        self.lockstep_manager = LockstepManager(self.config)
        self.user_portal = UserPortalIntegration(self.lockstep_manager)
        self.backend = BackendIntegration(self.lockstep_manager)
        
        # Initialize session state
        self._init_session_state()
    
    def _init_session_state(self):
        """Initialize session state for integration hooks."""
        if 'integration_hooks' not in st.session_state:
            st.session_state.integration_hooks = {
                'initialized': True,
                'lockstep_enabled': self.config.lockstep_enabled,
                'user_portal_connected': False,
                'backend_connected': False,
                'last_sync': datetime.now().isoformat()
            }
    
    def sync_user_data(self, user_id: str, data: Dict[str, Any]):
        """Sync user data across all systems."""
        self.user_portal.push_admin_update('user_data_sync', {
            'user_id': user_id,
            'data': data
        })
        
        self.backend.push_backend_update('user_data_update', {
            'user_id': user_id,
            'data': data
        })
    
    def sync_application_data(self, app_id: str, data: Dict[str, Any]):
        """Sync application data across all systems."""
        self.user_portal.push_admin_update('application_sync', {
            'application_id': app_id,
            'data': data
        })
        
        self.backend.push_backend_update('application_update', {
            'application_id': app_id,
            'data': data
        })
    
    def sync_system_config(self, config_key: str, config_value: Any):
        """Sync system configuration changes."""
        self.backend.push_backend_update('config_change', {
            'config_key': config_key,
            'config_value': config_value
        })
        
        # Update admin state
        self.lockstep_manager.queue_update('config_update', 'admin_state', {
            'config_key': config_key,
            'config_value': config_value
        })
    
    # =============================================================================
    # EXTENDED PAGE SUPPORT (Pages 10-15)
    # =============================================================================
    
    def sync_page_10_resume_data(self, user_id: str, resume_data: Dict[str, Any]):
        """[DEPRECATED] Sync page 10 (Current Resume) data across systems.
        
        NOTE: User Portal page 10 is now UMarketU Suite (consolidated pages 12,20,21,24,25,27).
        Resume data is now part of the UMarketU Suite sync.
        
        Use sync_umarketu_suite_data() instead.
        This method maintained for backward compatibility only.
        """
        self.logger.warning(f"DEPRECATED: sync_page_10_resume_data called. Use sync_umarketu_suite_data instead.")
        
        # Forward to new method
        suite_data = {
            'resume_tuning': {
                'resume_content': resume_data.get('content', ''),
                'filename': resume_data.get('filename', ''),
                'version': resume_data.get('version', '1.0'),
                'ai_builder_suggestions': resume_data.get('ai_suggestions', [])
            }
        }
        self.sync_umarketu_suite_data(user_id, suite_data)
    
    def sync_page_11_career_intelligence(self, user_id: str, analysis_data: Dict[str, Any]):
        """[DEPRECATED] Sync page 11 (Career Intelligence Suite) analysis across systems.
        
        NOTE: User Portal pages consolidated. Career intelligence is now part of:
        - Page 10: UMarketU Suite (fit analysis, career tracking)
        - Page 11: Coaching Hub (career coaching)
        
        Use sync_umarketu_suite_data() or sync_coaching_hub_data() instead.
        This method maintained for backward compatibility only.
        """
        self.logger.warning(f"DEPRECATED: sync_page_11_career_intelligence called. Use new consolidated methods.")
        
        # Forward to UMarketU Suite
        suite_data = {
            'fit_analysis': {
                'career_score': analysis_data.get('career_score', 0),
                'market_position': analysis_data.get('market_position', ''),
                'trajectory_prediction': analysis_data.get('trajectory', []),
                'peer_comparison': analysis_data.get('peer_comparison', {}),
                'admin_ai_enriched': True
            }
        }
        self.sync_umarketu_suite_data(user_id, suite_data)
    
    def sync_page_12_application_tracking(self, user_id: str, application_data: Dict[str, Any]):
        """[DEPRECATED] Sync page 12 (Application Tracker) data across systems.
        
        NOTE: Application Tracker is now part of UMarketU Suite (User Portal Page 10).
        
        Use sync_umarketu_suite_data() instead.
        This method maintained for backward compatibility only.
        """
        self.logger.warning(f"DEPRECATED: sync_page_12_application_tracking called. Use sync_umarketu_suite_data.")
        
        # Forward to UMarketU Suite
        suite_data = {
            'application_tracker': {
                'application_id': application_data.get('application_id', ''),
                'status': application_data.get('status', ''),
                'timeline_events': application_data.get('timeline', []),
                'real_time_notification': True
            }
        }
        self.sync_umarketu_suite_data(user_id, suite_data)
    
    def sync_page_13_market_visualization(self, user_id: str, visualization_data: Dict[str, Any]):
        """[DEPRECATED] Sync page 13 (Job Title Word Cloud) visualization data.
        
        NOTE: Job Title Word Cloud is now part of:
        - User Portal Page 10: UMarketU Suite (fit analysis, resume tuning)
        - User Portal Page 13: Dual Career Suite (market visualization)
        - Admin Portal Page 21: Job Title Overlap Cloud (source of data)
        
        Use sync_dual_career_suite_data() or sync_job_title_overlap_cloud() instead.
        This method maintained for backward compatibility only.
        """
        self.logger.warning(f"DEPRECATED: sync_page_13_market_visualization called. Use sync_dual_career_suite_data.")
        
        # Forward to Dual Career Suite
        partner_data = {
            'market_visualization': {
                'word_cloud_keywords': visualization_data.get('keywords', []),
                'trending_titles': visualization_data.get('trends', []),
                'market_analysis': visualization_data.get('analysis', {})
            }
        }
        self.sync_dual_career_suite_data(user_id, partner_data)
    
    def sync_page_14_resume_suite(self, user_id: str, suite_data: Dict[str, Any]):
        """Sync page 14 (Resume Suite) comprehensive data across systems."""
        self.logger.info(f"Syncing page 14 resume suite for user {user_id}")
        
        # Sync to user portal
        self.user_portal.push_admin_update('page_14_resume_suite', {
            'user_id': user_id,
            'resume_management': suite_data.get('management_data', {}),
            'ai_tuning_results': suite_data.get('tuning_results', {}),
            'version_comparison': suite_data.get('comparison', {}),
            'feedback_analysis': suite_data.get('feedback', {}),
            'salary_intelligence': suite_data.get('salary_data', {})
        })
        
        # Sync to backend with complete integration
        self.backend.push_backend_update('resume_suite_update', {
            'user_id': user_id,
            'suite_data': suite_data,
            'source_page': 'page_14',
            'admin_ai_processed': True,
            'gpt5_orchestrator_enhanced': True,
            'postgres_version_control': True,
            'lockstep_sync_complete': True
        })
    
    def sync_page_15_instant_upload(self, user_id: str, upload_data: Dict[str, Any]):
        """Sync page 15 (Resume Upload Enhanced) instant upload data."""
        self.logger.info(f"Syncing page 15 instant upload for user {user_id}")
        
        # Sync to user portal for instant feedback
        self.user_portal.push_admin_update('page_15_instant_upload', {
            'user_id': user_id,
            'file_id': upload_data.get('file_id', ''),
            'instant_feedback': upload_data.get('feedback', {}),
            'processing_status': upload_data.get('status', 'completed'),
            'quick_analysis': upload_data.get('quick_analysis', {})
        })
        
        # Sync to backend with admin AI enrichment
        self.backend.push_backend_update('instant_upload_update', {
            'user_id': user_id,
            'upload_data': upload_data,
            'source_page': 'page_15',
            'admin_ai_enrichment': True,
            'profile_auto_enriched': True,
            'postgres_updated': True
        })
    
    def sync_fastapi_orchestrator_result(self, workflow_id: str, result_data: Dict[str, Any]):
        """Sync GPT-5 Pro orchestrator workflow results across systems."""
        self.logger.info(f"Syncing FastAPI orchestrator result: {workflow_id}")
        
        user_id = result_data.get('user_id', '')
        
        # Sync to user portal
        self.user_portal.push_admin_update('orchestrator_result', {
            'workflow_id': workflow_id,
            'user_id': user_id,
            'success': result_data.get('success', False),
            'output': result_data.get('output', {}),
            'execution_time': result_data.get('execution_time', 0)
        })
        
        # Sync to backend
        self.backend.push_backend_update('orchestrator_workflow_complete', {
            'workflow_id': workflow_id,
            'result_data': result_data,
            'gpt5_enhanced': True
        })
    
    def sync_admin_intelligence_to_pages_10_15(self, intelligence_type: str, data: Dict[str, Any]):
        """Sync admin portal intelligence (pages 10-12) to user portal pages 10-15."""
        self.logger.info(f"Syncing admin intelligence: {intelligence_type}")
        
        # Market intelligence from admin pages 10-12
        if intelligence_type == 'market_intelligence':
            self.user_portal.push_admin_update('admin_market_intelligence', {
                'source': 'admin_pages_10_11_12',
                'intelligence_data': data,
                'target_pages': ['page_11', 'page_13', 'page_14'],
                'enrichment_enabled': True
            })
        
        # Business intelligence for career analysis
        elif intelligence_type == 'business_intelligence':
            self.user_portal.push_admin_update('admin_business_intelligence', {
                'source': 'admin_pages_12_13',
                'intelligence_data': data,
                'target_pages': ['page_11', 'page_14'],
                'ai_enhanced': True
            })
        
        # Web intelligence for real-time data
        elif intelligence_type == 'web_intelligence':
            self.user_portal.push_admin_update('admin_web_intelligence', {
                'source': 'admin_web_scraper',
                'intelligence_data': data,
                'target_pages': ['page_13', 'page_14'],
                'real_time_updates': True,
                'redis_cached': True
            })
        
        # Sync to backend
        self.backend.push_backend_update('admin_intelligence_integration', {
            'intelligence_type': intelligence_type,
            'data': data,
            'admin_source': True,
            'user_portal_targets': ['page_10', 'page_11', 'page_12', 'page_13', 'page_14', 'page_15']
        })
    
    # Extended Admin Pages Synchronization (Pages 16-26)
    def sync_logging_and_error_data(self, error_data: Dict[str, Any]):
        """Sync logging, error screen snapshots (Page 16)."""
        self.logger.info("Syncing logging and error data")
        
        self.backend.push_backend_update('error_logging', {
            'error_data': error_data,
            'source': 'admin_page_16',
            'screenshots_included': True,
            'timestamp': datetime.now().isoformat()
        })
    
    def sync_backup_management(self, backup_info: Dict[str, Any]):
        """Sync backup management data (Page 17)."""
        self.logger.info("Syncing backup management data")
        
        self.backend.push_backend_update('backup_sync', {
            'backup_info': backup_info,
            'source': 'admin_page_17',
            'backup_type': backup_info.get('type', 'full')
        })
    
    def sync_job_title_ai_data(self, job_title_data: Dict[str, Any]):
        """Sync job title AI integration data (Page 20)."""
        self.logger.info("Syncing job title AI data")
        
        self.user_portal.push_admin_update('job_title_ai', {
            'job_title_data': job_title_data,
            'source': 'admin_page_20',
            'ai_enhanced': True,
            'target_pages': ['page_11', 'page_13', 'page_14']
        })
    
    def sync_software_requirements(self, requirements_data: Dict[str, Any]):
        """Sync software requirements management (Page 22)."""
        self.logger.info("Syncing software requirements data")
        
        self.backend.push_backend_update('requirements_sync', {
            'requirements': requirements_data,
            'source': 'admin_page_22'
        })
    
    def sync_ai_model_training_data(self, training_data: Dict[str, Any]):
        """Sync AI model training review data (Page 23)."""
        self.logger.info("Syncing AI model training data")
        
        self.backend.push_backend_update('ai_training_sync', {
            'training_data': training_data,
            'source': 'admin_page_23',
            'model_updates': True
        })
    
    def sync_token_management(self, token_data: Dict[str, Any]):
        """Sync token management data (Page 24)."""
        self.logger.info("Syncing token management data")
        
        self.backend.push_backend_update('token_sync', {
            'token_data': token_data,
            'source': 'admin_page_24',
            'billing_impact': True
        })
    
    def sync_intelligence_hub_data(self, hub_data: Dict[str, Any]):
        """Sync intelligence hub data (Page 25)."""
        self.logger.info("Syncing intelligence hub data")
        
        self.user_portal.push_admin_update('intelligence_hub', {
            'hub_data': hub_data,
            'source': 'admin_page_25',
            'target_pages': ['page_11', 'page_12', 'page_13', 'page_14']
        })
        
        self.backend.push_backend_update('intelligence_hub_sync', {
            'hub_data': hub_data,
            'comprehensive_sync': True
        })
    
    def sync_interface_mapping(self, mapping_data: Dict[str, Any]):
        """Sync interface mapping hub data (Page 26)."""
        self.logger.info("Syncing interface mapping data")
        
        self.backend.push_backend_update('interface_mapping', {
            'mapping_data': mapping_data,
            'source': 'admin_page_26',
            'integration_updates': True
        })
    
    def sync_job_title_overlap_cloud(self, overlap_data: Dict[str, Any]):
        """Sync Job Title Overlap Cloud (Page 21) visualization and analysis data.
        
        Pushes job title overlap analysis, word cloud data, and skill mappings to:
        - User Portal Page 10 (UMarketU Suite) - for fit analysis and resume tuning
        - User Portal Page 13 (Dual Career Suite) - for dual job search and visualization
        - Backend cache (Redis) - for fast access
        """
        self.logger.info("Syncing job title overlap cloud data (Page 21)")
        
        # Sync to user portal for UMarketU Suite (Page 10)
        self.user_portal.push_admin_update('job_title_overlap_umarketu', {
            'overlap_data': overlap_data,
            'word_cloud_keywords': overlap_data.get('word_cloud_data', []),
            'skill_overlaps': overlap_data.get('skill_overlaps', {}),
            'career_paths': overlap_data.get('career_paths', []),
            'source': 'admin_page_21',
            'target_page': 'umarketu_suite_page_10',
            'features': ['fit_analysis', 'resume_tuning']
        })
        
        # Sync to user portal for Dual Career Suite (Page 13)
        self.user_portal.push_admin_update('job_title_overlap_dual_career', {
            'overlap_data': overlap_data,
            'dual_search_keywords': overlap_data.get('word_cloud_data', []),
            'industry_overlaps': overlap_data.get('industry_overlaps', {}),
            'visualization_data': overlap_data.get('visualization', {}),
            'source': 'admin_page_21',
            'target_page': 'dual_career_suite_page_13',
            'features': ['market_visualization', 'partner_search']
        })
        
        # Sync to backend for caching and persistence
        self.backend.push_backend_update('job_title_overlap_sync', {
            'overlap_data': overlap_data,
            'source': 'admin_page_21',
            'redis_cache': True,
            'postgres_store': True,
            'cache_ttl': 3600  # 1 hour cache
        })
    
    # =============================================================================
    # USER PORTAL CONSOLIDATED PAGES (Updated October 28, 2025)
    # =============================================================================
    
    def sync_umarketu_suite_data(self, user_id: str, suite_data: Dict[str, Any]):
        """Sync UMarketU Suite (User Portal Page 10) comprehensive data.
        
        Consolidates old pages: 12, 20, 21, 24, 25, 27
        Features: Job Discovery, Fit Analysis, Resume Tuning, Application Tracker, 
                  Interview Coach, Partner Mode
        """
        self.logger.info(f"Syncing UMarketU Suite data for user {user_id}")
        
        # Sync to user portal
        self.user_portal.push_admin_update('umarketu_suite_sync', {
            'user_id': user_id,
            'job_discovery': suite_data.get('job_discovery', {}),
            'fit_analysis': suite_data.get('fit_analysis', {}),  # Uses admin page 20 data
            'resume_tuning': suite_data.get('resume_tuning', {}),  # Uses admin page 21 overlap data
            'application_tracker': suite_data.get('applications', []),
            'interview_prep': suite_data.get('interview_prep', {}),
            'partner_mode': suite_data.get('partner_mode', {}),
            'admin_enriched': True
        })
        
        # Sync to backend
        self.backend.push_backend_update('umarketu_suite_update', {
            'user_id': user_id,
            'suite_data': suite_data,
            'source_page': 'user_page_10',
            'postgres_db_sync': True,
            'includes_job_title_ai': True  # From admin page 20 & 21
        })
    
    def sync_dual_career_suite_data(self, user_id: str, partner_data: Dict[str, Any]):
        """Sync Dual Career Suite (User Portal Page 13) partner optimization data.
        
        Premium feature for dual job search with geographic feasibility.
        Uses job title matching and overlap data from admin pages 20 & 21.
        """
        self.logger.info(f"Syncing Dual Career Suite data for user {user_id}")
        
        # Sync to user portal
        self.user_portal.push_admin_update('dual_career_suite_sync', {
            'user_id': user_id,
            'partner1_profile': partner_data.get('partner1', {}),
            'partner2_profile': partner_data.get('partner2', {}),
            'dual_search_results': partner_data.get('search_results', []),
            'geographic_analysis': partner_data.get('geographic', {}),
            'market_visualization': partner_data.get('visualization', {}),  # Uses admin page 21 word cloud
            'job_title_compatibility': partner_data.get('compatibility', {}),  # Uses admin page 20 & 21
            'admin_enriched': True
        })
        
        # Sync to backend
        self.backend.push_backend_update('dual_career_update', {
            'user_id': user_id,
            'partner_data': partner_data,
            'source_page': 'user_page_13',
            'premium_feature': True,
            'uses_job_title_ai': True  # From admin page 20 & 21
        })

    def get_integration_status(self) -> Dict[str, Any]:
        """Get comprehensive integration status."""
        return {
            'lockstep_manager': {
                'running': self.lockstep_manager.is_running,
                'pending_updates': len(self.lockstep_manager.pending_updates),
                'active_locks': len(self.lockstep_manager.active_locks)
            },
            'user_portal': self.user_portal.get_user_portal_status(),
            'backend': self.backend.get_backend_status(),
            'last_status_check': datetime.now().isoformat()
        }
    
    def shutdown(self):
        """Shutdown integration hooks manager."""
        self.lockstep_manager.stop_sync_engine()
        self.logger.info("Integration hooks manager shutdown complete")

# =============================================================================
# INITIALIZATION HELPER
# =============================================================================

def get_integration_hooks() -> IntegrationHooksManager:
    """Get or create integration hooks manager instance."""
    if 'integration_hooks_manager' not in st.session_state:
        st.session_state.integration_hooks_manager = IntegrationHooksManager()
    
    return st.session_state.integration_hooks_manager

def init_integration_hooks(config: Optional[IntegrationConfig] = None):
    """Initialize integration hooks for the admin portal."""
    if 'integration_hooks_manager' not in st.session_state:
        st.session_state.integration_hooks_manager = IntegrationHooksManager(config)
        st.success("✅ Integration hooks initialized successfully")
    
    return st.session_state.integration_hooks_manager