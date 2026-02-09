
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

#!/usr/bin/env python3
"""
IntelliCV Admin Portal - Admin Parsers
======================================

Advanced parser management and monitoring system for admin users.
Migrated from old admin portal with enhanced monitoring and AI integration.

Features:
- Parser execution and monitoring
- Real-time process tracking
- Log management and analysis
- Performance metrics
- Integration with AI enrichment system

Author: IntelliCV AI System
Date: September 21, 2025
"""

import streamlit as st
import subprocess
import time
import json
import psutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import threading
import queue

# Import shared components
try:
    from shared.components import render_section_header, render_metrics_row
    from shared.utils import get_session_state, set_session_state
    SHARED_AVAILABLE = True
except ImportError:
    SHARED_AVAILABLE = False

class ParserManager:
    """Advanced parser management with monitoring capabilities"""
    
    def __init__(self):
        """Initialize parser manager"""
        self.base_path = Path(__file__).parent.parent
        self.data_parsers_path = self.base_path / "data_parsers"
        self.logs_path = self.base_path / "logs"
        self.python_exe = self._find_python_executable()
        
        # Ensure directories exist
        self.logs_path.mkdir(exist_ok=True)
        
        # Available parsers
        self.parsers = {
            "Universal Parser": {
                "script": "resume_parser.py",
                "description": "Parse all resume formats",
                "category": "core"
            },
            "Company Email Extractor": {
                "script": "company_email_extract.py", 
                "description": "Extract company email addresses",
                "category": "email"
            },
            "AI Enrichment Parser": {
                "script": "ai_enrichment.py",
                "description": "AI-powered data enrichment",
                "category": "ai"
            },
            "Resume Content Parser": {
                "script": "resume_parser.py",
                "description": "Extract resume content and structure",
                "category": "resume"
            },
            "Job Description Analyzer": {
                "script": "job_description_parser.py",
                "description": "Analyze job descriptions and requirements",
                "category": "job"
            },
            "Skills Extractor": {
                "script": "skills_extractor.py",
                "description": "Extract and categorize skills",
                "category": "skills"
            }
        }
        
        self.running_processes = {}
        self.process_logs = {}
    
    def _find_python_executable(self) -> str:
        """Find the appropriate Python executable"""
        candidates = [
            "C:/IntelliCV/env310/python.exe",
            "C:/IntelliCV/env310/Scripts/python.exe", 
            "python",
            "python3"
        ]
        
        for candidate in candidates:
            try:
                result = subprocess.run([candidate, "--version"], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    return candidate
            except:
                continue
        
        return "python"  # fallback
    
    def get_parser_script_path(self, script_name: str) -> Optional[Path]:
        """Get full path to parser script"""
        script_path = self.data_parsers_path / script_name
        if script_path.exists():
            return script_path
        
        # Check in parent admin_portal directory
        alt_path = self.base_path.parent / "admin_portal" / "data_parsers" / script_name
        if alt_path.exists():
            return alt_path
        
        return None
    
    def start_parser(self, parser_name: str, options: Dict[str, Any] = None) -> Dict[str, Any]:
        """Start a parser process"""
        if parser_name not in self.parsers:
            return {"success": False, "error": f"Unknown parser: {parser_name}"}
        
        parser_info = self.parsers[parser_name]
        script_path = self.get_parser_script_path(parser_info["script"])
        
        if not script_path:
            return {"success": False, "error": f"Script not found: {parser_info['script']}"}
        
        try:
            # Create unique process ID
            process_id = f"{parser_name}_{int(time.time())}"
            
            # Prepare command
            cmd = [self.python_exe, str(script_path)]
            
            # Add options if provided
            if options:
                for key, value in options.items():
                    if value:  # Skip empty values
                        cmd.extend([f"--{key}", str(value)])
            
            # Start process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                cwd=str(script_path.parent)
            )
            
            # Track process
            self.running_processes[process_id] = {
                "process": process,
                "parser_name": parser_name,
                "start_time": datetime.now(),
                "command": " ".join(cmd),
                "status": "running"
            }
            
            # Initialize log queue
            self.process_logs[process_id] = queue.Queue()
            
            # Start log monitoring thread
            log_thread = threading.Thread(
                target=self._monitor_process_output,
                args=(process_id, process)
            )
            log_thread.daemon = True
            log_thread.start()
            
            return {
                "success": True,
                "process_id": process_id,
                "message": f"Started {parser_name} successfully"
            }
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def _monitor_process_output(self, process_id: str, process: subprocess.Popen):
        """Monitor process output in separate thread"""
        try:
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.process_logs[process_id].put({
                        "timestamp": datetime.now(),
                        "type": "stdout",
                        "message": output.strip()
                    })
            
            # Get any remaining error output
            stderr_output = process.stderr.read()
            if stderr_output:
                self.process_logs[process_id].put({
                    "timestamp": datetime.now(),
                    "type": "stderr", 
                    "message": stderr_output.strip()
                })
            
            # Update process status
            if process_id in self.running_processes:
                self.running_processes[process_id]["status"] = "completed"
                self.running_processes[process_id]["end_time"] = datetime.now()
                self.running_processes[process_id]["return_code"] = process.returncode
                
        except Exception as e:
            if process_id in self.process_logs:
                self.process_logs[process_id].put({
                    "timestamp": datetime.now(),
                    "type": "error",
                    "message": f"Monitoring error: {str(e)}"
                })
    
    def get_process_status(self, process_id: str) -> Dict[str, Any]:
        """Get status of a running process"""
        if process_id not in self.running_processes:
            return {"exists": False}
        
        proc_info = self.running_processes[process_id]
        process = proc_info["process"]
        
        # Check if process is still running
        if process.poll() is None:
            status = "running"
        else:
            status = "completed" if process.returncode == 0 else "failed"
            proc_info["status"] = status
        
        # Get runtime
        start_time = proc_info["start_time"]
        end_time = proc_info.get("end_time", datetime.now())
        runtime = (end_time - start_time).total_seconds()
        
        return {
            "exists": True,
            "status": status,
            "runtime": runtime,
            "return_code": process.returncode if process.poll() is not None else None,
            "start_time": start_time,
            "parser_name": proc_info["parser_name"],
            "command": proc_info["command"]
        }
    
    def get_process_logs(self, process_id: str, max_lines: int = 100) -> List[Dict]:
        """Get recent logs for a process"""
        if process_id not in self.process_logs:
            return []
        
        logs = []
        log_queue = self.process_logs[process_id]
        
        # Get all available logs
        while not log_queue.empty() and len(logs) < max_lines:
            try:
                logs.append(log_queue.get_nowait())
            except queue.Empty:
                break
        
        return logs[-max_lines:]  # Return most recent logs
    
    def stop_process(self, process_id: str) -> Dict[str, Any]:
        """Stop a running process"""
        if process_id not in self.running_processes:
            return {"success": False, "error": "Process not found"}
        
        try:
            process = self.running_processes[process_id]["process"]
            process.terminate()
            
            # Wait for graceful termination
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            
            self.running_processes[process_id]["status"] = "stopped"
            self.running_processes[process_id]["end_time"] = datetime.now()
            
            return {"success": True, "message": "Process stopped successfully"}
            
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get system performance metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_gb": memory.available / (1024**3),
                "disk_percent": disk.percent,
                "disk_free_gb": disk.free / (1024**3),
                "running_processes": len([p for p in self.running_processes.values() if p["status"] == "running"])
            }
        except Exception as e:
            return {"error": str(e)}

