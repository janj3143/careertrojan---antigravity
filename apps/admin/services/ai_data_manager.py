"""
=============================================================================
IntelliCV AI Data Manager - Modular Data Directory System
=============================================================================

Creates and manages intelligent data directory structure for AI processing:

📁 ai_data_main/           # Cleaned, processed data ready for production use
  ├── verified/            # Human-verified extractions (100% confidence)
  ├── high_confidence/     # AI confidence > 90% (auto-approved)
  ├── processed/           # Standard processing results (70-90% confidence)
  └── archived/            # Historical data for reference

📁 ai_data_pending/        # Data requiring AI interrogation and validation
  ├── unknown_terms/       # Terms not in learning table (research needed)
  ├── low_confidence/      # AI confidence < 70% (manual review required)
  ├── flagged/            # Suspicious or inconsistent data
  └── research_queue/     # Items queued for web/chat research

📁 ai_learning/           # Learning system data and configuration
  ├── learning_table.db   # SQLite database with learning entries
  ├── threshold_config.json # Configurable thresholds for learning
  ├── feedback_history.json # History of feedback and improvements
  └── training_data/      # Training datasets for AI models

This modular structure supports rotation sequences, data flow management,
and intelligent processing pipelines for production AI systems.

Author: IntelliCV AI Integration Team
Purpose: Production-ready data architecture with AI learning capabilities
Environment: IntelliCV\env310 with full data processing stack
"""

import os
import json
import shutil
import sqlite3
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logging_config import setup_logging, get_logger, LoggingMixin
from utils.exception_handler import ExceptionHandler, SafeOperationsMixin

# Initialize logging
setup_logging()
logger = get_logger(__name__)

# =============================================================================
# DATA FLOW CONFIGURATION
# =============================================================================

@dataclass
class DataFlowConfig:
    """Configuration for data flow and rotation policies"""
    # Confidence thresholds
    high_confidence_threshold: float = 0.90
    medium_confidence_threshold: float = 0.70
    low_confidence_threshold: float = 0.50
    
    # Rotation policies (days)
    pending_retention_days: int = 30
    processed_retention_days: int = 90
    archived_retention_days: int = 365
    
    # Processing limits
    max_pending_items: int = 1000
    max_research_queue: int = 500
    batch_processing_size: int = 50
    
    # Data validation
    enable_duplicate_detection: bool = True
    enable_quality_scoring: bool = True
    enable_auto_archival: bool = True

# =============================================================================
# AI DATA MANAGER
# =============================================================================

