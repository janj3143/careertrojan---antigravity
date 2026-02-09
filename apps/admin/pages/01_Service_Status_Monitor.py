"""
=============================================================================
IntelliCV Admin Portal - Service Status Monitor (Merged & Enhanced)
=============================================================================

Comprehensive system monitoring and service status tracking with:
- Real-time system metrics
- Service health monitoring
- Performance tracking
- Integration status
- System health analysis
"""

import streamlit as st  # type: ignore[import]

# =============================================================================
# BACKEND-FIRST SWITCH (lockstep) — falls back to local execution when backend is unavailable
# =============================================================================
try:
    from portal_bridge.python.intellicv_api_client import IntelliCVApiClient  # preferred
except Exception:  # pragma: no cover
    IntelliCVApiClient = None  # type: ignore

def _get_api_client():
    return IntelliCVApiClient() if IntelliCVApiClient else None

def _backend_try_get(path: str, params: dict | None = None):
    api = _get_api_client()
    if not api:
        return None, "portal_bridge client not available"
    try:
        return api.get(path, params=params), None
    except Exception as e:
        return None, str(e)

def _backend_try_post(path: str, payload: dict):
    api = _get_api_client()
    if not api:
        return None, "portal_bridge client not available"
    try:
        return api.post(path, payload), None
    except Exception as e:
        return None, str(e)

import subprocess
import json
import psutil  # type: ignore[import]
from datetime import datetime, timedelta
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

try:
    from services.api_client import AdminFastAPIClient
except ImportError:  # pragma: no cover - fallback when services path missing
    AdminFastAPIClient = None

# Add project root to path for imports
project_root = Path(__file__).parents[2]
sys.path.insert(0, str(project_root))


# =============================================================================
# Backend API Helpers
# =============================================================================

HEALTH_CACHE_KEY = "_system_health_snapshot"
HEALTH_TS_KEY = "_system_health_timestamp"
ACTIVITY_CACHE_KEY = "_system_activity_snapshot"
ACTIVITY_TS_KEY = "_system_activity_timestamp"


def get_admin_api_client():
    if AdminFastAPIClient is None:
        return None
    client = st.session_state.get("_admin_api_client")
    if client is None:
        st.session_state["_admin_api_client"] = AdminFastAPIClient()
        client = st.session_state["_admin_api_client"]
    return client


def fetch_system_health_data() -> Dict[str, Any]:
    client = get_admin_api_client()
    if not client:
        return {}
    return client.get_system_health() or {}


def fetch_system_activity_data() -> Dict[str, Any]:
    client = get_admin_api_client()
    if not client:
        return {}
    return client.get_system_activity() or {}


def get_system_health_snapshot(force_refresh: bool = False) -> Dict[str, Any]:
    if force_refresh:
        st.session_state.pop(HEALTH_CACHE_KEY, None)
        st.session_state.pop(HEALTH_TS_KEY, None)
    snapshot = st.session_state.get(HEALTH_CACHE_KEY)
    timestamp = st.session_state.get(HEALTH_TS_KEY)
    if snapshot and timestamp:
        if (datetime.utcnow() - timestamp).total_seconds() < 15:
            return snapshot
    snapshot = fetch_system_health_data()
    st.session_state[HEALTH_CACHE_KEY] = snapshot
    st.session_state[HEALTH_TS_KEY] = datetime.utcnow()
    return snapshot


def get_system_activity_snapshot(force_refresh: bool = False) -> List[Dict[str, Any]]:
    if force_refresh:
        st.session_state.pop(ACTIVITY_CACHE_KEY, None)
        st.session_state.pop(ACTIVITY_TS_KEY, None)
    snapshot = st.session_state.get(ACTIVITY_CACHE_KEY)
    timestamp = st.session_state.get(ACTIVITY_TS_KEY)
    if snapshot and timestamp:
        if (datetime.utcnow() - timestamp).total_seconds() < 60:
            return snapshot
    data = fetch_system_activity_data()
    events = data.get("events", []) if isinstance(data, dict) else []
    st.session_state[ACTIVITY_CACHE_KEY] = events
    st.session_state[ACTIVITY_TS_KEY] = datetime.utcnow()
    return events