def render_parser_management():
    """Render parser management interface"""
    parser_manager = ParserManager()
    

# Activate Enhanced Sidebar
if ENHANCED_SIDEBAR_AVAILABLE:
    inject_sidebar_css()
    render_enhanced_sidebar()

    st.subheader("🚀 Parser Execution")
    
    # Parser selection
    col1, col2 = st.columns([2, 1])
    
    with col1:
        parser_categories = {
            "core": "Core Parsers",
            "ai": "AI Enhancement", 
            "email": "Email Processing",
            "resume": "Resume Analysis",
            "job": "Job Description",
            "skills": "Skills Extraction"
        }
        
        selected_category = st.selectbox("Parser Category", list(parser_categories.values()))
        category_key = [k for k, v in parser_categories.items() if v == selected_category][0]
        
        # Filter parsers by category
        available_parsers = {
            name: info for name, info in parser_manager.parsers.items() 
            if info["category"] == category_key
        }
        
        selected_parser = st.selectbox(
            "Select Parser",
            list(available_parsers.keys()),
            format_func=lambda x: f"{x} - {available_parsers[x]['description']}"
        )
    
    with col2:
        st.subheader("📊 Quick Stats")
        metrics = parser_manager.get_system_metrics()
        
        if "error" not in metrics:
            st.metric("CPU Usage", f"{metrics['cpu_percent']:.1f}%")
            st.metric("Memory Usage", f"{metrics['memory_percent']:.1f}%")
            st.metric("Running Parsers", metrics['running_processes'])
    
    # Parser options
    with st.expander("⚙️ Parser Options"):
        col1, col2 = st.columns(2)
        
        with col1:
            input_dir = st.text_input("Input Directory", value="data/resumes")
            output_dir = st.text_input("Output Directory", value="ai_data")
            batch_size = st.number_input("Batch Size", min_value=1, max_value=1000, value=100)
        
        with col2:
            enable_ai = st.checkbox("Enable AI Enhancement", value=True)
            verbose_logging = st.checkbox("Verbose Logging", value=False)
            concurrent_processing = st.checkbox("Concurrent Processing", value=True)
    
    # Start parser
    if st.button("🚀 Start Parser", type="primary"):
        options = {
            "input-dir": input_dir,
            "output-dir": output_dir,
            "batch-size": batch_size,
            "ai-enhancement": enable_ai,
            "verbose": verbose_logging,
            "concurrent": concurrent_processing
        }
        
        result = parser_manager.start_parser(selected_parser, options)
        
        if result["success"]:
            st.success(f"✅ {result['message']}")
            st.session_state[f"parser_process_id"] = result["process_id"]
        else:
            st.error(f"❌ {result['error']}")