class AIDataManager(LoggingMixin, SafeOperationsMixin):
    """
    Intelligent data manager for modular AI data architecture.
    Handles data flow, rotation, quality assessment, and directory management.
    """
    
    def __init__(self, base_path: str = None, config: DataFlowConfig = None):
        super().__init__()
        self.base_path = Path(base_path) if base_path else Path("ai_data_system")
        self.config = config or DataFlowConfig()
        
        # Directory structure
        self.directories = {
            'main': self.base_path / "ai_data_main",
            'pending': self.base_path / "ai_data_pending", 
            'learning': self.base_path / "ai_learning"
        }
        
        # Subdirectories
        self.subdirectories = {
            'main': {
                'verified': self.directories['main'] / "verified",
                'high_confidence': self.directories['main'] / "high_confidence", 
                'processed': self.directories['main'] / "processed",
                'archived': self.directories['main'] / "archived"
            },
            'pending': {
                'unknown_terms': self.directories['pending'] / "unknown_terms",
                'low_confidence': self.directories['pending'] / "low_confidence",
                'flagged': self.directories['pending'] / "flagged",
                'research_queue': self.directories['pending'] / "research_queue"
            },
            'learning': {
                'training_data': self.directories['learning'] / "training_data",
                'models': self.directories['learning'] / "models",
                'exports': self.directories['learning'] / "exports"
            }
        }
        
        # Initialize logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Initialize system
        self._create_directory_structure()
        self._initialize_configuration()
        self._initialize_database()
        
        self.logger.info("AI Data Manager initialized successfully")
    
    def _create_directory_structure(self):
        """Create complete directory structure"""
        self.logger.info("Creating modular data directory structure...")
        
        # Create main directories
        for dir_type, path in self.directories.items():
            path.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Created directory: {path}")
        
        # Create subdirectories
        for dir_type, subdirs in self.subdirectories.items():
            for subdir_name, path in subdirs.items():
                path.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"Created subdirectory: {path}")
        
        # Create index files for each directory
        self._create_directory_indexes()
    
    def _create_directory_indexes(self):
        """Create index files for tracking directory contents"""
        for dir_type, path in self.directories.items():
            index_file = path / "directory_index.json"
            if not index_file.exists():
                index_data = {
                    'directory_type': dir_type,
                    'created': datetime.now().isoformat(),
                    'last_updated': datetime.now().isoformat(),
                    'file_count': 0,
                    'total_size_bytes': 0,
                    'description': self._get_directory_description(dir_type)
                }
                
                with open(index_file, 'w') as f:
                    json.dump(index_data, f, indent=2)
    
    def _get_directory_description(self, dir_type: str) -> str:
        """Get description for directory type"""
        descriptions = {
            'main': 'Cleaned, processed data ready for production use',
            'pending': 'Data requiring AI interrogation and validation',
            'learning': 'Learning system data and AI model configuration'
        }
        return descriptions.get(dir_type, 'AI data directory')
    
    def _initialize_configuration(self):
        """Initialize configuration files"""
        config_file = self.directories['learning'] / "threshold_config.json"
        
        if not config_file.exists():
            config_data = {
                'confidence_thresholds': {
                    'high_confidence': self.config.high_confidence_threshold,
                    'medium_confidence': self.config.medium_confidence_threshold,
                    'low_confidence': self.config.low_confidence_threshold
                },
                'rotation_policies': {
                    'pending_retention_days': self.config.pending_retention_days,
                    'processed_retention_days': self.config.processed_retention_days,
                    'archived_retention_days': self.config.archived_retention_days
                },
                'processing_limits': {
                    'max_pending_items': self.config.max_pending_items,
                    'max_research_queue': self.config.max_research_queue,
                    'batch_processing_size': self.config.batch_processing_size
                },
                'validation_settings': {
                    'enable_duplicate_detection': self.config.enable_duplicate_detection,
                    'enable_quality_scoring': self.config.enable_quality_scoring,
                    'enable_auto_archival': self.config.enable_auto_archival
                },
                'last_updated': datetime.now().isoformat()
            }
            
            with open(config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            self.logger.info(f"Configuration file created: {config_file}")
    
    def _initialize_database(self):
        """Initialize SQLite database for data tracking"""
        db_path = self.directories['learning'] / "data_flow_tracking.db"
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Data items table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS data_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT NOT NULL,
                item_type TEXT NOT NULL,
                confidence_score REAL,
                processing_status TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_updated TEXT DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,
                UNIQUE(file_path)
            )
        ''')
        
        # Data flow history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS flow_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                item_id INTEGER,
                from_directory TEXT,
                to_directory TEXT,
                reason TEXT,
                confidence_change REAL,
                timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (item_id) REFERENCES data_items (id)
            )
        ''')
        
        # Research queue table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS research_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                term TEXT NOT NULL,
                category TEXT,
                context TEXT,
                priority INTEGER DEFAULT 1,
                status TEXT DEFAULT 'pending',
                research_results TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_at TEXT
            )
        ''')
        
        # Create indexes for performance
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_processing_status ON data_items(processing_status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_confidence ON data_items(confidence_score)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_research_status ON research_queue(status)')
        
        conn.commit()
        conn.close()
        
        self.db_path = db_path
        self.logger.info(f"Database initialized: {db_path}")
    
    def add_data_item(self, file_path: str, item_type: str, confidence_score: float, 
                     metadata: Dict[str, Any] = None) -> bool:
        """
        Add data item to appropriate directory based on confidence score.
        
        Args:
            file_path: Path to the data file
            item_type: Type of data (cv, email, document, etc.)
            confidence_score: AI confidence score (0.0 to 1.0)
            metadata: Additional metadata about the item
            
        Returns:
            Success status
        """
        try:
            # Determine target directory based on confidence
            target_dir = self._get_target_directory(confidence_score)
            
            # Create unique filename
            source_path = Path(file_path)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            unique_filename = f"{timestamp}_{source_path.stem}_{item_type}{source_path.suffix}"
            target_path = target_dir / unique_filename
            
            # Copy file to target directory
            shutil.copy2(source_path, target_path)
            
            # Record in database
            self._record_data_item(str(target_path), item_type, confidence_score, metadata)
            
            # Update directory indexes
            self._update_directory_index(target_dir.parent.name, target_dir.name)
            
            self.logger.info(f"Data item added: {target_path} (confidence: {confidence_score:.2f})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add data item {file_path}: {e}")
            return False
    
    def _get_target_directory(self, confidence_score: float) -> Path:
        """Determine target directory based on confidence score"""
        if confidence_score >= self.config.high_confidence_threshold:
            return self.subdirectories['main']['high_confidence']
        elif confidence_score >= self.config.medium_confidence_threshold:
            return self.subdirectories['main']['processed']
        else:
            return self.subdirectories['pending']['low_confidence']
    
    def _record_data_item(self, file_path: str, item_type: str, confidence_score: float, 
                         metadata: Dict[str, Any]):
        """Record data item in database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Determine processing status
        if confidence_score >= self.config.high_confidence_threshold:
            status = 'ready'
        elif confidence_score >= self.config.medium_confidence_threshold:
            status = 'processed'
        else:
            status = 'pending_review'
        
        cursor.execute('''
            INSERT OR REPLACE INTO data_items 
            (file_path, item_type, confidence_score, processing_status, metadata, last_updated)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            file_path,
            item_type,
            confidence_score,
            status,
            json.dumps(metadata or {}),
            datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
    
    def queue_for_research(self, term: str, category: str, context: str = "", 
                          priority: int = 1) -> bool:
        """Queue unknown term for research"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR IGNORE INTO research_queue 
                (term, category, context, priority)
                VALUES (?, ?, ?, ?)
            ''', (term, category, context, priority))
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"Term queued for research: {term} ({category})")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to queue term for research: {e}")
            return False
    
    def process_data_rotation(self) -> Dict[str, int]:
        """Process data rotation based on retention policies"""
        rotation_stats = {
            'archived_files': 0,
            'deleted_files': 0,
            'moved_files': 0,
            'errors': 0
        }
        
        try:
            # Archive old processed files
            processed_dir = self.subdirectories['main']['processed']
            archived_dir = self.subdirectories['main']['archived']
            cutoff_processed = datetime.now() - timedelta(days=self.config.processed_retention_days)
            
            for file_path in processed_dir.glob("*"):
                if file_path.is_file():
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_processed:
                        try:
                            archive_path = archived_dir / file_path.name
                            shutil.move(str(file_path), str(archive_path))
                            rotation_stats['archived_files'] += 1
                            self._record_flow_history(str(archive_path), 'processed', 'archived', 'retention_policy')
                        except Exception as e:
                            self.logger.error(f"Failed to archive {file_path}: {e}")
                            rotation_stats['errors'] += 1
            
            # Delete old pending files
            pending_dirs = [
                self.subdirectories['pending']['unknown_terms'],
                self.subdirectories['pending']['low_confidence'],
                self.subdirectories['pending']['flagged']
            ]
            
            cutoff_pending = datetime.now() - timedelta(days=self.config.pending_retention_days)
            
            for pending_dir in pending_dirs:
                for file_path in pending_dir.glob("*"):
                    if file_path.is_file():
                        file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                        if file_time < cutoff_pending:
                            try:
                                file_path.unlink()
                                rotation_stats['deleted_files'] += 1
                            except Exception as e:
                                self.logger.error(f"Failed to delete {file_path}: {e}")
                                rotation_stats['errors'] += 1
            
            # Delete very old archived files
            cutoff_archived = datetime.now() - timedelta(days=self.config.archived_retention_days)
            
            for file_path in archived_dir.glob("*"):
                if file_path.is_file():
                    file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                    if file_time < cutoff_archived:
                        try:
                            file_path.unlink()
                            rotation_stats['deleted_files'] += 1
                        except Exception as e:
                            self.logger.error(f"Failed to delete archived {file_path}: {e}")
                            rotation_stats['errors'] += 1
            
            self.logger.info(f"Data rotation completed: {rotation_stats}")
            return rotation_stats
            
        except Exception as e:
            self.logger.error(f"Data rotation failed: {e}")
            rotation_stats['errors'] += 1
            return rotation_stats
    
    def _record_flow_history(self, file_path: str, from_dir: str, to_dir: str, reason: str):
        """Record data flow history"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get item ID
            cursor.execute('SELECT id FROM data_items WHERE file_path = ?', (file_path,))
            row = cursor.fetchone()
            
            if row:
                item_id = row[0]
                cursor.execute('''
                    INSERT INTO flow_history 
                    (item_id, from_directory, to_directory, reason)
                    VALUES (?, ?, ?, ?)
                ''', (item_id, from_dir, to_dir, reason))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            self.logger.error(f"Failed to record flow history: {e}")
    
    def _update_directory_index(self, dir_type: str, subdir_name: str = None):
        """Update directory index with current statistics"""
        try:
            if subdir_name:
                index_path = self.directories[dir_type] / "directory_index.json"
            else:
                index_path = self.directories[dir_type] / "directory_index.json"
            
            if index_path.exists():
                with open(index_path, 'r') as f:
                    index_data = json.load(f)
            else:
                index_data = {}
            
            # Count files and calculate size
            if subdir_name:
                target_dir = self.subdirectories[dir_type][subdir_name]
            else:
                target_dir = self.directories[dir_type]
            
            file_count = len([f for f in target_dir.glob("*") if f.is_file()])
            total_size = sum(f.stat().st_size for f in target_dir.glob("*") if f.is_file())
            
            # Update index
            index_data.update({
                'last_updated': datetime.now().isoformat(),
                'file_count': file_count,
                'total_size_bytes': total_size
            })
            
            with open(index_path, 'w') as f:
                json.dump(index_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Failed to update directory index: {e}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            status = {
                'directories': {},
                'database_stats': {},
                'research_queue': {},
                'recent_activity': []
            }
            
            # Directory statistics
            for dir_type, path in self.directories.items():
                dir_stats = {'subdirectories': {}}
                
                # Main directory stats
                index_file = path / "directory_index.json"
                if index_file.exists():
                    with open(index_file, 'r') as f:
                        dir_stats.update(json.load(f))
                
                # Subdirectory stats
                if dir_type in self.subdirectories:
                    for subdir_name, subdir_path in self.subdirectories[dir_type].items():
                        file_count = len([f for f in subdir_path.glob("*") if f.is_file()])
                        total_size = sum(f.stat().st_size for f in subdir_path.glob("*") if f.is_file())
                        
                        dir_stats['subdirectories'][subdir_name] = {
                            'file_count': file_count,
                            'total_size_bytes': total_size,
                            'path': str(subdir_path)
                        }
                
                status['directories'][dir_type] = dir_stats
            
            # Database statistics
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('SELECT COUNT(*) FROM data_items')
            total_items = cursor.fetchone()[0]
            
            cursor.execute('SELECT processing_status, COUNT(*) FROM data_items GROUP BY processing_status')
            status_counts = dict(cursor.fetchall())
            
            cursor.execute('SELECT COUNT(*) FROM research_queue WHERE status = "pending"')
            pending_research = cursor.fetchone()[0]
            
            status['database_stats'] = {
                'total_items': total_items,
                'status_distribution': status_counts,
                'pending_research_items': pending_research
            }
            
            # Research queue stats
            cursor.execute('''
                SELECT category, COUNT(*) FROM research_queue 
                WHERE status = "pending" 
                GROUP BY category
            ''')
            research_by_category = dict(cursor.fetchall())
            
            status['research_queue'] = {
                'total_pending': pending_research,
                'by_category': research_by_category
            }
            
            # Recent activity (last 24 hours)
            yesterday = (datetime.now() - timedelta(days=1)).isoformat()
            cursor.execute('''
                SELECT COUNT(*) FROM data_items 
                WHERE created_at > ?
            ''', (yesterday,))
            recent_items = cursor.fetchone()[0]
            
            cursor.execute('''
                SELECT COUNT(*) FROM flow_history 
                WHERE timestamp > ?
            ''', (yesterday,))
            recent_moves = cursor.fetchone()[0]
            
            status['recent_activity'] = {
                'items_added_24h': recent_items,
                'items_moved_24h': recent_moves
            }
            
            conn.close()
            
            return status
            
        except Exception as e:
            self.logger.error(f"Failed to get system status: {e}")
            return {'error': str(e)}
    
    def export_system_data(self, export_path: str) -> bool:
        """Export system data for backup or analysis"""
        try:
            export_data = {
                'export_timestamp': datetime.now().isoformat(),
                'system_status': self.get_system_status(),
                'configuration': {
                    'base_path': str(self.base_path),
                    'config': {
                        'high_confidence_threshold': self.config.high_confidence_threshold,
                        'medium_confidence_threshold': self.config.medium_confidence_threshold,
                        'low_confidence_threshold': self.config.low_confidence_threshold,
                        'pending_retention_days': self.config.pending_retention_days,
                        'processed_retention_days': self.config.processed_retention_days,
                        'archived_retention_days': self.config.archived_retention_days
                    }
                }
            }
            
            # Export database data
            conn = sqlite3.connect(self.db_path)
            
            # Export data items
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM data_items')
            columns = [description[0] for description in cursor.description]
            data_items = [dict(zip(columns, row)) for row in cursor.fetchall()]
            export_data['data_items'] = data_items
            
            # Export research queue
            cursor.execute('SELECT * FROM research_queue')
            columns = [description[0] for description in cursor.description]
            research_items = [dict(zip(columns, row)) for row in cursor.fetchall()]
            export_data['research_queue'] = research_items
            
            conn.close()
            
            # Write export file
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"System data exported to {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to export system data: {e}")
            return False
    
    def cleanup_and_optimize(self) -> Dict[str, Any]:
        """Cleanup and optimize the data system"""
        results = {
            'duplicates_removed': 0,
            'empty_dirs_removed': 0,
            'database_optimized': False,
            'indexes_updated': 0
        }
        
        try:
            # Remove duplicate files (same content hash)
            if self.config.enable_duplicate_detection:
                results['duplicates_removed'] = self._remove_duplicates()
            
            # Remove empty directories
            results['empty_dirs_removed'] = self._remove_empty_directories()
            
            # Optimize database
            conn = sqlite3.connect(self.db_path)
            conn.execute('VACUUM')
            conn.execute('ANALYZE')
            conn.close()
            results['database_optimized'] = True
            
            # Update all directory indexes
            for dir_type in self.directories.keys():
                self._update_directory_index(dir_type)
                results['indexes_updated'] += 1
            
            self.logger.info(f"System cleanup completed: {results}")
            return results
            
        except Exception as e:
            self.logger.error(f"System cleanup failed: {e}")
            results['error'] = str(e)
            return results
    
    def _remove_duplicates(self) -> int:
        """Remove duplicate files based on content hash"""
        import hashlib
        
        duplicates_removed = 0
        seen_hashes = {}
        
        try:
            # Check all directories for duplicates
            for dir_type, subdirs in self.subdirectories.items():
                for subdir_name, subdir_path in subdirs.items():
                    for file_path in subdir_path.glob("*"):
                        if file_path.is_file():
                            # Calculate file hash
                            hasher = hashlib.md5()
                            with open(file_path, 'rb') as f:
                                for chunk in iter(lambda: f.read(4096), b""):
                                    hasher.update(chunk)
                            file_hash = hasher.hexdigest()
                            
                            if file_hash in seen_hashes:
                                # Duplicate found - keep the one in higher priority directory
                                existing_path = seen_hashes[file_hash]
                                if self._get_directory_priority(file_path) > self._get_directory_priority(existing_path):
                                    # Remove existing, keep current
                                    existing_path.unlink()
                                    seen_hashes[file_hash] = file_path
                                else:
                                    # Remove current, keep existing
                                    file_path.unlink()
                                duplicates_removed += 1
                            else:
                                seen_hashes[file_hash] = file_path
            
            return duplicates_removed
            
        except Exception as e:
            self.logger.error(f"Duplicate removal failed: {e}")
            return duplicates_removed
    
    def _get_directory_priority(self, file_path: Path) -> int:
        """Get priority for directory (higher = more important)"""
        path_str = str(file_path)
        
        if 'verified' in path_str:
            return 100
        elif 'high_confidence' in path_str:
            return 90
        elif 'processed' in path_str:
            return 80
        elif 'archived' in path_str:
            return 70
        else:
            return 50
    
    def _remove_empty_directories(self) -> int:
        """Remove empty directories"""
        removed_count = 0
        
        try:
            for dir_type, subdirs in self.subdirectories.items():
                for subdir_name, subdir_path in subdirs.items():
                    if subdir_path.exists() and not any(subdir_path.iterdir()):
                        # Directory is empty, but don't remove it - just log
                        self.logger.info(f"Empty directory found: {subdir_path}")
            
            return removed_count
            
        except Exception as e:
            self.logger.error(f"Empty directory removal failed: {e}")
            return removed_count

