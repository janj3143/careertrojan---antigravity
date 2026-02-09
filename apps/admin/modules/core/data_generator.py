
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


# Activate Enhanced Sidebar
if ENHANCED_SIDEBAR_AVAILABLE:
    inject_sidebar_css()
    render_enhanced_sidebar()

"""
IntelliCV-AI Data Generation System
=================================

This module creates and manages the SQLite database and JSON data generation
for the AI dashboard            # Audit Logs Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id TEXT PRIMARY KEY,
                    admin_user_id TEXT,
                    action TEXT NOT NULL,
                    resource_type TEXT,
                    resource_id TEXT,
                    details TEXT, -- JSON string
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    user_agent TEXT
                )
            ''')
            
            # Error Logs Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS error_logs (
                    id TEXT PRIMARY KEY,
                    error_type TEXT NOT NULL,
                    severity TEXT NOT NULL DEFAULT 'medium',
                    title TEXT NOT NULL,
                    description TEXT,
                    stack_trace TEXT,
                    user_context TEXT, -- JSON string with user info
                    system_context TEXT, -- JSON string with system info
                    reported_by TEXT,
                    status TEXT DEFAULT 'open',
                    resolution TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP,
                    tags TEXT -- JSON array
                )
            ''')
            
            conn.commit()
            self.logger.info("Database schema created successfully")nsures all dashboard links have proper
data sources before AI interpretation begins.
"""

import json
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import random
import logging
import glob
import os