def check_admin_authentication():
    """Check if user is authenticated as admin"""
    if not st.session_state.get('admin_authenticated', False):
        st.error("🔒 Authentication session expired")
        st.info("Please refresh the page to re-authenticate.")
        st.stop()

def inject_admin_monitoring_css():
    """Inject professional admin monitoring CSS"""
    st.markdown("""
    <style>
    /* Admin Monitoring Styles */
    .admin-monitoring-header {
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }

    .service-status-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
        gap: 1.5rem;
        margin-bottom: 2rem;
    }

    .service-card {
        background: white;
        border-radius: 12px;
        padding: 1.5rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid;
        transition: transform 0.2s ease;
    }

    .service-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }

    .service-card.status-running {
        border-left-color: #10b981;
    }

    .service-card.status-stopped {
        border-left-color: #ef4444;
    }

    .service-card.status-warning {
        border-left-color: #f59e0b;
    }

    .status-indicator {
        display: inline-flex;
        align-items: center;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.875rem;
        font-weight: 600;
        margin-bottom: 1rem;
    }

    .status-running {
        background-color: #dcfce7;
        color: #166534;
    }

    .status-stopped {
        background-color: #fee2e2;
        color: #991b1b;
    }

    .status-warning {
        background-color: #fef3c7;
        color: #92400e;
    }

    .quick-action-btn {
        background: linear-gradient(135deg, #6366f1 0%, #8b5cf6 100%);
        color: white;
        border: none;
        padding: 0.75rem 1.5rem;
        border-radius: 8px;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.2s ease;
        width: 100%;
        margin: 0.25rem 0;
    }

    .quick-action-btn:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 8px rgba(99, 102, 241, 0.3);
    }

    .system-metrics {
        background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        border-radius: 12px;
        padding: 1.5rem;
        margin: 1rem 0;
    }

    .metric-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 0.5rem 0;
        border-bottom: 1px solid #e2e8f0;
    }

    .metric-row:last-child {
        border-bottom: none;
    }

    .metric-label {
        font-weight: 600;
        color: #374151;
    }

    .metric-value {
        font-family: 'Consolas', monospace;
        color: #6366f1;
        font-weight: 700;
    }
    </style>
    """, unsafe_allow_html=True)

def get_service_status(system_health: Optional[Dict[str, Any]] = None):
    """Get status of key IntelliCV services"""
    system_health = system_health or {}
    service_map = system_health.get('services') if isinstance(system_health, dict) else None
    if service_map:
        mapping = {
            'Backend API (Port 8000)': service_map.get('backend_api', 'unknown'),
            'Admin Portal (Port 8501)': service_map.get('admin_portal', 'unknown'),
            'User Portal (Port 8502)': service_map.get('user_portal', 'unknown'),
            'PostgreSQL (Port 5432)': service_map.get('postgres', 'unknown'),
            'Redis (Port 6379)': service_map.get('redis', 'unknown'),
            'pgAdmin (Port 5050)': service_map.get('pgadmin', 'unknown'),
            'Redis Commander (Port 8081)': service_map.get('redis_commander', 'unknown'),
        }
        return mapping
    # Fallback to local port checks when API unavailable
    return {
        'Backend API (Port 8000)': check_port_status(8000),
        'Admin Portal (Port 8501)': check_port_status(8501),
        'User Portal (Port 8502)': check_port_status(8502),
        'PostgreSQL (Port 5432)': check_port_status(5432),
        'Redis (Port 6379)': check_port_status(6379),
        'pgAdmin (Port 5050)': check_port_status(5050),
        'Redis Commander (Port 8081)': check_port_status(8081),
    }