# =============================================================================
# MAIN EXECUTION & TESTING
# =============================================================================

if __name__ == "__main__":
    # Example usage and testing
    logger.info("IntelliCV AI Data Manager - Testing")
    
    # Initialize data manager
    config = DataFlowConfig(
        high_confidence_threshold=0.90,
        medium_confidence_threshold=0.70,
        pending_retention_days=30,
        max_pending_items=1000
    )
    
    data_manager = AIDataManager(
        base_path="test_ai_data_system",
        config=config
    )
    
    # Test adding data items
    logger.info("\nTesting data item addition...")
    
    # Create test files
    test_files = [
        ("high_conf_cv.txt", "cv", 0.95, {"source": "email", "language": "en"}),
        ("medium_conf_doc.txt", "document", 0.75, {"source": "upload", "pages": 2}),
        ("low_conf_resume.txt", "resume", 0.45, {"source": "web", "quality": "poor"})
    ]
    
    for filename, item_type, confidence, metadata in test_files:
        # Create test file
        test_path = Path(filename)
        test_path.write_text(f"Test content for {filename}\nConfidence: {confidence}")
        
        # Add to data manager
        success = data_manager.add_data_item(str(test_path), item_type, confidence, metadata)
        logger.info(f"Added {filename}: {'Success' if success else 'Failed'}")
        
        # Clean up test file
        if test_path.exists():
            test_path.unlink()
        test_path.unlink(missing_ok=True)
    
    # Test research queue
    logger.info("\nTesting research queue...")
    data_manager.queue_for_research("AI/ML Engineer", "job_titles", "Found in CV", priority=2)
    data_manager.queue_for_research("TensorFlow", "skills", "Technical skill", priority=1)
    
    # Get system status
    logger.info("\nSystem Status:")
    status = data_manager.get_system_status()
    logger.info(f"Total data items: {status['database_stats']['total_items']}")
    logger.info(f"Pending research: {status['database_stats']['pending_research_items']}")
    
    logger.info("\nTesting data rotation...")
    rotation_stats = data_manager.process_data_rotation()
    logger.info(f"Rotation results: {rotation_stats}")otation()
    print(f"Rotation results: {rotation_stats}")
    
    # Export system data
    export_file = "ai_data_system_export.json"
    success = data_manager.export_system_data(export_file)
    logger.info(f"Export to {export_file}: {'Success' if success else 'Failed'}")
    
    # Cleanup and optimize
    logger.info("\nRunning system cleanup...")
    cleanup_results = data_manager.cleanup_and_optimize()
    logger.info(f"Cleanup results: {cleanup_results}")
    
    logger.info("\nAI Data Manager testing completed!")
    logger.info(f"Directory structure created at: {data_manager.base_path}")