class IntelliCVDataGenerator:
    """
    Comprehensive data generation system for IntelliCV-AI dashboard.
    
    Creates:
    - SQLite database with all required tables
    - JSON exports for AI component consumption
    - Realistic test data for dashboard testing
    - Data verification and linking system
    """
    
    def __init__(self, base_path: Optional[Path] = None, existing_data_path: Optional[Path] = None):
        """Initialize the data generator."""
        self.base_path = base_path or Path(__file__).parents[3]
        self.db_path = self.base_path / "data" / "intellicv_admin.db"
        self.json_export_path = self.base_path / "ai_data"
        self.frontend_data_path = self.base_path / "frontend" / "data"
        
        # Path to existing AI enrichment data
        if existing_data_path:
            self.existing_data_path = Path(existing_data_path)
        else:
            # Default to the Data_forAi_Enrichment_linked_Admin_portal_final directory
            self.existing_data_path = Path("c:/IntelliCV/admin_portal_final/Data_forAi_Enrichment_linked_Admin_portal_final/ai_data")
        
        # Ensure directories exist
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.json_export_path.mkdir(parents=True, exist_ok=True)
        self.frontend_data_path.mkdir(parents=True, exist_ok=True)
        (self.frontend_data_path / "users").mkdir(exist_ok=True)
        (self.frontend_data_path / "user_preferences").mkdir(exist_ok=True)
        (self.frontend_data_path / "user_activity").mkdir(exist_ok=True)
        (self.json_export_path / "normalized").mkdir(exist_ok=True)
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('IntelliCVDataGenerator')
        
        # Initialize database
        self._create_database_schema()
        self._update_schema_if_needed()
        
        self.logger.info(f"Data generator initialized - DB: {self.db_path}")
    
    def _create_database_schema(self):
        """Create the complete SQLite database schema."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Admin Users Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS admin_users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT UNIQUE NOT NULL,
                    role TEXT DEFAULT 'admin',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1,
                    permissions TEXT -- JSON string
                )
            ''')
            
            # System Metrics Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS system_metrics (
                    id TEXT PRIMARY KEY,
                    metric_type TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    service_name TEXT,
                    metadata TEXT -- JSON string
                )
            ''')
            
            # User Profiles Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_profiles (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE NOT NULL,
                    full_name TEXT,
                    skills TEXT, -- JSON array
                    experience_years INTEGER,
                    current_role TEXT,
                    location TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ai_score REAL,
                    profile_completeness REAL,
                    metadata TEXT -- JSON string for additional data
                )
            ''')
            
            # CV Documents Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cv_documents (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    filename TEXT,
                    file_size INTEGER,
                    upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    processing_status TEXT DEFAULT 'pending',
                    ai_analysis TEXT, -- JSON string
                    skills_extracted TEXT, -- JSON array
                    confidence_score REAL,
                    extracted_text TEXT, -- Full extracted text content
                    FOREIGN KEY (user_id) REFERENCES user_profiles (id)
                )
            ''')
            
            # Job Postings Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS job_postings (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    company TEXT,
                    location TEXT,
                    salary_min INTEGER,
                    salary_max INTEGER,
                    required_skills TEXT, -- JSON array
                    description TEXT,
                    posted_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'active',
                    ai_requirements TEXT -- JSON object
                )
            ''')
            
            # AI Processing Queue Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ai_processing_queue (
                    id TEXT PRIMARY KEY,
                    task_type TEXT NOT NULL,
                    input_data TEXT, -- JSON string
                    status TEXT DEFAULT 'pending',
                    priority INTEGER DEFAULT 5,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    result_data TEXT, -- JSON string
                    error_message TEXT
                )
            ''')
            
            # Market Intelligence Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS market_intelligence (
                    id TEXT PRIMARY KEY,
                    data_type TEXT NOT NULL,
                    industry TEXT,
                    location TEXT,
                    data_value TEXT, -- JSON string
                    confidence_score REAL,
                    source TEXT,
                    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Audit Log Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS audit_logs (
                    id TEXT PRIMARY KEY,
                    admin_user_id TEXT,
                    action TEXT NOT NULL,
                    resource_type TEXT,
                    resource_id TEXT,
                    details TEXT, -- JSON string
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    user_agent TEXT
                )
            ''')
            
            # Error Logs Table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS error_logs (
                    id TEXT PRIMARY KEY,
                    error_type TEXT NOT NULL,
                    severity TEXT NOT NULL DEFAULT 'medium',
                    title TEXT NOT NULL,
                    description TEXT,
                    stack_trace TEXT,
                    user_context TEXT, -- JSON string with user info
                    system_context TEXT, -- JSON string with system info
                    reported_by TEXT,
                    status TEXT DEFAULT 'open',
                    resolution TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP,
                    tags TEXT -- JSON array
                )
            ''')
            
            conn.commit()
            self.logger.info("Database schema created successfully")
    
    def _update_schema_if_needed(self):
        """Update database schema to add missing columns."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            try:
                # Check if metadata column exists in user_profiles
                cursor.execute("PRAGMA table_info(user_profiles)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'metadata' not in columns:
                    cursor.execute("ALTER TABLE user_profiles ADD COLUMN metadata TEXT")
                    self.logger.info("Added metadata column to user_profiles table")
                
                # Check if extracted_text column exists in cv_documents
                cursor.execute("PRAGMA table_info(cv_documents)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'extracted_text' not in columns:
                    cursor.execute("ALTER TABLE cv_documents ADD COLUMN extracted_text TEXT")
                    self.logger.info("Added extracted_text column to cv_documents table")
                
                # Check if content column exists in market_intelligence
                cursor.execute("PRAGMA table_info(market_intelligence)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'content' not in columns:
                    cursor.execute("ALTER TABLE market_intelligence ADD COLUMN content TEXT")
                    self.logger.info("Added content column to market_intelligence table")
                
                if 'created_at' not in columns:
                    cursor.execute("ALTER TABLE market_intelligence ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
                    self.logger.info("Added created_at column to market_intelligence table")
                
                if 'source' not in columns:
                    cursor.execute("ALTER TABLE market_intelligence ADD COLUMN source TEXT")
                    self.logger.info("Added source column to market_intelligence table")
                
                # Check audit_logs table columns
                cursor.execute("PRAGMA table_info(audit_logs)")
                columns = [column[1] for column in cursor.fetchall()]
                
                missing_audit_columns = ['user_id', 'action', 'resource_type', 'resource_id', 'details', 'ip_address', 'user_agent']
                for col in missing_audit_columns:
                    if col not in columns:
                        cursor.execute(f"ALTER TABLE audit_logs ADD COLUMN {col} TEXT")
                        self.logger.info(f"Added {col} column to audit_logs table")
                
                # Check if error_logs table exists
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='error_logs'")
                if not cursor.fetchone():
                    cursor.execute('''
                        CREATE TABLE error_logs (
                            id TEXT PRIMARY KEY,
                            error_type TEXT NOT NULL,
                            severity TEXT NOT NULL DEFAULT 'medium',
                            title TEXT NOT NULL,
                            description TEXT,
                            stack_trace TEXT,
                            user_context TEXT, -- JSON string with user info
                            system_context TEXT, -- JSON string with system info
                            reported_by TEXT,
                            status TEXT DEFAULT 'open',
                            resolution TEXT,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            resolved_at TIMESTAMP,
                            tags TEXT -- JSON array
                        )
                    ''')
                    self.logger.info("Created error_logs table")
                
                conn.commit()
                
            except Exception as e:
                self.logger.warning(f"Schema update error: {e}")
    
    def generate_sample_data(self, num_users: int = 50):
        """Generate realistic sample data for testing."""
        self.logger.info(f"Generating sample data for {num_users} users...")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Generate admin users
            admin_users = [
                {
                    'id': str(uuid.uuid4()),
                    'username': 'admin',
                    'email': 'admin@intellicv.ai',
                    'role': 'superadmin',
                    'permissions': json.dumps(['all'])
                },
                {
                    'id': str(uuid.uuid4()),
                    'username': 'hr_admin',
                    'email': 'hr@intellicv.ai',
                    'role': 'hr_admin',
                    'permissions': json.dumps(['users', 'reports', 'analytics'])
                }
            ]
            
            for admin in admin_users:
                cursor.execute('''
                    INSERT OR REPLACE INTO admin_users 
                    (id, username, email, role, permissions, last_login)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (admin['id'], admin['username'], admin['email'], 
                     admin['role'], admin['permissions'], datetime.now()))
            
            # Generate user profiles
            sample_skills = [
                ["Python", "Machine Learning", "Data Analysis"],
                ["JavaScript", "React", "Node.js", "MongoDB"],
                ["Java", "Spring Boot", "PostgreSQL", "AWS"],
                ["C#", ".NET", "Azure", "SQL Server"],
                ["PHP", "Laravel", "MySQL", "Docker"],
                ["Go", "Kubernetes", "DevOps", "CI/CD"],
                ["Ruby", "Rails", "Redis", "API Design"],
                ["Swift", "iOS Development", "Mobile", "UI/UX"]
            ]
            
            sample_roles = [
                "Software Engineer", "Data Scientist", "DevOps Engineer",
                "Full Stack Developer", "Machine Learning Engineer",
                "Backend Developer", "Frontend Developer", "Mobile Developer"
            ]
            
            sample_locations = [
                "San Francisco, CA", "New York, NY", "Austin, TX",
                "Seattle, WA", "Boston, MA", "Chicago, IL",
                "Los Angeles, CA", "Denver, CO", "Remote"
            ]
            
            user_ids = []
            for i in range(num_users):
                user_id = str(uuid.uuid4())
                user_ids.append(user_id)
                
                profile = {
                    'id': user_id,
                    'email': f'user{i+1}@example.com',
                    'full_name': f'User {i+1}',
                    'skills': json.dumps(random.choice(sample_skills)),
                    'experience_years': random.randint(1, 15),
                    'current_role': random.choice(sample_roles),
                    'location': random.choice(sample_locations),
                    'ai_score': round(random.uniform(0.6, 0.95), 2),
                    'profile_completeness': round(random.uniform(0.7, 1.0), 2)
                }
                
                cursor.execute('''
                    INSERT OR REPLACE INTO user_profiles 
                    (id, email, full_name, skills, experience_years, current_role, 
                     location, ai_score, profile_completeness)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', tuple(profile.values()))
            
            # Generate CV documents
            for user_id in user_ids[:30]:  # 30 users have CVs
                cv_id = str(uuid.uuid4())
                cv_data = {
                    'id': cv_id,
                    'user_id': user_id,
                    'filename': f'resume_{user_id[:8]}.pdf',
                    'file_size': random.randint(100000, 2000000),
                    'processing_status': random.choice(['completed', 'pending', 'processing']),
                    'ai_analysis': json.dumps({
                        'experience_level': random.choice(['junior', 'mid', 'senior']),
                        'domain_expertise': random.choice(['tech', 'finance', 'healthcare']),
                        'soft_skills': ['communication', 'leadership', 'teamwork']
                    }),
                    'skills_extracted': json.dumps(random.choice(sample_skills)),
                    'confidence_score': round(random.uniform(0.7, 0.95), 2)
                }
                
                cursor.execute('''
                    INSERT OR REPLACE INTO cv_documents 
                    (id, user_id, filename, file_size, processing_status, 
                     ai_analysis, skills_extracted, confidence_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', tuple(cv_data.values()))
            
            # Generate job postings
            sample_companies = [
                "TechCorp", "DataFlow Inc", "CloudSystems", "AI Innovations",
                "StartupXYZ", "Enterprise Solutions", "Future Tech", "DevMasters"
            ]
            
            for i in range(20):
                job_id = str(uuid.uuid4())
                job_data = {
                    'id': job_id,
                    'title': random.choice(sample_roles),
                    'company': random.choice(sample_companies),
                    'location': random.choice(sample_locations),
                    'salary_min': random.randint(60000, 120000),
                    'salary_max': random.randint(120000, 200000),
                    'required_skills': json.dumps(random.choice(sample_skills)),
                    'description': f'Join our team as a {random.choice(sample_roles)}...',
                    'ai_requirements': json.dumps({
                        'min_experience': random.randint(2, 8),
                        'education': random.choice(['bachelor', 'master', 'any']),
                        'remote_friendly': random.choice([True, False])
                    })
                }
                
                cursor.execute('''
                    INSERT OR REPLACE INTO job_postings 
                    (id, title, company, location, salary_min, salary_max, 
                     required_skills, description, ai_requirements)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', tuple(job_data.values()))
            
            # Generate system metrics
            metrics_types = [
                'cpu_usage', 'memory_usage', 'disk_usage', 'api_response_time',
                'active_users', 'processing_queue_size', 'error_rate'
            ]
            
            services = ['admin_portal', 'user_portal', 'backend_api', 'ai_engine']
            
            for _ in range(100):
                metric_id = str(uuid.uuid4())
                metric_data = {
                    'id': metric_id,
                    'metric_type': random.choice(metrics_types),
                    'metric_value': round(random.uniform(0.1, 100.0), 2),
                    'service_name': random.choice(services),
                    'metadata': json.dumps({
                        'environment': 'production',
                        'version': '1.0.0'
                    })
                }
                
                cursor.execute('''
                    INSERT OR REPLACE INTO system_metrics 
                    (id, metric_type, metric_value, service_name, metadata)
                    VALUES (?, ?, ?, ?, ?)
                ''', tuple(metric_data.values()))
            
            # Generate AI processing queue
            task_types = [
                'cv_analysis', 'skill_extraction', 'job_matching', 
                'market_analysis', 'candidate_scoring'
            ]
            
            for i in range(15):
                task_id = str(uuid.uuid4())
                task_data = {
                    'id': task_id,
                    'task_type': random.choice(task_types),
                    'input_data': json.dumps({'user_id': random.choice(user_ids)}),
                    'status': random.choice(['pending', 'processing', 'completed', 'failed']),
                    'priority': random.randint(1, 10),
                    'result_data': json.dumps({
                        'processing_time': random.randint(100, 5000),
                        'confidence': round(random.uniform(0.6, 0.95), 2)
                    })
                }
                
                cursor.execute('''
                    INSERT OR REPLACE INTO ai_processing_queue 
                    (id, task_type, input_data, status, priority, result_data)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', tuple(task_data.values()))
            
            conn.commit()
            self.logger.info(f"Sample data generated successfully")
    
    def load_existing_data(self):
        """Load data from existing AI enrichment files."""
        if not self.existing_data_path or not self.existing_data_path.exists():
            self.logger.warning(f"Existing data path not found: {self.existing_data_path}")
            self.logger.info("Falling back to sample data generation...")
            self.generate_sample_data()
            return
        
        self.logger.info(f"Loading existing data from: {self.existing_data_path}")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Load AI enriched profiles
            self._load_ai_profiles(cursor)
            
            # Load company database
            self._load_companies(cursor)
            
            # Load market intelligence
            self._load_market_intelligence(cursor)
            
            # Load normalized profiles
            self._load_normalized_profiles(cursor)
            
            conn.commit()
            self.logger.info("Existing data loaded successfully")
    
    def _load_ai_profiles(self, cursor):
        """Load AI enriched profiles from JSON file."""
        ai_profiles_path = self.existing_data_path / "ai" / "ai_enriched_profiles.json"
        
        if not ai_profiles_path.exists():
            self.logger.warning(f"AI profiles file not found: {ai_profiles_path}")
            return
        
        with open(ai_profiles_path, 'r', encoding='utf-8') as f:
            profiles_data = json.load(f)
        
        self.logger.info(f"Loading {len(profiles_data)} AI enriched profiles...")
        
        for file_id, profile in profiles_data.items():
            # Insert into user_profiles table
            user_profile = {
                'id': file_id,
                'email': f"{file_id}@extracted.cv",
                'full_name': profile.get('names', ['Unknown'])[0] if profile.get('names') else 'Unknown',
                'skills': json.dumps(profile.get('skills', [])),
                'experience_years': profile.get('experience_years', 0),
                'current_role': profile.get('title', 'Unknown'),
                'location': profile.get('location', 'Unknown'),
                'ai_score': profile.get('ai_final_score', 0.0),
                'profile_completeness': min(1.0, len(profile.get('skills', [])) / 10.0),
                'created_at': profile.get('ai_processed_at', datetime.now().isoformat()),
                'metadata': json.dumps({
                    'source_path': profile.get('source_path', ''),
                    'career_stage': profile.get('career_stage', ''),
                    'industries': profile.get('industries', []),
                    'ai_scores': profile.get('ai_scores', {})
                })
            }
            
            cursor.execute('''
                INSERT OR REPLACE INTO user_profiles 
                (id, email, full_name, skills, experience_years, current_role, 
                 location, ai_score, profile_completeness, created_at, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', tuple(user_profile.values()))
            
            # Insert into cv_documents table
            cv_document = {
                'id': f"cv_{file_id}",
                'user_id': file_id,
                'filename': os.path.basename(profile.get('source_path', f'{file_id}.pdf')),
                'file_size': len(profile.get('text', '')) * 8,  # Estimate file size
                'processing_status': 'completed',
                'ai_analysis': json.dumps({
                    'experience_level': profile.get('career_stage', 'unknown'),
                    'industries': profile.get('industries', []),
                    'confidence': profile.get('ai_final_score', 0.0)
                }),
                'skills_extracted': json.dumps(profile.get('skills', [])),
                'confidence_score': profile.get('ai_final_score', 0.0),
                'extracted_text': profile.get('text', '')[:5000]  # Truncate for storage
            }
            
            cursor.execute('''
                INSERT OR REPLACE INTO cv_documents 
                (id, user_id, filename, file_size, processing_status, 
                 ai_analysis, skills_extracted, confidence_score, extracted_text)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', tuple(cv_document.values()))
    
    def _load_companies(self, cursor):
        """Load companies database from JSON file."""
        companies_path = self.existing_data_path / "companies" / "companies_database.json"
        
        if not companies_path.exists():
            self.logger.warning(f"Companies file not found: {companies_path}")
            return
        
        with open(companies_path, 'r', encoding='utf-8') as f:
            companies_data = json.load(f)
        
        self.logger.info(f"Loading {len(companies_data)} companies...")
        
        for comp_id, company in companies_data.items():
            # Insert market intelligence data
            intelligence_data = {
                'id': f"intel_{comp_id}",
                'data_type': 'company_profile',
                'content': json.dumps({
                    'name': company.get('name', ''),
                    'industries': company.get('industries', []),
                    'estimated_size': company.get('estimated_size', 'unknown'),
                    'occurrence_count': company.get('occurrence_count', 0),
                    'confidence': company.get('confidence', 0.0)
                }),
                'confidence_score': company.get('confidence', 0.0),
                'source': company.get('source', 'text_extraction'),
                'created_at': company.get('created_at', datetime.now().isoformat())
            }
            
            cursor.execute('''
                INSERT OR REPLACE INTO market_intelligence 
                (id, data_type, content, confidence_score, source, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', tuple(intelligence_data.values()))
    
    def _load_market_intelligence(self, cursor):
        """Load market intelligence from JSON file."""
        market_intel_path = self.existing_data_path / "ai" / "market_intelligence.json"
        
        if not market_intel_path.exists():
            self.logger.warning(f"Market intelligence file not found: {market_intel_path}")
            return
        
        with open(market_intel_path, 'r', encoding='utf-8') as f:
            market_data = json.load(f)
        
        self.logger.info("Loading market intelligence data...")
        
        # Load hot skills data
        if 'market_trends' in market_data and 'hot_skills_2025' in market_data['market_trends']:
            for skill_data in market_data['market_trends']['hot_skills_2025']:
                intel_data = {
                    'id': f"skill_{skill_data['skill'].lower().replace(' ', '_')}",
                    'data_type': 'hot_skill',
                    'content': json.dumps(skill_data),
                    'confidence_score': 0.9,
                    'source': 'market_analysis',
                    'created_at': market_data.get('last_updated', datetime.now().isoformat())
                }
                
                cursor.execute('''
                    INSERT OR REPLACE INTO market_intelligence 
                    (id, data_type, content, confidence_score, source, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', tuple(intel_data.values()))
    
    def _load_normalized_profiles(self, cursor):
        """Load normalized profile files."""
        normalized_path = self.existing_data_path / "normalized"
        
        if not normalized_path.exists():
            self.logger.warning(f"Normalized profiles path not found: {normalized_path}")
            return
        
        # Get all JSON files in normalized directory
        json_files = list(normalized_path.glob("*.json"))
        self.logger.info(f"Found {len(json_files)} normalized profile files")
        
        # Load a sample of files to avoid overwhelming the database
        sample_files = json_files[:100]  # Load first 100 files
        
        for json_file in sample_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    profile_data = json.load(f)
                
                file_id = json_file.stem
                
                # Create audit log entry
                audit_entry = {
                    'id': f"audit_{file_id}",
                    'user_id': 'admin',
                    'action': 'profile_loaded',
                    'resource_type': 'normalized_profile',
                    'resource_id': file_id,
                    'details': json.dumps({
                        'filename': json_file.name,
                        'source': 'existing_data_load'
                    }),
                    'ip_address': '127.0.0.1',
                    'user_agent': 'IntelliCV-DataLoader/1.0'
                }
                
                cursor.execute('''
                    INSERT OR REPLACE INTO audit_logs 
                    (id, user_id, action, resource_type, resource_id, details, ip_address, user_agent)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', tuple(audit_entry.values()))
                
            except Exception as e:
                self.logger.warning(f"Error loading {json_file}: {e}")
                continue
    
    def export_to_json(self):
        """Export database data to JSON files for AI component consumption."""
        self.logger.info("Exporting data to JSON files...")
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Export user profiles with normalized structure
            cursor.execute('SELECT * FROM user_profiles')
            users = cursor.fetchall()
            
            for user in users:
                user_dict = dict(user)
                # Parse JSON fields
                if user_dict['skills']:
                    user_dict['skills'] = json.loads(user_dict['skills'])
                
                # Export to normalized format
                normalized_path = self.json_export_path / "normalized" / f"{user_dict['id']}.json"
                with open(normalized_path, 'w') as f:
                    json.dump(user_dict, f, indent=2, default=str)
                
                # Export to frontend format
                frontend_user_data = {
                    'id': user_dict['id'],
                    'profile': {
                        'email': user_dict['email'],
                        'full_name': user_dict['full_name'],
                        'current_role': user_dict['current_role'],
                        'location': user_dict['location'],
                        'experience_years': user_dict['experience_years']
                    },
                    'skills': user_dict['skills'] or [],
                    'ai_metrics': {
                        'ai_score': user_dict['ai_score'],
                        'profile_completeness': user_dict['profile_completeness']
                    },
                    'last_updated': user_dict['updated_at']
                }
                
                frontend_path = self.frontend_data_path / "users" / f"{user_dict['id']}.json"
                with open(frontend_path, 'w') as f:
                    json.dump(frontend_user_data, f, indent=2, default=str)
            
            # Export system metrics
            cursor.execute('''
                SELECT metric_type, AVG(metric_value) as avg_value, 
                       COUNT(*) as count, service_name
                FROM system_metrics 
                GROUP BY metric_type, service_name
            ''')
            metrics = cursor.fetchall()
            
            metrics_data = {
                'system_health': {
                    'overall_status': 'healthy',
                    'last_updated': datetime.now().isoformat(),
                    'metrics': {}
                }
            }
            
            for metric in metrics:
                metric_dict = dict(metric)
                service = metric_dict['service_name'] or 'general'
                if service not in metrics_data['system_health']['metrics']:
                    metrics_data['system_health']['metrics'][service] = {}
                
                metrics_data['system_health']['metrics'][service][metric_dict['metric_type']] = {
                    'value': round(metric_dict['avg_value'], 2),
                    'sample_count': metric_dict['count']
                }
            
            # Export admin updates
            admin_updates = {
                'updates': [
                    {
                        'id': str(uuid.uuid4()),
                        'title': 'System Performance Optimized',
                        'message': 'AI processing speed improved by 25%',
                        'type': 'success',
                        'timestamp': (datetime.now() - timedelta(hours=2)).isoformat()
                    },
                    {
                        'id': str(uuid.uuid4()),
                        'title': 'New Users Registered',
                        'message': f'{len(users)} active users in the system',
                        'type': 'info',
                        'timestamp': (datetime.now() - timedelta(hours=1)).isoformat()
                    }
                ],
                'generated_at': datetime.now().isoformat()
            }
            
            admin_updates_path = self.frontend_data_path / "admin_updates.json"
            with open(admin_updates_path, 'w') as f:
                json.dump(admin_updates, f, indent=2, default=str)
            
            # Export market intelligence data
            cursor.execute('SELECT * FROM market_intelligence')
            market_data = cursor.fetchall()
            
            market_intelligence = {
                'market_trends': {
                    'high_demand_skills': ["Python", "AI/ML", "Cloud Computing", "Data Analysis"],
                    'emerging_technologies': ["GenAI", "Quantum Computing", "Edge AI", "Web3"],
                    'industry_growth': {
                        'technology': 0.15,
                        'healthcare': 0.12,
                        'finance': 0.08
                    }
                },
                'salary_insights': {
                    'average_ranges': {
                        'junior': {'min': 60000, 'max': 80000},
                        'mid': {'min': 80000, 'max': 120000},
                        'senior': {'min': 120000, 'max': 180000}
                    }
                },
                'generated_at': datetime.now().isoformat()
            }
            
            market_path = self.json_export_path / "market_intelligence.json"
            with open(market_path, 'w') as f:
                json.dump(market_intelligence, f, indent=2, default=str)
            
            self.logger.info("JSON export completed successfully")
    
    def verify_data_links(self) -> Dict[str, bool]:
        """Verify all data links are working and files exist."""
        verification_results = {}
        
        # Check database
        verification_results['database_exists'] = self.db_path.exists()
        
        # Check JSON exports
        verification_results['json_export_dir'] = self.json_export_path.exists()
        verification_results['frontend_data_dir'] = self.frontend_data_path.exists()
        
        # Count generated files
        normalized_files = list((self.json_export_path / "normalized").glob("*.json"))
        user_files = list((self.frontend_data_path / "users").glob("*.json"))
        
        verification_results['normalized_user_files'] = len(normalized_files)
        verification_results['frontend_user_files'] = len(user_files)
        verification_results['admin_updates_exists'] = (self.frontend_data_path / "admin_updates.json").exists()
        verification_results['market_intelligence_exists'] = (self.json_export_path / "market_intelligence.json").exists()
        
        # Check database tables
        if verification_results['database_exists']:
            try:
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("SELECT COUNT(*) FROM user_profiles")
                    verification_results['user_profiles_count'] = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM cv_documents")
                    verification_results['cv_documents_count'] = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM system_metrics")
                    verification_results['system_metrics_count'] = cursor.fetchone()[0]
                    
                    cursor.execute("SELECT COUNT(*) FROM ai_processing_queue")
                    verification_results['ai_queue_count'] = cursor.fetchone()[0]
            except Exception as e:
                verification_results['database_error'] = str(e)
        
        return verification_results
    
    def get_dashboard_data_summary(self) -> Dict[str, Any]:
        """Get summary data for dashboard display."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Basic counts
            cursor.execute("SELECT COUNT(*) FROM user_profiles")
            total_users = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM cv_documents WHERE processing_status = 'completed'")
            processed_cvs = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM ai_processing_queue WHERE status = 'completed'")
            ai_tasks_completed = cursor.fetchone()[0]
            
            cursor.execute("SELECT AVG(ai_score) FROM user_profiles WHERE ai_score IS NOT NULL")
            avg_ai_score = cursor.fetchone()[0] or 0
            
            # Recent activity
            cursor.execute('''
                SELECT 'CV Processed' as activity, filename as details, upload_date as timestamp
                FROM cv_documents 
                WHERE processing_status = 'completed' 
                ORDER BY upload_date DESC LIMIT 5
            ''')
            recent_activity = cursor.fetchall()
            
            return {
                'metrics': {
                    'total_users': total_users,
                    'processed_cvs': processed_cvs,
                    'ai_tasks_completed': ai_tasks_completed,
                    'avg_ai_score': round(avg_ai_score, 2),
                    'system_health': '98%'
                },
                'recent_activity': [
                    {
                        'activity': row[0],
                        'details': row[1],
                        'timestamp': row[2],
                        'status': '✅'
                    } for row in recent_activity
                ]
            }


def initialize_data_system(use_existing_data: bool = True):
    """Initialize the complete data system for the admin dashboard."""
    generator = IntelliCVDataGenerator()
    
    # Load existing data or generate sample data
    if use_existing_data:
        generator.load_existing_data()
    else:
        generator.generate_sample_data(num_users=50)
    
    # Export to JSON
    generator.export_to_json()
    
    # Verify links
    verification = generator.verify_data_links()
    
    return generator, verification


if __name__ == "__main__":
    generator, verification = initialize_data_system(use_existing_data=True)
    print("Existing Data Integration Complete!")
    print(f"Verification Results: {verification}")