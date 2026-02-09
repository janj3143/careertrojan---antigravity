"""
Shared Data Models for IntelliCV Admin Portal
============================================

Common data structures and models used across admin modules.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum

class UserRole(Enum):
    """User role enumeration"""
    GUEST = "guest"
    USER = "user"  
    MANAGER = "manager"
    ADMIN = "admin"
    SUPERADMIN = "superadmin"

class SystemStatus(Enum):
    """System status enumeration"""
    OPERATIONAL = "operational"
    WARNING = "warning"
    ERROR = "error"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"

class JobStatus(Enum):
    """Processing job status enumeration"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class AdminUser:
    """Admin user data model"""
    id: int
    username: str
    email: str
    role: UserRole
    created_at: datetime
    last_login: Optional[datetime] = None
    is_active: bool = True
    permissions: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if isinstance(self.role, str):
            self.role = UserRole(self.role)

@dataclass
class SystemMetrics:
    """System metrics data model"""
    timestamp: datetime
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    network_io: float
    active_users: int
    active_sessions: int
    api_requests_per_minute: int
    database_connections: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp.isoformat(),
            "cpu_usage": self.cpu_usage,
            "memory_usage": self.memory_usage,
            "disk_usage": self.disk_usage,
            "network_io": self.network_io,
            "active_users": self.active_users,
            "active_sessions": self.active_sessions,
            "api_requests_per_minute": self.api_requests_per_minute,
            "database_connections": self.database_connections
        }

@dataclass
class ProcessingJob:
    """Processing job data model"""
    id: int
    name: str
    job_type: str
    status: JobStatus
    progress: float
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_by: str = "system"
    error_message: Optional[str] = None
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if isinstance(self.status, str):
            self.status = JobStatus(self.status)
    
    @property
    def duration(self) -> Optional[float]:
        """Get job duration in seconds"""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None
    
    @property
    def is_running(self) -> bool:
        """Check if job is currently running"""
        return self.status == JobStatus.RUNNING
    
    @property
    def is_completed(self) -> bool:
        """Check if job is completed (success or failure)"""
        return self.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]

@dataclass
class AIEnrichmentResult:
    """AI enrichment result data model"""
    id: int
    profile_id: int
    enrichment_type: str
    confidence_score: float
    enriched_fields: Dict[str, Any]
    processing_time: float
    model_version: str
    created_at: datetime
    status: str = "completed"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "profile_id": self.profile_id,
            "enrichment_type": self.enrichment_type,
            "confidence_score": self.confidence_score,
            "enriched_fields": self.enriched_fields,
            "processing_time": self.processing_time,
            "model_version": self.model_version,
            "created_at": self.created_at.isoformat(),
            "status": self.status
        }

@dataclass
class SecurityEvent:
    """Security event data model"""
    id: int
    event_type: str
    severity: str
    user_id: Optional[int]
    ip_address: str
    user_agent: str
    description: str
    timestamp: datetime
    resolved: bool = False
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "event_type": self.event_type,
            "severity": self.severity,
            "user_id": self.user_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "description": self.description,
            "timestamp": self.timestamp.isoformat(),
            "resolved": self.resolved,
            "resolved_by": self.resolved_by,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None
        }

@dataclass
class APIEndpoint:
    """API endpoint monitoring data model"""
    path: str
    method: str
    status: SystemStatus
    requests_per_minute: int
    avg_response_time: float
    error_rate: float
    last_error: Optional[str] = None
    last_request: Optional[datetime] = None
    
    def __post_init__(self):
        if isinstance(self.status, str):
            self.status = SystemStatus(self.status)

@dataclass
class ComplianceCheck:
    """Compliance check result data model"""
    id: int
    check_type: str
    category: str
    status: str
    score: float
    description: str
    recommendations: List[str]
    last_checked: datetime
    next_check: datetime
    
    @property
    def is_compliant(self) -> bool:
        """Check if compliance check passed"""
        return self.status.lower() in ["pass", "compliant", "ok"]

@dataclass
class AnalyticsReport:
    """Analytics report data model"""
    id: int
    name: str
    report_type: str
    data: Dict[str, Any]
    generated_at: datetime
    generated_by: str
    file_size: int
    format: str = "json"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "report_type": self.report_type,
            "generated_at": self.generated_at.isoformat(),
            "generated_by": self.generated_by,
            "file_size": self.file_size,
            "format": self.format,
            "data_keys": list(self.data.keys()) if self.data else []
        }

# Factory functions for creating sample data

def create_sample_admin_user(id: int) -> AdminUser:
    """Create a sample admin user"""
    return AdminUser(
        id=id,
        username=f"admin_user_{id}",
        email=f"admin{id}@intellicv.com",
        role=UserRole.ADMIN,
        created_at=datetime.now(),
        last_login=datetime.now(),
        permissions=["read", "write", "admin"]
    )

def create_sample_processing_job(id: int) -> ProcessingJob:
    """Create a sample processing job"""
    import random
    
    statuses = list(JobStatus)
    job_types = ["resume_processing", "data_enrichment", "batch_analysis", "report_generation"]
    
    job = ProcessingJob(
        id=id,
        name=f"Job_{id}_{random.choice(job_types)}",
        job_type=random.choice(job_types),
        status=random.choice(statuses),
        progress=random.uniform(0, 100),
        created_at=datetime.now(),
        created_by=f"user_{random.randint(1, 10)}"
    )
    
    if job.status == JobStatus.RUNNING:
        job.started_at = datetime.now()
    elif job.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
        job.started_at = datetime.now()
        job.completed_at = datetime.now()
        job.progress = 100.0
    
    return job

def create_sample_system_metrics() -> SystemMetrics:
    """Create sample system metrics"""
    import random
    
    return SystemMetrics(
        timestamp=datetime.now(),
        cpu_usage=random.uniform(10, 80),
        memory_usage=random.uniform(30, 90),
        disk_usage=random.uniform(40, 95),
        network_io=random.uniform(10, 1000),
        active_users=random.randint(10, 100),
        active_sessions=random.randint(20, 200),
        api_requests_per_minute=random.randint(100, 1000),
        database_connections=random.randint(10, 50)
    )