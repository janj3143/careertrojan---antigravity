"""
AI Data Path Configuration and Browser
======================================

Provides path configuration, browsing, and validation for AI data sources.
"""

import streamlit as st
from pathlib import Path
from typing import Optional, List, Tuple
import json

# Canonical AI data directory (repo-root ai_data_final)
try:
    from shared.config import AI_DATA_DIR
except Exception:  # pragma: no cover
    AI_DATA_DIR = Path(__file__).resolve().parents[2] / "ai_data_final"

def get_default_ai_data_path() -> Path:
    """Get the default AI data path (canonical repo-root ai_data_final)."""
    return AI_DATA_DIR

def validate_ai_data_path(path: Path) -> Tuple[bool, str, dict]:
    """
    Validate if a path contains valid AI data structure

    Returns:
        Tuple of (is_valid, message, stats)
    """
    if not path.exists():
        return False, f"❌ Path does not exist: {path}", {}

    if not path.is_dir():
        return False, f"❌ Path is not a directory: {path}", {}

    # Check for expected subdirectories
    expected_dirs = [
        'companies', 'job_titles', 'locations',
        'parsed_resumes', 'normalized', 'metadata'
    ]

    found_dirs = []
    stats = {}

    for dir_name in expected_dirs:
        dir_path = path / dir_name
        if dir_path.exists():
            found_dirs.append(dir_name)
            # Count JSON files
            json_count = len(list(dir_path.glob("*.json")))
            stats[dir_name] = json_count

    if not found_dirs:
        return False, "❌ No AI data directories found (companies, job_titles, etc.)", {}

    total_files = sum(stats.values())
    message = f"✅ Valid AI data path with {len(found_dirs)} directories and {total_files:,} JSON files"

    return True, message, stats

def browse_ai_data_path() -> Optional[Path]:
    """
    Display a path browser interface for selecting AI data directory

    Returns:
        Selected path or None
    """
    st.subheader("📁 Browse for AI Data Directory")

    # Common paths to check
    default_path = get_default_ai_data_path()
    common_paths = [
        default_path,
        Path("../ai_data_final"),
        Path("../../ai_data_final"),
        Path("ai_data_final"),
        Path.cwd() / "ai_data_final",
    ]

    # Show current path
    current_path = st.session_state.get('ai_data_path', default_path)
    st.info(f"**Current Path:** `{current_path}`")

    # Quick select from common paths
    st.markdown("#### Quick Select")
    cols = st.columns(2)

    for idx, path in enumerate(common_paths):
        col = cols[idx % 2]
        with col:
            if path.exists():
                status = "✅ Found"
                is_valid, msg, stats = validate_ai_data_path(path)
                file_count = sum(stats.values()) if stats else 0
                button_label = f"{status} - {path.name} ({file_count:,} files)"
                button_type = "primary" if path == default_path else "secondary"
            else:
                status = "❌ Not Found"
                button_label = f"{status} - {path.name}"
                button_type = "secondary"

            if st.button(button_label, key=f"quick_path_{idx}", type=button_type):
                if path.exists():
                    return path
                else:
                    st.error(f"Path does not exist: {path}")

    # Manual path entry
    st.markdown("#### Manual Path Entry")
    manual_path = st.text_input(
        "Enter full path to ai_data_final directory",
        value=str(current_path),
        placeholder=str(default_path),
        help="Enter the absolute path to your ai_data_final directory"
    )

    col1, col2 = st.columns(2)

    with col1:
        if st.button("🔍 Validate Path", type="primary"):
            test_path = Path(manual_path)
            is_valid, message, stats = validate_ai_data_path(test_path)

            if is_valid:
                st.success(message)

                # Show directory structure
                st.markdown("**Directory Structure:**")
                for dir_name, count in stats.items():
                    st.write(f"- `{dir_name}/`: {count:,} JSON files")

                return test_path
            else:
                st.error(message)

    with col2:
        if st.button("🔄 Reset to Default"):
            return default_path

    return None

def show_path_configuration_panel():
    """
    Display comprehensive path configuration panel
    """
    st.markdown("### ⚙️ AI Data Path Configuration")

    # Get current configuration
    default_path = get_default_ai_data_path()
    current_path = st.session_state.get('ai_data_path', default_path)

    # Validate current path
    is_valid, message, stats = validate_ai_data_path(Path(current_path))

    # Display status
    col1, col2, col3 = st.columns([2, 1, 1])

    with col1:
        st.info(f"**Current Path:** `{current_path}`")

    with col2:
        if is_valid:
            st.success("✅ Valid")
        else:
            st.error("❌ Invalid")

    with col3:
        total_files = sum(stats.values()) if stats else 0
        st.metric("JSON Files", f"{total_files:,}")

    # Show detailed stats if valid
    if is_valid and stats:
        with st.expander("📊 Detailed Directory Statistics"):
            for dir_name, count in sorted(stats.items(), key=lambda x: x[1], reverse=True):
                st.write(f"- **{dir_name}**: {count:,} files")

    # Browse button
    if st.button("📁 Browse for AI Data Path", type="primary"):
        st.session_state.show_path_browser = True

    # Show browser if requested
    if st.session_state.get('show_path_browser', False):
        new_path = browse_ai_data_path()

        if new_path:
            st.session_state.ai_data_path = str(new_path)
            st.session_state.show_path_browser = False
            st.success(f"✅ Path updated to: {new_path}")
            st.rerun()

        if st.button("❌ Cancel Browse"):
            st.session_state.show_path_browser = False
            st.rerun()

def get_configured_ai_data_path() -> Path:
    """
    Get the currently configured AI data path

    Returns:
        Path object pointing to ai_data_final
    """
    if 'ai_data_path' in st.session_state:
        configured_path = Path(st.session_state.ai_data_path)
        if configured_path.exists():
            return configured_path

    # Return default
    default_path = get_default_ai_data_path()
    if default_path.exists():
        return default_path

    # Fallback to current directory
    return Path.cwd() / "ai_data_final"

def initialize_ai_data_path():
    """
    Initialize AI data path in session state if not already set
    """
    if 'ai_data_path' not in st.session_state:
        default_path = get_default_ai_data_path()
        st.session_state.ai_data_path = str(default_path)
