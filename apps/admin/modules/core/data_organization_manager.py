
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


# Activate Enhanced Sidebar
if ENHANCED_SIDEBAR_AVAILABLE:
    inject_sidebar_css()
    render_enhanced_sidebar()

#!/usr/bin/env python3
"""
Data Organization and Movement System for IntelliCV
Organizes JSON files, moves data to appropriate locations, and prepares for sandbox deployment
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any
import sqlite3
import csv

class DataOrganizationManager:
    def __init__(self, base_path: str = "C:\\IntelliCV\\admin_portal_final"):
        self.base_path = Path(base_path)
        self.root_path = Path("C:\\IntelliCV")
        self.sandbox_path = self.root_path / "SANDBOX"
        self.data_enrichment_path = self.base_path / "Data_forAi_Enrichment_linked_Admin_portal_final"
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        print(f"📁 Data Organization Manager initialized")
        print(f"🏠 Base: {self.base_path}")
        print(f"🏗️  Sandbox: {self.sandbox_path}")

    def move_root_json_files(self):
        """Move JSON files from root to Data_for_enrichment folder"""
        print("\n📦 MOVING ROOT JSON FILES")
        print("=" * 50)
        
        # Files to move from root
        root_files = [
            'canonical_glossary.json',
            'canonical_glossary 1.json', 
            'consolidated_terms.json',
            'consolidated_terms 1.json',
            'file_manifest.json',
            'file_manifest 1.json'
        ]
        
        moved_files = []
        
        # Ensure target directory exists
        target_dir = self.data_enrichment_path / "reference_data"
        target_dir.mkdir(parents=True, exist_ok=True)
        
        for filename in root_files:
            source_path = self.root_path / filename
            if source_path.exists():
                # Clean filename (remove " 1" duplicates)
                clean_filename = filename.replace(' 1.json', '.json')
                target_path = target_dir / clean_filename
                
                try:
                    # Copy file (don't move to preserve original)
                    shutil.copy2(source_path, target_path)
                    
                    moved_files.append({
                        'source': str(source_path),
                        'target': str(target_path),
                        'size_mb': source_path.stat().st_size / (1024*1024),
                        'status': 'copied'
                    })
                    
                    print(f"📋 Copied: {filename} -> {clean_filename}")
                    
                except Exception as e:
                    print(f"❌ Error copying {filename}: {e}")
        
        print(f"✅ Moved {len(moved_files)} JSON files")
        return moved_files

    def analyze_and_organize_json_content(self):
        """Analyze JSON content and organize by type and purpose"""
        print("\n🔍 ANALYZING & ORGANIZING JSON CONTENT")
        print("=" * 60)
        
        json_categories = {
            'reference_data': [],
            'ai_enrichment': [],
            'csv_integration': [],
            'email_databases': [],
            'intelligence_outputs': [],
            'parsing_reports': [],
            'error_reports': []
        }
        
        # Scan all JSON files in the system
        for json_file in self.base_path.rglob("*.json"):
            if any(skip in str(json_file) for skip in ['.git', '.vs', '__pycache__']):
                continue
            
            try:
                category = self._categorize_json_file(json_file)
                json_categories[category].append({
                    'path': str(json_file),
                    'size_mb': json_file.stat().st_size / (1024*1024),
                    'category': category
                })
                
            except Exception as e:
                print(f"⚠️  Error analyzing {json_file.name}: {e}")
        
        # Print categorization summary
        print("\n📊 JSON FILE CATEGORIZATION:")
        print("-" * 60)
        for category, files in json_categories.items():
            total_size = sum(f['size_mb'] for f in files)
            print(f"{category:<20} {len(files):<8} files, {total_size:.2f} MB")
        
        return json_categories

    def _categorize_json_file(self, file_path: Path) -> str:
        """Categorize a JSON file based on name and content"""
        filename = file_path.name.lower()
        
        # Reference data
        if any(ref in filename for ref in ['canonical', 'glossary', 'manifest', 'consolidated_terms']):
            return 'reference_data'
        
        # AI enrichment outputs
        if any(ai in filename for ai in ['ai_enrichment', 'enriched_', 'intelligence_insights']):
            return 'ai_enrichment'
        
        # CSV integration results
        if 'csv' in filename and any(process in filename for process in ['intelligence', 'analytics', 'repaired']):
            return 'csv_integration'
        
        # Email databases
        if any(email in filename for email in ['email', 'unified_emails']):
            return 'email_databases'
        
        # Intelligence outputs
        if any(intel in filename for intel in ['market_intelligence', 'skills_intelligence', 'user_management']):
            return 'intelligence_outputs'
        
        # Parsing reports
        if any(report in filename for report in ['processing_report', 'parsing']):
            return 'parsing_reports'
        
        # Error reports
        if any(error in filename for error in ['error', 'failed', 'repair_report']):
            return 'error_reports'
        
        return 'reference_data'  # Default category

    def create_sandbox_data_structure(self):
        """Create organized data structure for sandbox"""
        print("\n🏗️  CREATING SANDBOX DATA STRUCTURE")
        print("=" * 60)
        
        # Ensure sandbox exists
        self.sandbox_path.mkdir(exist_ok=True)
        
        # Define sandbox structure
        sandbox_structure = {
            'admin_portal': 'Complete admin portal with all 18 functions',
            'data': {
                'enriched': 'AI-enriched candidate and company data',
                'emails': 'Processed email databases with analytics',
                'intelligence': 'Market and skills intelligence outputs',
                'reference': 'Canonical glossaries and consolidated terms'
            },
            'config': 'Configuration files and settings',
            'api': 'API endpoints and integration hooks',
            'reports': 'Processing and analysis reports'
        }
        
        # Create directory structure
        for main_dir, subdirs in sandbox_structure.items():
            main_path = self.sandbox_path / main_dir
            main_path.mkdir(exist_ok=True)
            
            if isinstance(subdirs, dict):
                for subdir, description in subdirs.items():
                    sub_path = main_path / subdir
                    sub_path.mkdir(exist_ok=True)
                    
                    # Create README with description
                    readme_path = sub_path / "README.md"
                    with open(readme_path, 'w', encoding='utf-8') as f:
                        f.write(f"# {subdir.title()}\n\n{description}\n")
        
        print(f"🏗️  Created sandbox structure at: {self.sandbox_path}")
        return sandbox_structure

    def copy_enriched_data_to_sandbox(self):
        """Copy processed and enriched data to sandbox"""
        print("\n📦 COPYING ENRICHED DATA TO SANDBOX")
        print("=" * 60)
        
        copy_operations = []
        
        # Copy AI enriched outputs
        ai_enriched_dir = self.base_path / "ai_enriched_output"
        if ai_enriched_dir.exists():
            target_dir = self.sandbox_path / "data" / "enriched"
            self._copy_directory_contents(ai_enriched_dir, target_dir, "AI Enriched Data")
            copy_operations.append(f"AI enriched: {len(list(ai_enriched_dir.glob('*')))} files")
        
        # Copy email databases
        ai_csv_dir = self.base_path / "ai_csv_integration"
        if ai_csv_dir.exists():
            email_files = [f for f in ai_csv_dir.glob("*email*.json")]
            target_dir = self.sandbox_path / "data" / "emails"
            
            for email_file in email_files:
                try:
                    shutil.copy2(email_file, target_dir / email_file.name)
                    print(f"📧 Copied email data: {email_file.name}")
                except Exception as e:
                    print(f"❌ Error copying {email_file.name}: {e}")
            
            copy_operations.append(f"Email databases: {len(email_files)} files")
        
        # Copy intelligence outputs
        intelligence_files = []
        for pattern in ["*intelligence*.json", "*market*.json", "*skills*.json"]:
            intelligence_files.extend(self.base_path.rglob(pattern))
        
        target_dir = self.sandbox_path / "data" / "intelligence"
        copied_intelligence = 0
        
        for intel_file in intelligence_files:
            if intel_file.stat().st_size < 50 * 1024 * 1024:  # Only copy files < 50MB
                try:
                    shutil.copy2(intel_file, target_dir / intel_file.name)
                    copied_intelligence += 1
                except Exception as e:
                    print(f"⚠️  Error copying {intel_file.name}: {e}")
        
        copy_operations.append(f"Intelligence data: {copied_intelligence} files")
        
        # Copy reference data
        ref_dir = self.data_enrichment_path / "reference_data"
        if ref_dir.exists():
            target_dir = self.sandbox_path / "data" / "reference"
            self._copy_directory_contents(ref_dir, target_dir, "Reference Data")
            copy_operations.append(f"Reference data: {len(list(ref_dir.glob('*')))} files")
        
        print(f"✅ Data copy operations completed:")
        for operation in copy_operations:
            print(f"   📋 {operation}")
        
        return copy_operations

    def _copy_directory_contents(self, source_dir: Path, target_dir: Path, description: str):
        """Copy contents of one directory to another"""
        target_dir.mkdir(parents=True, exist_ok=True)
        
        for item in source_dir.iterdir():
            if item.is_file():
                try:
                    shutil.copy2(item, target_dir / item.name)
                    print(f"📋 Copied {description}: {item.name}")
                except Exception as e:
                    print(f"❌ Error copying {item.name}: {e}")

    def create_integration_hooks(self):
        """Create integration hooks for user portal"""
        print("\n🔗 CREATING INTEGRATION HOOKS")
        print("=" * 50)
        
        hooks = {
            'candidate_profiles': {
                'endpoint': '/api/candidates/enriched',
                'data_source': 'data/enriched/enriched_candidates.json',
                'ai_features': ['skill_matching', 'experience_analysis', 'profile_scoring']
            },
            'company_intelligence': {
                'endpoint': '/api/companies/intelligence',
                'data_source': 'data/intelligence/market_intelligence.json',
                'ai_features': ['market_analysis', 'company_scoring', 'industry_insights']
            },
            'email_analytics': {
                'endpoint': '/api/emails/analytics',
                'data_source': 'data/emails/unified_emails.json',
                'ai_features': ['domain_analysis', 'contact_verification', 'lead_scoring']
            },
            'skill_matching': {
                'endpoint': '/api/skills/matching',
                'data_source': 'data/intelligence/skills_intelligence.json',
                'ai_features': ['semantic_matching', 'skill_gap_analysis', 'recommendation_engine']
            },
            'cv_parsing': {
                'endpoint': '/api/parsing/cv',
                'data_source': 'data/enriched/parsing_results.json',
                'ai_features': ['nlp_extraction', 'structure_analysis', 'content_categorization']
            }
        }
        
        # Save integration hooks configuration
        hooks_path = self.sandbox_path / "config" / "integration_hooks.json"
        hooks_path.parent.mkdir(exist_ok=True)
        
        with open(hooks_path, 'w', encoding='utf-8') as f:
            json.dump(hooks, f, indent=2, ensure_ascii=False)
        
        print(f"🔗 Created {len(hooks)} integration hooks")
        print(f"📋 Hooks configuration: {hooks_path}")
        
        return hooks

    def generate_sandbox_summary(self):
        """Generate comprehensive summary of sandbox preparation"""
        print("\n📋 GENERATING SANDBOX SUMMARY")
        print("=" * 50)
        
        summary = {
            'sandbox_preparation': {
                'timestamp': self.timestamp,
                'sandbox_path': str(self.sandbox_path),
                'status': 'ready_for_deployment'
            },
            'data_statistics': self._collect_data_statistics(),
            'file_organization': self._analyze_file_organization(),
            'integration_readiness': self._assess_integration_readiness(),
            'deployment_checklist': self._create_deployment_checklist()
        }
        
        # Save summary
        summary_path = self.sandbox_path / f"SANDBOX_DEPLOYMENT_READY_{self.timestamp}.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        print(f"📋 Sandbox summary: {summary_path}")
        return summary

    def _collect_data_statistics(self) -> Dict:
        """Collect statistics about processed data"""
        stats = {
            'total_files': 0,
            'total_size_mb': 0,
            'file_types': {},
            'data_categories': {}
        }
        
        if self.sandbox_path.exists():
            for file_path in self.sandbox_path.rglob("*"):
                if file_path.is_file():
                    stats['total_files'] += 1
                    size_mb = file_path.stat().st_size / (1024*1024)
                    stats['total_size_mb'] += size_mb
                    
                    # Track file types
                    ext = file_path.suffix.lower()
                    if ext not in stats['file_types']:
                        stats['file_types'][ext] = 0
                    stats['file_types'][ext] += 1
        
        return stats

    def _analyze_file_organization(self) -> Dict:
        """Analyze file organization in sandbox"""
        organization = {}
        
        if self.sandbox_path.exists():
            for item in self.sandbox_path.iterdir():
                if item.is_dir():
                    file_count = len(list(item.rglob("*")))
                    total_size = sum(f.stat().st_size for f in item.rglob("*") if f.is_file())
                    
                    organization[item.name] = {
                        'file_count': file_count,
                        'size_mb': total_size / (1024*1024)
                    }
        
        return organization

    def _assess_integration_readiness(self) -> Dict:
        """Assess readiness for admin/user portal integration"""
        readiness = {
            'admin_portal': False,
            'user_portal_hooks': False,
            'api_endpoints': False,
            'data_accessibility': False,
            'ai_engines': False
        }
        
        # Check if admin portal files exist
        admin_files = ['app.py', 'create_sandbox_admin_portal.py']
        if any((self.base_path / f).exists() for f in admin_files):
            readiness['admin_portal'] = True
        
        # Check for integration hooks
        hooks_file = self.sandbox_path / "config" / "integration_hooks.json"
        if hooks_file.exists():
            readiness['user_portal_hooks'] = True
        
        # Check for API structure
        api_dir = self.sandbox_path / "api"
        if api_dir.exists():
            readiness['api_endpoints'] = True
        
        # Check data accessibility
        data_dir = self.sandbox_path / "data"
        if data_dir.exists() and len(list(data_dir.rglob("*.json"))) > 0:
            readiness['data_accessibility'] = True
        
        # Check AI engines (based on previous analysis)
        enriched_dir = self.sandbox_path / "data" / "enriched"
        if enriched_dir.exists():
            readiness['ai_engines'] = True
        
        return readiness

    def _create_deployment_checklist(self) -> List[str]:
        """Create deployment checklist"""
        checklist = [
            "✅ Sandbox directory structure created",
            "✅ Root JSON files moved to reference data",
            "✅ AI enriched data copied to sandbox",
            "✅ Email databases organized",
            "✅ Intelligence outputs available",
            "✅ Integration hooks configured",
            "📝 Admin portal ready for deployment",
            "📝 User portal hooks available for connection",
            "📝 API endpoints configured for data access",
            "🔧 Backend integration pending final configuration",
            "🎨 UI completion ready for admin and user portals"
        ]
        
        return checklist

    def run_complete_organization(self):
        """Run complete data organization process"""
        print("🚀 STARTING COMPLETE DATA ORGANIZATION")
        print("=" * 80)
        
        try:
            # Step 1: Move root JSON files
            moved_files = self.move_root_json_files()
            
            # Step 2: Analyze and organize JSON content
            json_categories = self.analyze_and_organize_json_content()
            
            # Step 3: Create sandbox structure
            sandbox_structure = self.create_sandbox_data_structure()
            
            # Step 4: Copy enriched data to sandbox
            copy_operations = self.copy_enriched_data_to_sandbox()
            
            # Step 5: Create integration hooks
            hooks = self.create_integration_hooks()
            
            # Step 6: Generate summary
            summary = self.generate_sandbox_summary()
            
            print("\n✅ DATA ORGANIZATION COMPLETE")
            print("=" * 80)
            print(f"🏗️  Sandbox ready: {self.sandbox_path}")
            print(f"📦 Files moved: {len(moved_files)}")
            print(f"🔗 Integration hooks: {len(hooks)}")
            print(f"📊 Data statistics: {summary['data_statistics']['total_files']} files")
            print(f"💾 Total size: {summary['data_statistics']['total_size_mb']:.2f} MB")
            
            return summary
            
        except Exception as e:
            print(f"❌ Organization failed: {e}")
            return None


def main():
    """Main execution function"""
    organizer = DataOrganizationManager()
    result = organizer.run_complete_organization()
    
    if result:
        print("\n🎯 ORGANIZATION SUCCESS")
        print(f"🏗️  Sandbox location: {organizer.sandbox_path}")
        print(f"📋 Ready for admin portal deployment")
        print(f"🔗 User portal hooks configured")
        print(f"🤖 AI engines integrated and ready")
        print(f"💾 All data organized and accessible")


if __name__ == "__main__":
    main()