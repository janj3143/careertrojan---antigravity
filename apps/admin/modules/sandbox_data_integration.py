
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
Sandbox Data Integration Module
Provides easy access to all enriched data for the admin portal
"""

import json
import sqlite3
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
import streamlit as st

class SandboxDataIntegrator:
    """Integrates all enriched data for sandbox admin portal"""
    
    def __init__(self):
        self.data_root = Path("../../data")
        self.enriched_path = self.data_root / "enriched"
        self.email_path = self.data_root / "emails"  
        self.intelligence_path = self.data_root / "intelligence"
        self.reference_path = self.data_root / "reference"
        
    def get_enriched_candidates(self) -> List[Dict]:
        """Get enriched candidate data"""
        try:
            db_path = self.enriched_path / "comprehensive_enrichment.db"
            if db_path.exists():
                conn = sqlite3.connect(str(db_path))
                df = pd.read_sql_query("SELECT * FROM candidates LIMIT 1000", conn)
                conn.close()
                return df.to_dict('records')
        except Exception as e:

# Activate Enhanced Sidebar
if ENHANCED_SIDEBAR_AVAILABLE:
    inject_sidebar_css()
    render_enhanced_sidebar()

            st.error(f"Error loading candidates: {e}")
        return []
    
    def get_email_analytics(self) -> Dict[str, Any]:
        """Get email analytics data"""
        email_data = {
            'total_emails': 0,
            'domains': {},
            'recent_emails': []
        }
        
        try:
            for email_file in self.email_path.glob("*unified_emails*.json"):
                with open(email_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'emails' in data:
                        email_data['total_emails'] += len(data['emails'])
                        email_data['recent_emails'].extend(data['emails'][:100])
        except Exception as e:
            st.error(f"Error loading emails: {e}")
        
        return email_data
    
    def get_intelligence_summary(self) -> Dict[str, Any]:
        """Get AI intelligence summary"""
        intelligence = {
            'market_insights': 0,
            'skills_analyzed': 0,
            'companies_profiled': 0,
            'keywords_extracted': 0
        }
        
        try:
            # Load intelligence files
            for intel_file in self.intelligence_path.glob("*.json"):
                with open(intel_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    if 'market' in intel_file.name:
                        intelligence['market_insights'] += len(data.get('insights', []))
                    elif 'skills' in intel_file.name:
                        intelligence['skills_analyzed'] += len(data.get('skills', []))
                    elif 'companies' in intel_file.name:
                        intelligence['companies_profiled'] += len(data.get('companies', []))
        except Exception as e:
            st.error(f"Error loading intelligence: {e}")
        
        return intelligence
    
    def get_reference_data(self) -> Dict[str, Any]:
        """Get reference data (glossaries, terms, etc.)"""
        reference = {}
        
        try:
            for ref_file in self.reference_path.glob("*.json"):
                with open(ref_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    reference[ref_file.stem] = data
        except Exception as e:
            st.error(f"Error loading reference data: {e}")
        
        return reference
    
    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """Get comprehensive dashboard metrics"""
        return {
            'candidates': self.get_enriched_candidates()[:10],  # Sample
            'emails': self.get_email_analytics(),
            'intelligence': self.get_intelligence_summary(),
            'reference': self.get_reference_data()
        }

# Global instance for easy access
sandbox_data = SandboxDataIntegrator()
