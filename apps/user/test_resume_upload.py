"""
Simple Test Script for Resume Upload Page
==========================================
Runs the resume upload page in standalone mode for testing
"""

import streamlit as st
from pathlib import Path
import sys

# Add current directory to path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Configure page
st.set_page_config(
    page_title="Resume Upload Test",
    page_icon="📄",
    layout="wide"
)

# Initialize session state for testing
if 'authenticated_user' not in st.session_state:
    st.session_state.authenticated_user = 'test_user'
    st.session_state.user_id = 'test_123'
    st.session_state.username = 'Test User'
    st.session_state.email = 'test@intellicv.ai'
    st.session_state.subscription_plan = 'monthly'
    st.session_state.subscription_status = 'active'

# Initialize profile data (required for resume upload)
if 'profile_data' not in st.session_state:
    st.session_state.profile_data = {
        'full_name': 'Test User',
        'email': 'test@intellicv.ai',
        'phone': '+1234567890',
        'location': 'New York, NY'
    }

# Initialize resume data with mock AI analysis (simulating processed CV)
if 'resume_data' not in st.session_state:
    # Mock enhanced data based on Dean Cooper CV
    mock_enhanced_data = {
        'skill_mapping': {
            'technical_skills': [
                'Solidworks', 'Keyshot', 'Adobe Photoshop', 'Adobe Illustrator',
                'CAD Modeling', '3D Visualization', 'Prototyping', 'Technical Drawing'
            ],
            'professional_skills': [
                'Product Design', 'Design Research', 'User-Centered Design',
                'Project Management', 'Team Collaboration', 'Problem Solving',
                'Creative Thinking', 'Attention to Detail'
            ]
        },
        'career_suggestions': [
            'Senior Product Designer',
            'Industrial Design Engineer',
            'Lead CAD Designer',
            'Product Development Manager',
            'Design Consultant'
        ],
        'industry_match': [
            'Industrial Design',
            'Product Development',
            'Manufacturing',
            'Consumer Goods',
            'Automotive Design'
        ],
        'market_intelligence': {
            'salary_range': '$65,000 - $95,000',
            'demand_level': 'High',
            'growth_outlook': 'Positive'
        },
        'performance_metrics': {
            'confidence_score': 0.87,
            'experience_level': 'Mid-Level Professional',
            'skill_diversity': 'High',
            'industry_relevance': 'Strong'
        }
    }
    
    st.session_state.resume_data = {
        'filename': 'Dean_Cooper_CV.pdf',
        'content': 'Mock resume content for Dean Cooper - Industrial Designer',
        'file_type': 'application/pdf',
        'file_size': 245000,
        'upload_date': '2025-10-21 14:30:00',
        'processed': True,
        'analysis_ready': True,
        'admin_ai_processed': True,
        'enhanced_data': mock_enhanced_data
    }

# Test banner
st.markdown("""
<div style="background: #667eea; color: white; padding: 1rem; border-radius: 8px; margin-bottom: 2rem;">
    <h2>🧪 Resume Upload Test Mode</h2>
    <p>Testing resume upload with AI parsing, keyword extraction, and summary generation</p>
    <p><strong>Logged in as:</strong> Test User (Monthly Plan)</p>
</div>
""", unsafe_allow_html=True)

# Import and run the resume upload page content
try:
    # Read and execute the resume upload page
    resume_upload_path = current_dir / "pages" / "05_Resume_Upload.py"
    
    if resume_upload_path.exists():
        with open(resume_upload_path, 'r', encoding='utf-8') as f:
            code = f.read()
            
        # Remove the page config and auth check from the code
        code_lines = code.split('\n')
        filtered_lines = []
        skip_until_blank = False
        
        for line in code_lines:
            # Skip page config block
            if 'st.set_page_config' in line:
                skip_until_blank = True
                continue
            
            # Skip authentication check
            if "if not st.session_state.get('authenticated_user'):" in line:
                skip_until_blank = True
                continue
            
            # Skip profile completion check
            if "if profile_completion < 50:" in line:
                skip_until_blank = True
                continue
                
            if skip_until_blank:
                if line.strip() == '' or (line.strip() and not line.startswith(' ')):
                    skip_until_blank = False
                continue
                
            filtered_lines.append(line)
        
        # Execute the filtered code
        exec('\n'.join(filtered_lines), globals())
    else:
        st.error("Resume upload page not found!")
        st.info(f"Looking for: {resume_upload_path}")
        
except Exception as e:
    st.error(f"Error loading resume upload page: {str(e)}")
    import traceback
    st.code(traceback.format_exc())
