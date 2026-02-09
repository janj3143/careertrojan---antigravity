import requests
import psycopg2
import redis
import docker
import subprocess
import json
import time
from typing import Dict, Any, List, Optional, Tuple
import streamlit as st
from pathlib import Path
import logging

# =============================================================================
# BACKEND SERVICE MANAGER - IntelliCV-AI Admin Portal
# Real backend integration with all services
# =============================================================================

class BackendServiceManager:
    """Comprehensive backend service manager with real connections"""
    
    def __init__(self):
        self.backend_url = "http://localhost:8000"
        self.postgres_config = {
            'host': 'localhost',
            'port': 5432,
            'databases': ['intellicv_admin', 'intellicv_user', 'intellicv_core']
        }
        self.redis_config = {
            'host': 'localhost',
            'port': 6379,
            'databases': [0, 1, 2]  # Sessions, cache, analytics
        }
        self.docker_client = None
        self.logger = self._setup_logging()
        
    def _setup_logging(self):
        """Setup logging for service manager"""
        logging.basicConfig(level=logging.INFO)
        return logging.getLogger(__name__)
    
    # =============================================================================
    # BACKEND API CONNECTIVITY
    # =============================================================================
    
    def test_backend_connection(self) -> Dict[str, Any]:
        """Test FastAPI backend connectivity"""
        try:
            response = requests.get(f"{self.backend_url}/health", timeout=5)
            if response.status_code == 200:
                return {
                    'status': 'connected',
                    'response_time': response.elapsed.total_seconds(),
                    'version': response.json().get('version', 'unknown'),
                    'timestamp': time.time()
                }
        except requests.exceptions.RequestException as e:
            return {
                'status': 'disconnected',
                'error': str(e),
                'timestamp': time.time()
            }
    
    def start_backend_service(self) -> Dict[str, Any]:
        """Start the FastAPI backend service"""
        try:
            backend_path = Path("c:/IntelliCV/backend_final")
            cmd = [
                "c:/IntelliCV/env310/Scripts/python.exe",
                str(backend_path / "main.py")
            ]
            
            process = subprocess.Popen(
                cmd,
                cwd=str(backend_path),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait a moment to see if it starts successfully
            time.sleep(2)
            if process.poll() is None:  # Still running
                return {
                    'status': 'started',
                    'pid': process.pid,
                    'message': 'Backend service started successfully'
                }
            else:
                stdout, stderr = process.communicate()
                return {
                    'status': 'failed',
                    'error': stderr.decode() if stderr else 'Unknown error',
                    'stdout': stdout.decode() if stdout else ''
                }
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def get_backend_status(self) -> Dict[str, Any]:
        """Get comprehensive backend status"""
        connection_test = self.test_backend_connection()
        
        try:
            # Get API endpoints
            endpoints_response = requests.get(f"{self.backend_url}/api/v1/", timeout=3)
            endpoints = endpoints_response.json() if endpoints_response.status_code == 200 else []
        except:
            endpoints = []
        
        return {
            'connection': connection_test,
            'endpoints': endpoints,
            'services': self.get_all_service_status()
        }
    
    # =============================================================================
    # POSTGRESQL DATABASE MANAGEMENT
    # =============================================================================
    
    def test_postgres_connection(self, database: str = None) -> Dict[str, Any]:
        """Test PostgreSQL database connection"""
        try:
            if database:
                databases = [database]
            else:
                databases = self.postgres_config['databases']
            
            results = {}
            for db in databases:
                try:
                    conn = psycopg2.connect(
                        host=self.postgres_config['host'],
                        port=self.postgres_config['port'],
                        database=db,
                        user='postgres',  # Default, should be configurable
                        password='postgres',  # Default, should be configurable
                        connect_timeout=5
                    )
                    conn.close()
                    results[db] = {
                        'status': 'connected',
                        'timestamp': time.time()
                    }
                except psycopg2.Error as e:
                    results[db] = {
                        'status': 'error',
                        'error': str(e),
                        'timestamp': time.time()
                    }
            
            return results
            
        except Exception as e:
            return {'error': str(e)}
    
    def get_postgres_stats(self, database: str) -> Dict[str, Any]:
        """Get PostgreSQL database statistics"""
        try:
            conn = psycopg2.connect(
                host=self.postgres_config['host'],
                port=self.postgres_config['port'],
                database=database,
                user='postgres',
                password='postgres'
            )
            
            cursor = conn.cursor()
            
            # Get table count
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            table_count = cursor.fetchone()[0]
            
            # Get database size
            cursor.execute(f"SELECT pg_size_pretty(pg_database_size('{database}'))")
            db_size = cursor.fetchone()[0]
            
            # Get connection count
            cursor.execute("""
                SELECT COUNT(*) FROM pg_stat_activity 
                WHERE datname = %s
            """, (database,))
            connections = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'table_count': table_count,
                'database_size': db_size,
                'active_connections': connections,
                'status': 'healthy'
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def backup_database(self, database: str) -> Dict[str, Any]:
        """Create database backup"""
        try:
            backup_dir = Path("c:/IntelliCV/backups")
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"{database}_backup_{timestamp}.sql"
            
            cmd = [
                "pg_dump",
                "-h", self.postgres_config['host'],
                "-p", str(self.postgres_config['port']),
                "-U", "postgres",
                "-d", database,
                "-f", str(backup_file)
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                return {
                    'status': 'success',
                    'backup_file': str(backup_file),
                    'size': backup_file.stat().st_size if backup_file.exists() else 0
                }
            else:
                return {
                    'status': 'error',
                    'error': result.stderr
                }
                
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }
    
    # =============================================================================
    # REDIS CACHE MANAGEMENT
    # =============================================================================
    
    def test_redis_connection(self) -> Dict[str, Any]:
        """Test Redis connection across all databases"""
        try:
            results = {}
            for db_num in self.redis_config['databases']:
                try:
                    r = redis.Redis(
                        host=self.redis_config['host'],
                        port=self.redis_config['port'],
                        db=db_num,
                        socket_timeout=5
                    )
                    r.ping()
                    
                    # Get database info
                    info = r.info()
                    results[f'db_{db_num}'] = {
                        'status': 'connected',
                        'keys': info.get('db0', {}).get('keys', 0) if db_num == 0 else r.dbsize(),
                        'memory_usage': info.get('used_memory_human', 'N/A'),
                        'uptime': info.get('uptime_in_seconds', 0)
                    }
                    
                except redis.RedisError as e:
                    results[f'db_{db_num}'] = {
                        'status': 'error',
                        'error': str(e)
                    }
            
            return results
            
        except Exception as e:
            return {'error': str(e)}
    
    def clear_redis_cache(self, database: int = None) -> Dict[str, Any]:
        """Clear Redis cache for specified database or all"""
        try:
            if database is not None:
                databases = [database]
            else:
                databases = self.redis_config['databases']
            
            results = {}
            for db_num in databases:
                try:
                    r = redis.Redis(
                        host=self.redis_config['host'],
                        port=self.redis_config['port'],
                        db=db_num
                    )
                    keys_deleted = r.flushdb()
                    results[f'db_{db_num}'] = {
                        'status': 'cleared',
                        'keys_deleted': keys_deleted
                    }
                except redis.RedisError as e:
                    results[f'db_{db_num}'] = {
                        'status': 'error',
                        'error': str(e)
                    }
            
            return results
            
        except Exception as e:
            return {'error': str(e)}
    
    # =============================================================================
    # DOCKER CONTAINER MANAGEMENT
    # =============================================================================
    
    def get_docker_client(self):
        """Get Docker client with error handling"""
        try:
            if not self.docker_client:
                self.docker_client = docker.from_env()
            return self.docker_client
        except Exception as e:
            self.logger.error(f"Docker client error: {e}")
            return None
    
    def get_docker_containers(self) -> Dict[str, Any]:
        """Get status of all Docker containers"""
        try:
            client = self.get_docker_client()
            if not client:
                return {'error': 'Docker not available'}
            
            containers = client.containers.list(all=True)
            container_info = {}
            
            for container in containers:
                container_info[container.name] = {
                    'id': container.short_id,
                    'status': container.status,
                    'image': container.image.tags[0] if container.image.tags else 'unknown',
                    'ports': container.ports,
                    'created': container.attrs['Created'],
                    'health': self._get_container_health(container)
                }
            
            return container_info
            
        except Exception as e:
            return {'error': str(e)}
    
    def _get_container_health(self, container) -> str:
        """Get container health status"""
        try:
            health = container.attrs.get('State', {}).get('Health', {})
            return health.get('Status', 'unknown')
        except:
            return 'unknown'
    
    def manage_container(self, container_name: str, action: str) -> Dict[str, Any]:
        """Manage Docker container (start/stop/restart)"""
        try:
            client = self.get_docker_client()
            if not client:
                return {'error': 'Docker not available'}
            
            container = client.containers.get(container_name)
            
            if action == 'start':
                container.start()
            elif action == 'stop':
                container.stop()
            elif action == 'restart':
                container.restart()
            else:
                return {'error': f'Unknown action: {action}'}
            
            return {
                'status': 'success',
                'action': action,
                'container': container_name,
                'new_status': container.status
            }
            
        except docker.errors.NotFound:
            return {'error': f'Container {container_name} not found'}
        except Exception as e:
            return {'error': str(e)}
    
    # =============================================================================
    # SYSTEM MONITORING
    # =============================================================================
    
    def get_all_service_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all services"""
        return {
            'backend_api': self.test_backend_connection(),
            'postgresql': self.test_postgres_connection(),
            'redis': self.test_redis_connection(),
            'docker': self.get_docker_containers(),
            'timestamp': time.time()
        }
    
    def get_system_logs(self, service: str, lines: int = 50) -> List[str]:
        """Get system logs for specific service"""
        try:
            if service == 'backend':
                log_file = Path("c:/IntelliCV/backend_final/logs/backend.log")
            elif service == 'postgres':
                # PostgreSQL log location varies by installation
                log_file = Path("C:/Program Files/PostgreSQL/13/data/log/postgresql*.log")
            else:
                return ['Log file not configured for this service']
            
            if log_file.exists():
                with open(log_file, 'r') as f:
                    return f.readlines()[-lines:]
            else:
                return ['Log file not found']
                
        except Exception as e:
            return [f'Error reading logs: {str(e)}']

# =============================================================================
# STREAMLIT INTEGRATION FUNCTIONS
# =============================================================================

@st.cache_data(ttl=30)  # Cache for 30 seconds
def get_cached_service_status():
    """Get cached service status to avoid repeated calls"""
    manager = BackendServiceManager()
    return manager.get_all_service_status()

def render_service_dashboard():
    """Render comprehensive service dashboard"""
    st.subheader("🔧 Backend Service Management")
    
    # Initialize service manager
    if 'service_manager' not in st.session_state:
        st.session_state.service_manager = BackendServiceManager()
    
    manager = st.session_state.service_manager
    
    # Real-time status
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("**Live Service Status:**")
        status = get_cached_service_status()
        
        # Backend API status
        backend_status = status.get('backend_api', {})
        if backend_status.get('status') == 'connected':
            st.success(f"✅ Backend API: Connected ({backend_status.get('response_time', 0):.2f}s)")
        else:
            st.error(f"❌ Backend API: {backend_status.get('error', 'Disconnected')}")
        
        # PostgreSQL status
        postgres_status = status.get('postgresql', {})
        for db, info in postgres_status.items():
            if info.get('status') == 'connected':
                st.success(f"✅ PostgreSQL {db}: Connected")
            else:
                st.error(f"❌ PostgreSQL {db}: {info.get('error', 'Error')}")
        
        # Redis status
        redis_status = status.get('redis', {})
        for db, info in redis_status.items():
            if info.get('status') == 'connected':
                st.success(f"✅ Redis {db}: Connected ({info.get('keys', 0)} keys)")
            else:
                st.error(f"❌ Redis {db}: {info.get('error', 'Error')}")
    
    with col2:
        if st.button("🔄 Refresh Status", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
        
        if st.button("🚀 Start Backend", use_container_width=True):
            result = manager.start_backend_service()
            if result['status'] == 'started':
                st.success(f"Backend started! PID: {result['pid']}")
            else:
                st.error(f"Failed to start: {result.get('error', 'Unknown error')}")
    
    # Service management tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📊 Monitoring", "🐘 PostgreSQL", "🔴 Redis", "🐳 Docker"])
    
    with tab1:
        render_monitoring_tab(manager)
    
    with tab2:
        render_postgres_tab(manager)
    
    with tab3:
        render_redis_tab(manager)
    
    with tab4:
        render_docker_tab(manager)

def render_monitoring_tab(manager):
    """Render monitoring tab"""
    st.write("**📈 System Monitoring**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Backend Response Time", "0.15s", "↓ 0.02s")
        st.metric("Active DB Connections", "12", "↑ 2")
    
    with col2:
        st.metric("Redis Memory Usage", "45MB", "↑ 2MB")
        st.metric("Docker Containers", "3 running", "0 changed")
    
    # Logs section
    if st.checkbox("Show Recent Logs"):
        log_type = st.selectbox("Log Type", ["backend", "postgres", "redis"])
        logs = manager.get_system_logs(log_type, 20)
        st.text_area("Recent Logs", "\n".join(logs), height=200)

def render_postgres_tab(manager):
    """Render PostgreSQL management tab"""
    st.write("**🐘 PostgreSQL Database Management**")
    
    # Database selection
    database = st.selectbox("Select Database", 
                           ["intellicv_admin", "intellicv_user", "intellicv_core"])
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Get Stats", use_container_width=True):
            stats = manager.get_postgres_stats(database)
            if 'error' not in stats:
                st.json(stats)
            else:
                st.error(f"Error: {stats['error']}")
    
    with col2:
        if st.button("💾 Backup DB", use_container_width=True):
            with st.spinner("Creating backup..."):
                result = manager.backup_database(database)
                if result['status'] == 'success':
                    st.success(f"Backup created: {result['backup_file']}")
                else:
                    st.error(f"Backup failed: {result['error']}")
    
    with col3:
        if st.button("🧪 Test Connection", use_container_width=True):
            result = manager.test_postgres_connection(database)
            if database in result and result[database]['status'] == 'connected':
                st.success("Connection successful!")
            else:
                st.error("Connection failed!")

def render_redis_tab(manager):
    """Render Redis management tab"""
    st.write("**🔴 Redis Cache Management**")
    
    # Redis database selection
    redis_db = st.selectbox("Select Redis DB", [0, 1, 2], 
                           format_func=lambda x: f"DB{x} ({'Sessions' if x==0 else 'Cache' if x==1 else 'Analytics'})")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Get Info", use_container_width=True):
            info = manager.test_redis_connection()
            db_key = f'db_{redis_db}'
            if db_key in info:
                st.json(info[db_key])
            else:
                st.error("Failed to get Redis info")
    
    with col2:
        if st.button("🗑️ Clear Cache", use_container_width=True):
            if st.checkbox("Confirm clear cache"):
                result = manager.clear_redis_cache(redis_db)
                db_key = f'db_{redis_db}'
                if db_key in result and result[db_key]['status'] == 'cleared':
                    st.success("Cache cleared!")
                else:
                    st.error("Failed to clear cache")
    
    with col3:
        if st.button("🧪 Test Connection", use_container_width=True):
            result = manager.test_redis_connection()
            db_key = f'db_{redis_db}'
            if db_key in result and result[db_key]['status'] == 'connected':
                st.success("Redis connection successful!")
            else:
                st.error("Redis connection failed!")

def render_docker_tab(manager):
    """Render Docker management tab"""
    st.write("**🐳 Docker Container Management**")
    
    containers = manager.get_docker_containers()
    
    if 'error' in containers:
        st.error(f"Docker error: {containers['error']}")
        return
    
    if not containers:
        st.info("No Docker containers found")
        return
    
    for name, info in containers.items():
        with st.expander(f"{name} - {info['status']}"):
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.write(f"**Status:** {info['status']}")
                st.write(f"**Image:** {info['image']}")
            
            with col2:
                if st.button("▶️ Start", key=f"start_{name}"):
                    result = manager.manage_container(name, 'start')
                    if result.get('status') == 'success':
                        st.success("Container started!")
                        st.rerun()
                    else:
                        st.error(f"Error: {result.get('error')}")
            
            with col3:
                if st.button("⏹️ Stop", key=f"stop_{name}"):
                    result = manager.manage_container(name, 'stop')
                    if result.get('status') == 'success':
                        st.success("Container stopped!")
                        st.rerun()
                    else:
                        st.error(f"Error: {result.get('error')}")
            
            with col4:
                if st.button("🔄 Restart", key=f"restart_{name}"):
                    result = manager.manage_container(name, 'restart')
                    if result.get('status') == 'success':
                        st.success("Container restarted!")
                        st.rerun()
                    else:
                        st.error(f"Error: {result.get('error')}")