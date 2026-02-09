
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

"""
IntelliCV-AI Logo Preview Demo
=============================

This file demonstrates different logo variations for the IntelliCV Admin Portal.
You can run this to see how different text variations look.
"""

import streamlit as st

def preview_logo_variations():
    """Preview different logo text variations"""
    

# Activate Enhanced Sidebar
if ENHANCED_SIDEBAR_AVAILABLE:
    inject_sidebar_css()
    render_enhanced_sidebar()

    st.title("🎨 IntelliCV Logo Variations Preview")
    st.write("Here are different variations of the logo text to help you decide:")
    
    variations = [
        "IntelliCV-AI",
        "IntelliC-CV-AI", 
        "Intelli-CV-AI",
        "IntelliCV AI",
        "IntelliCV•AI",
        "IntelliCV | AI"
    ]
    
    for i, logo_text in enumerate(variations):
        st.write(f"**Option {i+1}:**")
        st.markdown(f"""
        <div style="margin: 10px 0; text-align: center;">
            <div style="
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                border-radius: 12px;
                padding: 8px 12px;
                display: inline-block;
                box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
                border: 2px solid rgba(255, 255, 255, 0.2);
                backdrop-filter: blur(10px);
            ">
                <div style="
                    color: white;
                    font-weight: bold;
                    font-size: 14px;
                    text-shadow: 0 1px 3px rgba(0,0,0,0.3);
                    letter-spacing: 0.5px;
                ">
                    🤖 {logo_text}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.write("---")
    
    st.write("**Current Implementation:** The logo appears on the right-hand side of the admin dashboard header.")
    st.write("**To Change:** Edit the `logo_text` variable in `shared/components.py` line ~35")
    
    st.info("""
    **Recommendation:** 
    - "IntelliCV-AI" looks clean and professional
    - "IntelliC-CV-AI" breaks up the words more but might be harder to read
    - "IntelliCV | AI" has a nice separation with the pipe character
    
    The current implementation uses "IntelliCV-AI" but you can easily change it!
    """)

if __name__ == "__main__":
    preview_logo_variations()