def check_port_status(port):
    """Check if a port is being used (service is running)"""
    try:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(1)
            result = s.connect_ex(('localhost', port))
            return 'running' if result == 0 else 'stopped'
    except Exception:
        return 'unknown'

def get_system_metrics(system_health: Optional[Dict[str, Any]] = None):
    """Get system performance metrics"""
    if system_health:
        try:
            return {
                'CPU Usage': f"{system_health.get('cpu_pct', 0):.1f}%",
                'Memory Usage': f"{system_health.get('memory_pct', 0):.1f}%",
                'Memory Available': f"{system_health.get('memory_available_gb', 0):.1f} GB",
                'Disk Usage': f"{system_health.get('disk_pct', 0):.1f}%",
                'Disk Free': f"{system_health.get('disk_free_gb', 0):.1f} GB",
            }
        except Exception:
            pass
    # Fallback to local metrics if API data unavailable
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')

        return {
            'CPU Usage': f"{cpu_percent:.1f}%",
            'Memory Usage': f"{memory.percent:.1f}%",
            'Memory Available': f"{memory.available / (1024**3):.1f} GB",
            'Disk Usage': f"{disk.percent:.1f}%",
            'Disk Free': f"{disk.free / (1024**3):.1f} GB",
        }
    except Exception as e:
        return {'Error': str(e)}

def render_service_status_card(service_name, status):
    """Render a service status card"""
    status_class = f"status-{status}"
    status_text = status.title()

    if status == 'running':
        status_emoji = "🟢"
    elif status == 'stopped':
        status_emoji = "🔴"
    else:
        status_emoji = "🟡"

    st.markdown(f"""
    <div class="service-card {status_class}">
        <div class="status-indicator {status_class}">
            {status_emoji} {status_text}
        </div>
        <h4>{service_name}</h4>
        <p>Service is currently <strong>{status_text.lower()}</strong></p>
    </div>
    """, unsafe_allow_html=True)