def render_process_monitoring():
    """Render process monitoring interface"""
    st.subheader("📊 Process Monitoring")
    
    parser_manager = ParserManager()
    
    # Get all processes
    all_processes = list(parser_manager.running_processes.keys())
    
    if not all_processes:
        st.info("No running or recent processes found.")
        return
    
    # Process selection
    selected_process = st.selectbox("Select Process", all_processes)
    
    if selected_process:
        status = parser_manager.get_process_status(selected_process)
        
        if status["exists"]:
            # Status display
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                status_color = {"running": "🟢", "completed": "✅", "failed": "❌", "stopped": "⏹️"}
                st.metric("Status", f"{status_color.get(status['status'], '❓')} {status['status'].title()}")
            
            with col2:
                st.metric("Runtime", f"{status['runtime']:.1f}s")
            
            with col3:
                st.metric("Parser", status['parser_name'])
            
            with col4:
                if status['return_code'] is not None:
                    st.metric("Exit Code", status['return_code'])
            
            # Control buttons
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if status["status"] == "running" and st.button("⏹️ Stop Process"):
                    result = parser_manager.stop_process(selected_process)
                    if result["success"]:
                        st.success("Process stopped")
                        st.experimental_rerun()
                    else:
                        st.error(f"Failed to stop: {result['error']}")
            
            with col2:
                if st.button("🔄 Refresh Status"):
                    st.experimental_rerun()
            
            with col3:
                if st.button("📋 Show Command"):
                    st.code(status['command'])
            
            # Process logs
            st.subheader("📜 Process Logs")
            
            logs = parser_manager.get_process_logs(selected_process)
            
            if logs:
                for log_entry in logs[-20:]:  # Show last 20 entries
                    timestamp = log_entry["timestamp"].strftime("%H:%M:%S")
                    log_type = log_entry["type"]
                    message = log_entry["message"]
                    
                    if log_type == "stderr" or log_type == "error":
                        st.error(f"[{timestamp}] {message}")
                    elif log_type == "stdout":
                        st.text(f"[{timestamp}] {message}")
                    else:
                        st.info(f"[{timestamp}] {message}")
            else:
                st.info("No logs available yet.")

def main():
    """Main function for admin parsers"""
    if SHARED_AVAILABLE:
        render_section_header(
            "🔧 Admin Parsers",
            "Advanced parser management and monitoring system"
        )
    else:
        st.title("🔧 Admin Parsers")
        st.markdown("Advanced parser management and monitoring system")
    
    # Tab navigation
    tab1, tab2, tab3 = st.tabs([
        "🚀 Parser Manager",
        "📊 Process Monitor", 
        "📋 System Logs"
    ])
    
    with tab1:
        render_parser_management()
    
    with tab2:
        render_process_monitoring()
    
    with tab3:
        st.subheader("📋 System Logs")
        
        # Log file selection
        logs_path = Path(__file__).parent.parent / "logs"
        
        if logs_path.exists():
            log_files = list(logs_path.glob("*.log"))
            
            if log_files:
                selected_log = st.selectbox("Select Log File", log_files)
                
                if selected_log and st.button("📖 Load Log"):
                    try:
                        with open(selected_log, 'r', encoding='utf-8') as f:
                            log_content = f.read()
                        
                        st.text_area("Log Content", log_content, height=400)
                        
                    except Exception as e:
                        st.error(f"Error reading log file: {e}")
            else:
                st.info("No log files found.")
        else:
            st.info("Logs directory not found.")

if __name__ == "__main__":
    main()