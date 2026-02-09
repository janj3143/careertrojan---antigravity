"""
Path Management System for IntelliCV Admin Portal
Provides standardized, cross-platform path handling with Docker detection
"""

from pathlib import Path
import os
from typing import Optional, Dict, Any, Union
from dataclasses import dataclass
import platform

from utils.logging_config import LoggingMixin


@dataclass
class PathConfiguration:
    """Configuration for path management"""
    base_path: Path
    data_path: Path
    logs_path: Path
    config_path: Path
    temp_path: Path
    ai_data_path: Path
    ai_data_final_path: Path
    companies_path: Path
    job_titles_path: Path
    job_descriptions_path: Path
    locations_path: Path
    metadata_path: Path
    parsed_resumes_path: Path
    normalized_path: Path
    parsed_job_descriptions_path: Path
    data_cloud_solutions_path: Path
    cv_path: Path
    profiles_path: Path
    leads_path: Path
    email_extracted_path: Path
    csv_output_path: Path


class PathValidationError(Exception):
    """Path validation error"""
    pass


class PathManager(LoggingMixin):
    """Centralized path management with environment detection"""
    
    def __init__(self, base_path: Optional[Union[str, Path]] = None):
        super().__init__()
        
        self.is_docker = self._detect_docker_environment()
        self.is_windows = platform.system().lower() == "windows"
        self.is_linux = platform.system().lower() == "linux"
        
        # Set base path based on environment
        if base_path:
            self.base_path = Path(base_path).resolve()
        else:
            self.base_path = self._determine_base_path()
        
        self.config = self._initialize_path_configuration()
        
        self.log_info("Path manager initialized", 
                     is_docker=self.is_docker,
                     is_windows=self.is_windows,
                     base_path=str(self.base_path),
                     platform=platform.system())
    
    def _detect_docker_environment(self) -> bool:
        """Detect if running in Docker container"""
        # Multiple detection methods for reliability
        docker_indicators = [
            Path("/.dockerenv").exists(),
            Path("/app").exists() and os.environ.get("DOCKER_ENV") == "true",
            self._check_docker_cgroup(),
            os.environ.get("CONTAINER") == "docker"
        ]
        
        return any(docker_indicators)
    
    def _check_docker_cgroup(self) -> bool:
        """Safely check Docker cgroup information"""
        try:
            if os.path.exists("/proc/1/cgroup"):
                with open("/proc/1/cgroup", 'r') as f:
                    content = f.read()
                    return "docker" in content
        except (IOError, OSError):
            pass
        return False
    
    def _determine_base_path(self) -> Path:
        """Determine base path based on environment"""
        if self.is_docker:
            # Docker environment - use /app as base
            return Path("/app")
        else:
            # Local environment - use current working directory or script location
            current_file = Path(__file__).resolve()
            # Go up to admin_portal directory
            admin_portal_path = current_file.parent.parent
            return admin_portal_path
    
    def _initialize_path_configuration(self) -> PathConfiguration:
        """Initialize comprehensive path configuration"""
        try:
            if self.is_docker:
                # Docker paths
                base_path = Path("/app")
                data_path = base_path / "data"
                ai_data_final_path = base_path / "ai_data_final"
                ai_data_path = base_path / "ai_data"
            else:
                # Local paths
                base_path = self.base_path
                data_path = base_path / "data"
                ai_data_final_path = base_path / "ai_data_final"
                ai_data_path = base_path / "ai_data"
            
            # Common paths for both environments
            logs_path = base_path / "logs"
            config_path = base_path / "config"
            temp_path = base_path / "temp"
            
            # AI data structure paths
            companies_path = ai_data_final_path / "companies"
            job_titles_path = ai_data_final_path / "job_titles"
            job_descriptions_path = ai_data_final_path / "job_descriptions"
            locations_path = ai_data_final_path / "locations"
            metadata_path = ai_data_final_path / "metadata"
            parsed_resumes_path = ai_data_final_path / "parsed_resumes"
            normalized_path = ai_data_final_path / "normalized"
            parsed_job_descriptions_path = ai_data_final_path / "parsed_job_descriptions"
            data_cloud_solutions_path = ai_data_final_path / "data_cloud_solutions"
            cv_path = ai_data_final_path / "cv"
            profiles_path = ai_data_final_path / "profiles"
            leads_path = ai_data_final_path / "leads"
            email_extracted_path = ai_data_path / "email_extracted"
            csv_output_path = ai_data_final_path / "csv_parsed_output"
            
            config = PathConfiguration(
                base_path=base_path,
                data_path=data_path,
                logs_path=logs_path,
                config_path=config_path,
                temp_path=temp_path,
                ai_data_path=ai_data_path,
                ai_data_final_path=ai_data_final_path,
                companies_path=companies_path,
                job_titles_path=job_titles_path,
                job_descriptions_path=job_descriptions_path,
                locations_path=locations_path,
                metadata_path=metadata_path,
                parsed_resumes_path=parsed_resumes_path,
                normalized_path=normalized_path,
                parsed_job_descriptions_path=parsed_job_descriptions_path,
                data_cloud_solutions_path=data_cloud_solutions_path,
                cv_path=cv_path,
                profiles_path=profiles_path,
                leads_path=leads_path,
                email_extracted_path=email_extracted_path,
                csv_output_path=csv_output_path
            )
            
            self.log_info("Path configuration initialized successfully",
                         docker_env=self.is_docker,
                         ai_data_final_exists=ai_data_final_path.exists(),
                         base_path=str(base_path))
            
            return config
            
        except Exception as e:
            self.log_error("Failed to initialize path configuration", exc_info=True)
            raise PathValidationError(f"Path initialization failed: {e}")
    
    def get_path(self, path_name: str) -> Path:
        """Get a specific path by name"""
        if not hasattr(self.config, path_name):
            raise PathValidationError(f"Unknown path name: {path_name}")
        
        path = getattr(self.config, path_name)
        return Path(path)
    
    def ensure_path_exists(self, path: Union[str, Path], is_file: bool = False) -> Path:
        """Ensure path exists, create directories as needed"""
        path = Path(path)
        
        try:
            if is_file:
                # Create parent directories for file
                path.parent.mkdir(parents=True, exist_ok=True)
                if not path.exists():
                    path.touch()
            else:
                # Create directory
                path.mkdir(parents=True, exist_ok=True)
            
            self.log_debug("Path ensured", path=str(path), is_file=is_file, exists=path.exists())
            return path
            
        except Exception as e:
            self.log_error("Failed to ensure path exists", path=str(path), exc_info=True)
            raise PathValidationError(f"Failed to create path {path}: {e}")
    
    def validate_path(self, path: Union[str, Path], must_exist: bool = False,
                     must_be_file: bool = False, must_be_dir: bool = False) -> Path:
        """Validate path with various constraints"""
        path = Path(path)
        
        if must_exist and not path.exists():
            raise PathValidationError(f"Path does not exist: {path}")
        
        if must_be_file and path.exists() and not path.is_file():
            raise PathValidationError(f"Path is not a file: {path}")
        
        if must_be_dir and path.exists() and not path.is_dir():
            raise PathValidationError(f"Path is not a directory: {path}")
        
        return path
    
    def get_relative_path(self, path: Union[str, Path], base: Optional[Union[str, Path]] = None) -> Path:
        """Get relative path from base (default: base_path)"""
        path = Path(path)
        base = Path(base) if base else self.config.base_path
        
        try:
            return path.relative_to(base)
        except ValueError:
            # Path is not relative to base, return as-is
            return path
    
    def normalize_path(self, path: Union[str, Path]) -> Path:
        """Normalize path for current platform"""
        path = Path(path)
        
        # Resolve to absolute path
        if not path.is_absolute():
            path = self.config.base_path / path
        
        # Resolve any symbolic links and normalize
        try:
            path = path.resolve()
        except (OSError, RuntimeError):
            # If resolution fails, just normalize without resolving
            pass
        
        return path
    
    def safe_join(self, base: Union[str, Path], *parts: str) -> Path:
        """Safely join path components, preventing directory traversal"""
        base = Path(base)
        
        for part in parts:
            # Remove any directory traversal attempts
            clean_part = str(part).replace("..", "").replace("/", "").replace("\\", "")
            if clean_part != part:
                self.log_warning("Directory traversal attempt detected", 
                               original=part, cleaned=clean_part)
            base = base / clean_part
        
        return base
    
    def create_all_directories(self) -> Dict[str, bool]:
        """Create all configured directories"""
        results = {}
        
        # Get all Path attributes from configuration
        for attr_name in dir(self.config):
            if not attr_name.startswith('_'):
                attr_value = getattr(self.config, attr_name)
                if isinstance(attr_value, Path):
                    try:
                        # Skip file paths (those ending with known extensions)
                        if attr_value.suffix in {'.json', '.csv', '.txt', '.log'}:
                            continue
                        
                        self.ensure_path_exists(attr_value, is_file=False)
                        results[attr_name] = True
                        self.log_debug("Directory created successfully", path=str(attr_value))
                    except Exception as e:
                        results[attr_name] = False
                        self.log_error("Failed to create directory", 
                                     path=str(attr_value), error=str(e))
        
        success_count = sum(results.values())
        total_count = len(results)
        
        self.log_info("Directory creation completed", 
                     success=success_count, 
                     total=total_count,
                     success_rate=f"{success_count/total_count*100:.1f}%")
        
        return results
    
    def get_disk_usage(self, path: Optional[Union[str, Path]] = None) -> Dict[str, float]:
        """Get disk usage statistics for path"""
        path = Path(path) if path else self.config.base_path
        
        try:
            import shutil
            total, used, free = shutil.disk_usage(path)
            
            return {
                'total_gb': total / (1024**3),
                'used_gb': used / (1024**3),
                'free_gb': free / (1024**3),
                'usage_percent': (used / total) * 100
            }
        except Exception as e:
            self.log_error("Failed to get disk usage", path=str(path), exc_info=True)
            return {}
    
    def cleanup_temp_files(self, older_than_hours: int = 24) -> int:
        """Clean up temporary files older than specified hours"""
        if not self.config.temp_path.exists():
            return 0
        
        from datetime import datetime, timedelta
        
        cutoff_time = datetime.now() - timedelta(hours=older_than_hours)
        cleaned_count = 0
        
        try:
            for temp_file in self.config.temp_path.iterdir():
                if temp_file.is_file():
                    file_time = datetime.fromtimestamp(temp_file.stat().st_mtime)
                    if file_time < cutoff_time:
                        temp_file.unlink()
                        cleaned_count += 1
                        self.log_debug("Temporary file cleaned", file=str(temp_file))
            
            self.log_info("Temporary file cleanup completed", 
                         cleaned_count=cleaned_count,
                         older_than_hours=older_than_hours)
            
        except Exception as e:
            self.log_error("Failed to cleanup temporary files", exc_info=True)
        
        return cleaned_count
    
    def export_path_info(self) -> Dict[str, Any]:
        """Export path configuration information"""
        info = {
            'environment': {
                'is_docker': self.is_docker,
                'is_windows': self.is_windows,
                'is_linux': self.is_linux,
                'platform': platform.system(),
                'base_path': str(self.config.base_path)
            },
            'paths': {}
        }
        
        # Add all configured paths
        for attr_name in dir(self.config):
            if not attr_name.startswith('_'):
                attr_value = getattr(self.config, attr_name)
                if isinstance(attr_value, Path):
                    info['paths'][attr_name] = {
                        'path': str(attr_value),
                        'exists': attr_value.exists(),
                        'is_file': attr_value.is_file() if attr_value.exists() else None,
                        'is_dir': attr_value.is_dir() if attr_value.exists() else None
                    }
        
        # Add disk usage for base path
        info['disk_usage'] = self.get_disk_usage()
        
        return info


# Global path manager instance
_path_manager = None

def get_path_manager() -> PathManager:
    """Get global path manager instance"""
    global _path_manager
    if _path_manager is None:
        _path_manager = PathManager()
    return _path_manager


def get_path(path_name: str) -> Path:
    """Convenience function to get a path by name"""
    return get_path_manager().get_path(path_name)


def ensure_path(path: Union[str, Path], is_file: bool = False) -> Path:
    """Convenience function to ensure path exists"""
    return get_path_manager().ensure_path_exists(path, is_file)