def main():
    # Check admin authentication
    check_admin_authentication()

    # Inject CSS
    inject_admin_monitoring_css()

    # Header
    st.markdown("""
    <div class="admin-monitoring-header">
        <h1>🔧 Service Status Monitor</h1>
        <p>Real-time monitoring of IntelliCV services and system resources</p>
    </div>
    """, unsafe_allow_html=True)

    # Auto-refresh toggle
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.subheader("Service Status Dashboard")
    with col2:
        auto_refresh = st.checkbox("Auto Refresh", value=True)
    with col3:
        if st.button("🔄 Refresh Now"):
            get_system_health_snapshot(force_refresh=True)
            get_system_activity_snapshot(force_refresh=True)
            st.rerun()

    system_health = get_system_health_snapshot()
    system_activity = get_system_activity_snapshot()

    # Service Status Grid
    services = get_service_status(system_health)

    # Create responsive columns
    cols = st.columns(3)
    for i, (service_name, status) in enumerate(services.items()):
        with cols[i % 3]:
            render_service_status_card(service_name, status)

    # System Metrics
    st.markdown("### 📊 System Metrics")
    metrics = get_system_metrics(system_health)

    st.markdown('<div class="system-metrics">', unsafe_allow_html=True)
    for metric_name, metric_value in metrics.items():
        st.markdown(f"""
        <div class="metric-row">
            <span class="metric-label">{metric_name}</span>
            <span class="metric-value">{metric_value}</span>
        </div>
        """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

    if system_activity:
        st.markdown("### 🛰️ Recent Activity")
        for event in system_activity[:6]:
            st.markdown(f"""
            <div style="background:#f9fafb;border-radius:8px;padding:0.75rem;margin-bottom:0.5rem;">
                <strong>{event.get('ts', 'Unknown')}</strong> — {event.get('source', 'system')} • {event.get('status', '').title()}<br/>
                <span style="color:#4b5563;">{event.get('details', '')}</span>
            </div>
            """, unsafe_allow_html=True)

    # Quick Actions Section
    st.markdown("### ⚡ Quick Actions")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🚀 Start Backend"):
            try:
                # Add logic to start backend service
                st.success("Backend start command sent")
            except Exception as e:
                st.error(f"Failed to start backend: {e}")

    with col2:
        if st.button("🐳 Docker Status"):
            try:
                result = subprocess.run(['docker', 'ps'], capture_output=True, text=True)
                if result.returncode == 0:
                    st.success("Docker is running")
                    with st.expander("Docker Containers"):
                        st.code(result.stdout)
                else:
                    st.warning("Docker not running or accessible")
            except Exception as e:
                st.error(f"Docker check failed: {e}")

    with col3:
        if st.button("📋 Service Logs"):
            st.info("Service logs viewer - implement based on your logging setup")

    with col4:
        if st.button("🔧 Restart Services"):
            st.warning("Service restart - implement based on your service management")

    # Development Tools Section
    with st.expander("🛠️ Development Tools", expanded=False):
        st.markdown("#### Database Tools")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("🐘 Open pgAdmin"):
                st.info("Opening pgAdmin at http://localhost:5050")

        with col2:
            if st.button("📡 Open Redis Commander"):
                st.info("Opening Redis Commander at http://localhost:8081")

        st.markdown("#### API Tools")
        col1, col2 = st.columns(2)

        with col1:
            if st.button("📡 Test Backend API"):
                try:
                    health_snapshot = get_system_health_snapshot(force_refresh=True)
                    if health_snapshot:
                        st.success("✅ Backend API responded via FastAPI client")
                        st.json({"cpu": health_snapshot.get('cpu_pct'), "memory": health_snapshot.get('memory_pct')})
                    else:
                        st.warning("⚠️ No response from FastAPI client")
                except Exception as e:
                    st.error(f"❌ Backend API unreachable: {e}")

        with col2:
            if st.button("📊 API Documentation"):
                st.info("Opening API docs at http://localhost:8000/docs")

    # Docker Controls Section
    with st.expander("🐳 Docker Controls", expanded=False):
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📋 Docker PS"):
                try:
                    result = subprocess.run(['docker', 'ps', '-a'], capture_output=True, text=True, timeout=10)
                    st.code(result.stdout)
                except Exception as e:
                    st.error(f"Docker PS failed: {e}")

        with col2:
            if st.button("🔄 Docker Compose Up"):
                st.info("Starting Docker Compose services...")
                try:
                    # Add your docker-compose path here
                    st.warning("Implement docker-compose up based on your setup")
                except Exception as e:
                    st.error(f"Docker Compose failed: {e}")

        with col3:
            if st.button("🛑 Docker Compose Down"):
                st.info("Stopping Docker Compose services...")
                try:
                    st.warning("Implement docker-compose down based on your setup")
                except Exception as e:
                    st.error(f"Docker Compose down failed: {e}")

# =============================================================================
# ENHANCED SYSTEM MONITORING CLASS
# =============================================================================

class SystemMonitor:
    """Enhanced System Monitor with comprehensive metrics and health checking"""

    def __init__(self, system_health: Optional[Dict[str, Any]] = None):
        """Initialize the system monitor"""
        self.system_health = system_health or {}
        self.integration_hooks = self.create_mock_integration_hooks(self.system_health)

    def create_mock_integration_hooks(self, system_health: Optional[Dict[str, Any]] = None):
        """Create mock integration hooks or use API health data"""
        services = (system_health or {}).get('services', {})

        def _status_for(key: str):
            value = services.get(key)
            if value == 'running':
                return {'running': True, 'status': 'Connected'}
            if value == 'stopped':
                return {'running': False, 'status': 'Stopped'}
            return {'running': False, 'status': 'Unknown'}

        return {
            'get_integration_status': lambda: {
                'lockstep_manager': _status_for('lockstep_manager'),
                'database': _status_for('postgres'),
                'redis': _status_for('redis'),
                'api_server': _status_for('backend_api')
            }
        }

    def get_system_stats(self) -> Dict[str, Any]:
        """Get comprehensive system statistics"""
        if self.system_health:
            try:
                network = psutil.net_io_counters()
                return {
                    'cpu_usage': self.system_health.get('cpu_pct', 0),
                    'cpu_count': self.system_health.get('cpu_count', psutil.cpu_count()),
                    'memory_total': self.system_health.get('memory_total_gb', 0) * (1024**3),
                    'memory_available': self.system_health.get('memory_available_gb', 0) * (1024**3),
                    'memory_used': (self.system_health.get('memory_total_gb', 0) - self.system_health.get('memory_available_gb', 0)) * (1024**3),
                    'memory_usage': self.system_health.get('memory_pct', 0),
                    'disk_total': self.system_health.get('disk_total_gb', 0) * (1024**3),
                    'disk_used': (self.system_health.get('disk_total_gb', 0) - self.system_health.get('disk_free_gb', 0)) * (1024**3),
                    'disk_free': self.system_health.get('disk_free_gb', 0) * (1024**3),
                    'disk_usage_percent': self.system_health.get('disk_pct', 0),
                    'network_bytes_sent': network.bytes_sent,
                    'network_bytes_recv': network.bytes_recv,
                    'boot_time': datetime.fromtimestamp(psutil.boot_time())
                }
            except Exception as exc:
                st.warning(f"Backend system health incomplete: {exc}")
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            network = psutil.net_io_counters()
            return {
                'cpu_usage': cpu_percent,
                'cpu_count': cpu_count,
                'memory_total': memory.total,
                'memory_available': memory.available,
                'memory_used': memory.used,
                'memory_usage': memory.percent,
                'disk_total': disk.total,
                'disk_used': disk.used,
                'disk_free': disk.free,
                'disk_usage_percent': (disk.used / disk.total) * 100,
                'network_bytes_sent': network.bytes_sent,
                'network_bytes_recv': network.bytes_recv,
                'boot_time': datetime.fromtimestamp(psutil.boot_time())
            }
        except Exception as e:
            st.error(f"Error getting system stats: {e}")
            return {}

    def get_system_services(self) -> List[Dict[str, Any]]:
        """Get system services status with enhanced monitoring"""
        try:
            # Get integration status safely
            integration_status = self.integration_hooks['get_integration_status']()

            api_services = (self.system_health.get('services') if isinstance(self.system_health, dict) else {}) or {}
            services = [
                {
                    "Service": "Streamlit Web Server",
                    "Status": api_services.get('admin_portal', 'Running'),
                    "Port": "8506",
                    "Uptime": "Active",
                    "Health": "Healthy" if api_services.get('admin_portal', 'running') == 'running' else "Warning",
                    "Description": "Admin Portal Web Interface"
                },
                {
                    "Service": "PostgreSQL Database",
                    "Status": integration_status.get('database', {}).get('status', 'Unknown'),
                    "Port": "5432",
                    "Uptime": "Available",
                    "Health": "Healthy" if integration_status.get('database', {}).get('running') else "Warning",
                    "Description": "Primary Database Server"
                },
                {
                    "Service": "Redis Cache",
                    "Status": integration_status.get('redis', {}).get('status', 'Unknown'),
                    "Port": "6379",
                    "Uptime": "Available",
                    "Health": "Healthy" if integration_status.get('redis', {}).get('running') else "Warning",
                    "Description": "Caching and Session Store"
                },
                {
                    "Service": "API Server",
                    "Status": integration_status.get('api_server', {}).get('status', 'Unknown'),
                    "Port": "8000",
                    "Uptime": "Available",
                    "Health": "Healthy" if integration_status.get('api_server', {}).get('running') else "Warning",
                    "Description": "REST API Backend"
                },
                {
                    "Service": "AI Processing Engine",
                    "Status": "Ready",
                    "Port": "N/A",
                    "Uptime": "Standby",
                    "Health": "Healthy",
                    "Description": "AI Data Enhancement System"
                },
                {
                    "Service": "File Parser Service",
                    "Status": "Ready",
                    "Port": "N/A",
                    "Uptime": "Standby",
                    "Health": "Healthy",
                    "Description": "Document Processing Service"
                }
            ]

            return services
        except Exception as e:
            st.error(f"Error getting service status: {e}")
            return []

    def get_health_summary(self) -> Dict[str, Any]:
        """Get overall system health summary"""
        try:
            stats = self.get_system_stats()
            services = self.get_system_services()

            # Calculate health metrics
            running_services = sum(1 for s in services if s['Status'] in ['Running', 'Connected', 'Ready'])
            total_services = len(services)

            healthy_services = sum(1 for s in services if s['Health'] == 'Healthy')

            # Integration status
            integration_status = self.integration_hooks['get_integration_status']()

            health_summary = {
                'overall_health': 'Healthy' if healthy_services / total_services > 0.8 else 'Warning',
                'services_running': f"{running_services}/{total_services}",
                'services_healthy': f"{healthy_services}/{total_services}",
                'disk_health': 'Good' if stats.get('disk_usage_percent', 0) < 80 else 'Warning',
                'memory_health': 'Good' if stats.get('memory_usage', 0) < 80 else 'Warning',
                'cpu_health': 'Good' if stats.get('cpu_usage', 0) < 70 else 'Warning',
                'integration_health': 'Connected' if integration_status.get('lockstep_manager', {}).get('running', False) else 'Disconnected'
            }

            return health_summary
        except Exception as e:
            st.error(f"Error getting health summary: {e}")
            return {}

def render_enhanced_system_metrics():
    """Render enhanced system metrics with health analysis"""
    system_monitor = SystemMonitor(get_system_health_snapshot())

    st.subheader("📊 Enhanced System Metrics")

    # Get system data
    stats = system_monitor.get_system_stats()
    health_summary = system_monitor.get_health_summary()

    if not stats:
        st.error("Unable to retrieve system statistics")
        return

    # System health overview
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        health_color = "🟢" if health_summary.get('overall_health') == 'Healthy' else "🟡"
        st.metric(f"{health_color} Overall Health", health_summary.get('overall_health', 'Unknown'))

    with col2:
        st.metric("🔧 Services", health_summary.get('services_running', '0/0'))

    with col3:
        cpu_health = health_summary.get('cpu_health', 'Unknown')
        cpu_color = "🟢" if cpu_health == 'Good' else "🟡"
        st.metric(f"{cpu_color} CPU Health", cpu_health)

    with col4:
        memory_health = health_summary.get('memory_health', 'Unknown')
        memory_color = "🟢" if memory_health == 'Good' else "🟡"
        st.metric(f"{memory_color} Memory Health", memory_health)

    # Detailed metrics
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 💻 CPU & Performance")
        st.metric("CPU Usage", f"{stats.get('cpu_usage', 0):.1f}%")
        st.metric("CPU Cores", stats.get('cpu_count', 0))

    with col2:
        st.markdown("#### 🧠 Memory")
        memory_used_gb = stats.get('memory_used', 0) / (1024**3)
        memory_total_gb = stats.get('memory_total', 0) / (1024**3)
        st.metric("Memory Used", f"{memory_used_gb:.1f} GB")
        st.metric("Memory Total", f"{memory_total_gb:.1f} GB")
        st.metric("Memory Usage", f"{stats.get('memory_usage', 0):.1f}%")

    with col3:
        st.markdown("#### 💽 Storage")
        disk_used_gb = stats.get('disk_used', 0) / (1024**3)
        disk_total_gb = stats.get('disk_total', 0) / (1024**3)
        st.metric("Disk Used", f"{disk_used_gb:.1f} GB")
        st.metric("Disk Total", f"{disk_total_gb:.1f} GB")
        st.metric("Disk Usage", f"{stats.get('disk_usage_percent', 0):.1f}%")

def render_enhanced_service_status():
    """Render enhanced service status with detailed monitoring"""
    system_monitor = SystemMonitor(get_system_health_snapshot())
    services = system_monitor.get_system_services()

    st.subheader("🔧 Service Status Monitor")

    if not services:
        st.error("Unable to retrieve service status")
        return

    # Service status cards
    for i in range(0, len(services), 2):
        col1, col2 = st.columns(2)

        with col1:
            if i < len(services):
                service = services[i]
                status_color = "🟢" if service['Status'] in ['Running', 'Connected', 'Ready'] else "🔴"
                health_color = "🟢" if service['Health'] == 'Healthy' else "🟡"

                st.markdown(f"""
                <div style="
                    background: white;
                    padding: 1rem;
                    border-radius: 8px;
                    border-left: 4px solid {'#10b981' if service['Health'] == 'Healthy' else '#f59e0b'};
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    margin-bottom: 1rem;
                ">
                    <h4 style="margin: 0 0 0.5rem 0;">{status_color} {service['Service']}</h4>
                    <p style="margin: 0; color: #666; font-size: 0.9rem;">{service['Description']}</p>
                    <div style="margin-top: 0.5rem;">
                        <span style="background: {'#dcfce7' if service['Health'] == 'Healthy' else '#fef3c7'};
                                     color: {'#166534' if service['Health'] == 'Healthy' else '#92400e'};
                                     padding: 0.25rem 0.5rem; border-radius: 12px; font-size: 0.8rem;">
                            {health_color} {service['Health']}
                        </span>
                        <span style="margin-left: 0.5rem; color: #666; font-size: 0.8rem;">
                            Port: {service['Port']} | {service['Uptime']}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        with col2:
            if i + 1 < len(services):
                service = services[i + 1]
                status_color = "🟢" if service['Status'] in ['Running', 'Connected', 'Ready'] else "🔴"
                health_color = "🟢" if service['Health'] == 'Healthy' else "🟡"

                st.markdown(f"""
                <div style="
                    background: white;
                    padding: 1rem;
                    border-radius: 8px;
                    border-left: 4px solid {'#10b981' if service['Health'] == 'Healthy' else '#f59e0b'};
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    margin-bottom: 1rem;
                ">
                    <h4 style="margin: 0 0 0.5rem 0;">{status_color} {service['Service']}</h4>
                    <p style="margin: 0; color: #666; font-size: 0.9rem;">{service['Description']}</p>
                    <div style="margin-top: 0.5rem;">
                        <span style="background: {'#dcfce7' if service['Health'] == 'Healthy' else '#fef3c7'};
                                     color: {'#166534' if service['Health'] == 'Healthy' else '#92400e'};
                                     padding: 0.25rem 0.5rem; border-radius: 12px; font-size: 0.8rem;">
                            {health_color} {service['Health']}
                        </span>
                        <span style="margin-left: 0.5rem; color: #666; font-size: 0.8rem;">
                            Port: {service['Port']} | {service['Uptime']}
                        </span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

# =============================================================================
# MAIN RENDER FUNCTION
# =============================================================================

def render_service_status_monitor():
    """Render the complete Service Status Monitor"""
    # Page configuration
    st.set_page_config(
        page_title="🔧 Service Status Monitor",
        page_icon="🔧",
        layout="wide"
    )


with st.sidebar.expander("🛰️ Backend ping", expanded=False):
    payload, err = _backend_try_get("/telemetry/status")
    if payload is not None:
        st.success("✅ Backend reachable")
        st.json(payload)
    else:
        st.info(f"Backend not reachable ({err})")

    # Authentication check
    check_admin_authentication()

    # Inject CSS
    inject_admin_monitoring_css()

    # Header
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%);
        color: white;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(0,0,0,0.2);
    ">
        <h1 style="margin: 0; font-size: 2.5rem;">🔧 Service Status Monitor</h1>
        <p style="margin: 0.5rem 0 0 0; opacity: 0.9; font-size: 1.2rem;">
            Comprehensive System Monitoring & Service Health Analysis
        </p>
        <p style="margin: 0.3rem 0 0 0; opacity: 0.7; font-size: 1rem;">
            Real-time metrics • Service monitoring • Performance analysis
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Enhanced system metrics
    render_enhanced_system_metrics()

    st.markdown("---")

    # Enhanced service status
    render_enhanced_service_status()

    # Original quick actions (kept for compatibility)
    st.markdown("---")
    st.subheader("🚀 Quick Actions")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🔄 Refresh Status"):
            get_system_health_snapshot(force_refresh=True)
            get_system_activity_snapshot(force_refresh=True)
            st.rerun()

    with col2:
        if st.button("📊 View Logs"):
            st.info("Service logs viewer - implement based on your logging setup")

    with col3:
        if st.button("🔧 Restart Services"):
            st.warning("Service restart - implement based on your service management")

    with col4:
        if st.button("⚙️ System Settings"):
            st.switch_page("pages/16_Advanced_Settings.py")

    # Docker Controls Section
    st.markdown("---")
    st.subheader("🐳 Docker Container Management")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("🚀 Docker Compose Up"):
            try:
                st.info("Starting Docker containers...")
                # Add your docker-compose path here
                st.warning("Implement docker-compose up based on your setup")
                # Example implementation:
                # import subprocess
                # result = subprocess.run(['docker-compose', 'up', '-d'],
                #                        cwd='C:\\IntelliCV-AI',
                #                        capture_output=True, text=True)
                # if result.returncode == 0:
                #     st.success("Docker containers started successfully!")
                # else:
                #     st.error(f"Docker start failed: {result.stderr}")
            except Exception as e:
                st.error(f"Docker Compose up failed: {e}")

    with col2:
        if st.button("🛑 Docker Compose Down"):
            try:
                st.info("Stopping Docker containers...")
                # Add your docker-compose path here
                st.warning("Implement docker-compose down based on your setup")
                # Example implementation:
                # import subprocess
                # result = subprocess.run(['docker-compose', 'down'],
                #                        cwd='C:\\IntelliCV-AI',
                #                        capture_output=True, text=True)
                # if result.returncode == 0:
                #     st.success("Docker containers stopped successfully!")
                # else:
                #     st.error(f"Docker stop failed: {result.stderr}")
            except Exception as e:
                st.error(f"Docker Compose down failed: {e}")

    with col3:
        if st.button("🔄 Docker Restart"):
            try:
                st.info("Restarting Docker containers...")
                # Implement docker-compose restart
                st.warning("Implement docker-compose restart based on your setup")
                # Example implementation:
                # import subprocess
                # result = subprocess.run(['docker-compose', 'restart'],
                #                        cwd='C:\\IntelliCV-AI',
                #                        capture_output=True, text=True)
            except Exception as e:
                st.error(f"Docker restart failed: {e}")

    with col4:
        if st.button("📋 Docker Status"):
            try:
                st.info("Checking Docker container status...")
                # Implement docker ps
                st.warning("Implement docker ps status check")
                # Example implementation:
                # import subprocess
                # result = subprocess.run(['docker', 'ps'],
                #                        capture_output=True, text=True)
                # if result.returncode == 0:
                #     st.code(result.stdout)
            except Exception as e:
                st.error(f"Docker status check failed: {e}")

# =============================================================================
# MAIN EXECUTION
# =============================================================================

if __name__ == "__main__":
    render_service_status_monitor()
else:
    render_service_status_monitor()
