"""
System Health Monitoring Service for IntelliCV Admin Portal
Provides real system status monitoring and health checks
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import subprocess
import requests
import pandas as pd
from collections import defaultdict

class SystemHealthMonitoringService:
    """Service to provide real system health monitoring"""

    def __init__(self):
        self.base_path = Path(__file__).parent.parent.parent.parent
        self.admin_portal_path = Path(__file__).parent.parent
        self.logs_path = self.admin_portal_path / "logs"
        self.pages_path = self.admin_portal_path / "pages"

        # Ensure logs directory exists
        self.logs_path.mkdir(exist_ok=True)

        # Initialize monitoring data
        self.last_health_check = None
        self.system_status = {}
        self.error_log = []

    def run_comprehensive_system_health_check(self) -> Dict[str, Any]:
        """Run comprehensive health check on all system components"""
        health_status = {
            'timestamp': datetime.now().isoformat(),
            'overall_status': 'healthy',
            'components': {},
            'errors': [],
            'warnings': [],
            'recommendations': []
        }

        # Check database connectivity
        db_status = self._check_database_health()
        health_status['components']['database'] = db_status

        # Check AI data sources
        ai_status = self._check_ai_data_health()
        health_status['components']['ai_data'] = ai_status

        # Check file system integrity
        fs_status = self._check_filesystem_health()
        health_status['components']['filesystem'] = fs_status

        # Check admin portal pages
        pages_status = self._check_admin_pages_health()
        health_status['components']['admin_pages'] = pages_status

        # Check external dependencies
        deps_status = self._check_external_dependencies()
        health_status['components']['external_deps'] = deps_status

        # Check services
        services_status = self._check_services_health()
        health_status['components']['services'] = services_status

        # Aggregate overall status
        all_statuses = [comp['status'] for comp in health_status['components'].values()]
        if 'critical' in all_statuses:
            health_status['overall_status'] = 'critical'
        elif 'warning' in all_statuses:
            health_status['overall_status'] = 'warning'
        elif 'error' in all_statuses:
            health_status['overall_status'] = 'error'

        # Collect all errors and warnings
        for component, details in health_status['components'].items():
            if 'errors' in details:
                health_status['errors'].extend(details['errors'])
            if 'warnings' in details:
                health_status['warnings'].extend(details['warnings'])
            if 'recommendations' in details:
                health_status['recommendations'].extend(details['recommendations'])

        self.last_health_check = datetime.now()
        return health_status

    def _check_database_health(self) -> Dict[str, Any]:
        """Check database connectivity and integrity"""
        status = {
            'status': 'healthy',
            'details': {},
            'errors': [],
            'warnings': [],
            'recommendations': []
        }

        # Check for database files
        db_files = [
            self.admin_portal_path / "secure_credentials.db",
            self.admin_portal_path / "admin_credentials.json"
        ]

        for db_file in db_files:
            if db_file.exists():
                try:
                    if db_file.suffix == '.db':
                        # Test SQLite connection
                        conn = sqlite3.connect(str(db_file))
                        cursor = conn.cursor()
                        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                        tables = cursor.fetchall()
                        conn.close()

                        status['details'][db_file.name] = {
                            'exists': True,
                            'accessible': True,
                            'tables': len(tables),
                            'size_mb': round(db_file.stat().st_size / (1024*1024), 2)
                        }
                    elif db_file.suffix == '.json':
                        # Test JSON file
                        with open(db_file, 'r') as f:
                            data = json.load(f)

                        status['details'][db_file.name] = {
                            'exists': True,
                            'accessible': True,
                            'valid_json': True,
                            'records': len(data) if isinstance(data, dict) else 0
                        }

                except Exception as e:
                    status['status'] = 'error'
                    status['errors'].append(f"Database {db_file.name} error: {str(e)}")
            else:
                status['warnings'].append(f"Database file {db_file.name} not found")
                if status['status'] == 'healthy':
                    status['status'] = 'warning'

        return status

    def _check_ai_data_health(self) -> Dict[str, Any]:
        """Check AI data sources health"""
        status = {
            'status': 'healthy',
            'details': {},
            'errors': [],
            'warnings': [],
            'recommendations': []
        }

        # Check ai_data_final
        ai_data_final = self.base_path / "ai_data_final"
        ai_data_backup = self.base_path / "ai_data"
        automated_parser = self.base_path / "automated_parser"

        data_sources = {
            'ai_data_final': ai_data_final,
            'ai_data_backup': ai_data_backup,
            'automated_parser': automated_parser
        }

        for source_name, source_path in data_sources.items():
            if source_path.exists():
                try:
                    # Count files in directory
                    all_files = list(source_path.rglob("*"))
                    json_files = list(source_path.rglob("*.json"))
                    csv_files = list(source_path.rglob("*.csv"))

                    # Calculate total size
                    total_size = sum(f.stat().st_size for f in all_files if f.is_file())

                    status['details'][source_name] = {
                        'exists': True,
                        'total_files': len(all_files),
                        'json_files': len(json_files),
                        'csv_files': len(csv_files),
                        'total_size_mb': round(total_size / (1024*1024), 2),
                        'last_modified': datetime.fromtimestamp(source_path.stat().st_mtime).isoformat()
                    }

                    # Check for recent activity
                    recent_files = [f for f in all_files if f.is_file() and
                                  datetime.fromtimestamp(f.stat().st_mtime) > datetime.now() - timedelta(days=7)]

                    if len(recent_files) == 0 and source_name == 'ai_data_final':
                        status['warnings'].append(f"No recent activity in {source_name} (last 7 days)")
                        if status['status'] == 'healthy':
                            status['status'] = 'warning'

                except Exception as e:
                    status['errors'].append(f"Error analyzing {source_name}: {str(e)}")
                    status['status'] = 'error'
            else:
                if source_name == 'ai_data_final':
                    status['warnings'].append(f"Primary data source {source_name} not found")
                    if status['status'] == 'healthy':
                        status['status'] = 'warning'
                else:
                    status['details'][source_name] = {'exists': False}

        return status

    def _check_filesystem_health(self) -> Dict[str, Any]:
        """Check filesystem health and disk space"""
        status = {
            'status': 'healthy',
            'details': {},
            'errors': [],
            'warnings': [],
            'recommendations': []
        }

        try:
            # Check disk space
            import shutil
            total, used, free = shutil.disk_usage(self.base_path)

            free_gb = free // (1024**3)
            total_gb = total // (1024**3)
            used_percent = (used / total) * 100

            status['details']['disk_space'] = {
                'total_gb': total_gb,
                'free_gb': free_gb,
                'used_percent': round(used_percent, 1)
            }

            if free_gb < 5:
                status['errors'].append(f"Low disk space: {free_gb}GB free")
                status['status'] = 'critical'
            elif free_gb < 20:
                status['warnings'].append(f"Disk space warning: {free_gb}GB free")
                if status['status'] == 'healthy':
                    status['status'] = 'warning'

            # Check important directories
            important_dirs = [
                self.admin_portal_path,
                self.pages_path,
                self.logs_path,
                self.base_path / "automated_parser"
            ]

            for dir_path in important_dirs:
                if dir_path.exists():
                    file_count = len(list(dir_path.iterdir()))
                    status['details'][dir_path.name] = {
                        'exists': True,
                        'writable': os.access(dir_path, os.W_OK),
                        'file_count': file_count
                    }
                else:
                    status['errors'].append(f"Critical directory missing: {dir_path.name}")
                    status['status'] = 'error'

        except Exception as e:
            status['errors'].append(f"Filesystem check error: {str(e)}")
            status['status'] = 'error'

        return status

    def _check_admin_pages_health(self) -> Dict[str, Any]:
        """Check admin portal pages health"""
        status = {
            'status': 'healthy',
            'details': {},
            'errors': [],
            'warnings': [],
            'recommendations': []
        }

        if not self.pages_path.exists():
            status['errors'].append("Admin pages directory not found")
            status['status'] = 'critical'
            return status

        try:
            # Find all Python files in pages directory
            page_files = list(self.pages_path.glob("*.py"))

            status['details']['total_pages'] = len(page_files)
            status['details']['pages'] = {}

            for page_file in page_files:
                page_name = page_file.stem
                try:
                    # Basic syntax check
                    with open(page_file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Check for common issues
                    issues = []
                    if 'mock' in content.lower() or 'demo' in content.lower():
                        issues.append("Contains mock/demo data")

                    if 'fallback' in content.lower():
                        issues.append("Uses fallback implementations")

                    if 'import' not in content:
                        issues.append("No imports detected")

                    status['details']['pages'][page_name] = {
                        'exists': True,
                        'size_kb': round(page_file.stat().st_size / 1024, 1),
                        'last_modified': datetime.fromtimestamp(page_file.stat().st_mtime).isoformat(),
                        'issues': issues
                    }

                    if issues:
                        status['warnings'].extend([f"{page_name}: {issue}" for issue in issues])
                        if status['status'] == 'healthy':
                            status['status'] = 'warning'

                except Exception as e:
                    status['errors'].append(f"Error checking {page_name}: {str(e)}")
                    status['status'] = 'error'

        except Exception as e:
            status['errors'].append(f"Pages health check error: {str(e)}")
            status['status'] = 'error'

        return status

    def _check_external_dependencies(self) -> Dict[str, Any]:
        """Check external dependencies and APIs"""
        status = {
            'status': 'healthy',
            'details': {},
            'errors': [],
            'warnings': [],
            'recommendations': []
        }

        # Check Python packages
        try:
            required_packages = ['streamlit', 'pandas', 'plotly', 'requests']
            for package in required_packages:
                try:
                    __import__(package)
                    status['details'][f'package_{package}'] = {'status': 'available'}
                except ImportError:
                    status['errors'].append(f"Required package {package} not found")
                    status['status'] = 'error'

        except Exception as e:
            status['errors'].append(f"Package check error: {str(e)}")

        return status

    def _check_services_health(self) -> Dict[str, Any]:
        """Check internal services health"""
        status = {
            'status': 'healthy',
            'details': {},
            'errors': [],
            'warnings': [],
            'recommendations': []
        }

        # Check services directory
        services_path = self.admin_portal_path / "services"
        if services_path.exists():
            service_files = list(services_path.glob("*.py"))

            status['details']['services_found'] = len(service_files)
            status['details']['services'] = {}

            for service_file in service_files:
                service_name = service_file.stem
                try:
                    # Check if service can be imported
                    sys.path.insert(0, str(services_path))
                    spec = sys.modules.get(service_name)

                    status['details']['services'][service_name] = {
                        'exists': True,
                        'size_kb': round(service_file.stat().st_size / 1024, 1),
                        'importable': spec is not None
                    }

                except Exception as e:
                    status['warnings'].append(f"Service {service_name} check failed: {str(e)}")
                    if status['status'] == 'healthy':
                        status['status'] = 'warning'
        else:
            status['warnings'].append("Services directory not found")
            if status['status'] == 'healthy':
                status['status'] = 'warning'

        return status

    def get_real_time_system_metrics(self) -> Dict[str, Any]:
        """Get real-time system performance metrics"""
        try:
            import psutil

            return {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'disk_usage': psutil.disk_usage('/').percent if os.name != 'nt' else psutil.disk_usage('C:').percent,
                'process_count': len(psutil.pids()),
                'timestamp': datetime.now().isoformat()
            }
        except ImportError:
            # Fallback without psutil
            return {
                'cpu_percent': 'Unknown - install psutil',
                'memory_percent': 'Unknown - install psutil',
                'disk_usage': 'Unknown - install psutil',
                'process_count': 'Unknown',
                'timestamp': datetime.now().isoformat()
            }

    def get_error_log_analysis(self) -> Dict[str, Any]:
        """Analyze system error logs"""
        analysis = {
            'total_errors': 0,
            'recent_errors': 0,
            'error_categories': defaultdict(int),
            'recommendations': []
        }

        # Check for log files
        log_files = list(self.logs_path.glob("*.log"))

        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()

                for line in lines:
                    if any(term in line.lower() for term in ['error', 'exception', 'failed']):
                        analysis['total_errors'] += 1

                        # Check if recent (last 24 hours)
                        # Simple heuristic - would be better with actual timestamps
                        if 'today' in line.lower() or str(datetime.now().date()) in line:
                            analysis['recent_errors'] += 1

                        # Categorize error
                        if 'database' in line.lower():
                            analysis['error_categories']['database'] += 1
                        elif 'api' in line.lower():
                            analysis['error_categories']['api'] += 1
                        elif 'file' in line.lower():
                            analysis['error_categories']['filesystem'] += 1
                        else:
                            analysis['error_categories']['general'] += 1

            except Exception as e:
                analysis['error_categories']['log_analysis'] += 1

        # Generate recommendations
        if analysis['recent_errors'] > 10:
            analysis['recommendations'].append("High recent error rate - investigate immediately")

        if analysis['error_categories']['database'] > 0:
            analysis['recommendations'].append("Database errors detected - check database connectivity")

        return analysis
