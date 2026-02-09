"""
IntelliCV Auto-Screen System - SANDBOX Version
==============================================

Automatic data screening and AI processing for user login events.
Monitors data directories and processes both existing and new data automatically.

Features:
- Automatic CV/Resume screening on user login
- Background processing of new data uploads
- AI enrichment pipeline integration
- SQLite learning system updates
- Real-time user data quality assessment

Author: IntelliCV AI Team
Purpose: Automated user data screening with AI intelligence
Environment: SANDBOX Admin Portal
"""

import os
import json
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import hashlib

# Import our AI services
try:
    from services.unified_ai_engine import get_unified_ai_engine
    from services.sqlite_manager import get_sqlite_manager
    from services.azure_integration import get_azure_integration
    from services.ai_data_manager import get_ai_data_manager
    from services.ai_feedback_loop import get_feedback_loop_system
    AI_SERVICES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ AI services not available: {e}")
    AI_SERVICES_AVAILABLE = False

class IntelliCVAutoScreenSystem:
    """
    Automatic screening system for user data processing
    """

    def __init__(self):
        """Initialize the auto-screen system"""
        self.data_directories = {
            'centralized': Path('data/centralized'),
            'ai_data_system': Path('ai_data_system'),
            'user_registrations': Path('data/user_registrations'),
            'email_data': Path('data/email_data')
        }

        # Initialize AI services
        self.ai_engine = None
        self.sqlite_manager = None
        self.azure_integration = None
        self.data_manager = None
        self.feedback_system = None

        if AI_SERVICES_AVAILABLE:
            self._initialize_ai_services()

        # Processing statistics
        self.stats = {
            'users_screened': 0,
            'files_processed': 0,
            'ai_analyses_completed': 0,
            'data_quality_scores': [],
            'last_screening_time': None
        }

        # Load existing screening history
        self._load_screening_history()

    def _initialize_ai_services(self):
        """Initialize all AI service components"""
        try:
            self.ai_engine = get_unified_ai_engine()
            self.sqlite_manager = get_sqlite_manager()
            self.azure_integration = get_azure_integration()
            self.data_manager = get_ai_data_manager()
            self.feedback_system = get_feedback_loop_system()
            print("[OK] AI services initialized successfully")
        except Exception as e:
            print(f"[ERROR] Error initializing AI services: {e}")

    def _load_screening_history(self):
        """Load existing screening history from file"""
        history_file = Path('ai_data_system/screening_history.json')
        if history_file.exists():
            try:
                with open(history_file, 'r') as f:
                    saved_stats = json.load(f)
                    self.stats.update(saved_stats)
                print(f"[OK] Loaded screening history: {self.stats['users_screened']} users processed")
            except Exception as e:
                print(f"[WARNING] Could not load screening history: {e}")

    def _save_screening_history(self):
        """Save screening history to file"""
        history_file = Path('ai_data_system/screening_history.json')
        history_file.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(history_file, 'w') as f:
                json.dump(self.stats, f, indent=2, default=str)
            print("[OK] Screening history saved")
        except Exception as e:
            print(f"[ERROR] Error saving screening history: {e}")

    def screen_user_on_login(self, user_id: str, user_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Automatically screen user data when they log in

        Args:
            user_id: Unique user identifier
            user_data: Optional user data dictionary

        Returns:
            Dictionary with screening results
        """
        print(f"🔍 Starting auto-screen for user: {user_id}")

        screening_results = {
            'user_id': user_id,
            'screening_timestamp': datetime.now().isoformat(),
            'files_found': 0,
            'files_processed': 0,
            'ai_analysis_results': [],
            'data_quality_score': 0.0,
            'recommendations': [],
            'processing_status': 'started'
        }

        try:
            # 1. Find all user data files
            user_files = self._find_user_files(user_id)
            screening_results['files_found'] = len(user_files)

            if not user_files:
                screening_results['recommendations'].append("No user files found - encourage data upload")
                screening_results['processing_status'] = 'no_data'
                return screening_results

            # 2. Process each file with AI analysis
            for file_path in user_files:
                try:
                    analysis_result = self._process_file_with_ai(file_path, user_id)
                    if analysis_result:
                        screening_results['ai_analysis_results'].append(analysis_result)
                        screening_results['files_processed'] += 1

                        # Save to SQLite learning system
                        if self.sqlite_manager:
                            learning_data = {
                                'session_id': f"auto_screen_{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                                'processing_mode': 'auto_screen',
                                'input_type': 'user_file',
                                'bayesian_confidence': analysis_result.get('bayesian_confidence', 0.0),
                                'nlp_sentiment': analysis_result.get('nlp_sentiment', 0.0),
                                'fuzzy_logic_score': analysis_result.get('fuzzy_logic_score', 0.0),
                                'llm_coherence': analysis_result.get('llm_coherence', 0.0),
                                'combined_score': analysis_result.get('combined_score', 0.0),
                                'processing_time': analysis_result.get('processing_time', 0.0),
                                'data_size': analysis_result.get('file_size', 0),
                                'model_version': 'auto_screen_v1.0',
                                'metadata': json.dumps({
                                    'user_id': user_id,
                                    'file_name': analysis_result.get('file_name', ''),
                                    'auto_screening': True
                                })
                            }
                            self.sqlite_manager.save_ai_learning_result(learning_data)

                except Exception as e:
                    print(f"❌ Error processing file {file_path}: {e}")
                    screening_results['ai_analysis_results'].append({
                        'file_path': str(file_path),
                        'error': str(e),
                        'status': 'failed'
                    })

            # 3. Calculate overall data quality score
            screening_results['data_quality_score'] = self._calculate_data_quality_score(screening_results['ai_analysis_results'])

            # 4. Generate recommendations
            screening_results['recommendations'] = self._generate_recommendations(screening_results)

            # 5. Update statistics
            self.stats['users_screened'] += 1
            self.stats['files_processed'] += screening_results['files_processed']
            self.stats['ai_analyses_completed'] += len(screening_results['ai_analysis_results'])
            self.stats['data_quality_scores'].append(screening_results['data_quality_score'])
            self.stats['last_screening_time'] = datetime.now().isoformat()

            screening_results['processing_status'] = 'completed'

            # Save results and history
            self._save_screening_results(user_id, screening_results)
            self._save_screening_history()

            print(f"✅ Auto-screening completed for user {user_id}: {screening_results['files_processed']} files processed")

        except Exception as e:
            print(f"❌ Error in auto-screening for user {user_id}: {e}")
            screening_results['processing_status'] = 'error'
            screening_results['error'] = str(e)

        return screening_results

    def _find_user_files(self, user_id: str) -> List[Path]:
        """Find all files associated with a user"""
        user_files = []

        # Search patterns for user files
        search_patterns = [
            f"*{user_id}*",
            f"*{user_id.lower()}*",
            f"*{user_id.upper()}*"
        ]

        # File extensions to look for
        file_extensions = ['.pdf', '.doc', '.docx', '.txt', '.csv', '.json']

        for directory_name, directory_path in self.data_directories.items():
            if directory_path.exists():
                # Search recursively in each directory
                for pattern in search_patterns:
                    for ext in file_extensions:
                        matches = list(directory_path.rglob(f"{pattern}{ext}"))
                        user_files.extend(matches)

                # Also search for files that might contain user data
                for file_path in directory_path.rglob('*'):
                    if file_path.is_file() and file_path.suffix.lower() in file_extensions:
                        # Check if file content might relate to this user
                        if self._file_contains_user_data(file_path, user_id):
                            user_files.append(file_path)

        # Remove duplicates
        return list(set(user_files))

    def _file_contains_user_data(self, file_path: Path, user_id: str) -> bool:
        """Check if a file contains data related to the user"""
        try:
            if file_path.suffix.lower() in ['.txt', '.csv', '.json']:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
                return user_id.lower() in content.lower()
        except Exception:
            pass
        return False

    def _process_file_with_ai(self, file_path: Path, user_id: str) -> Optional[Dict[str, Any]]:
        """Process a single file with AI analysis"""
        try:
            # Basic file information
            file_stats = file_path.stat()
            analysis_result = {
                'file_path': str(file_path),
                'file_name': file_path.name,
                'file_size': file_stats.st_size,
                'file_modified': datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                'processing_time': 0.0
            }

            start_time = datetime.now()

            # Read file content
            if file_path.suffix.lower() in ['.txt', '.csv', '.json']:
                content = file_path.read_text(encoding='utf-8', errors='ignore')
            else:
                # For binary files, just note the file type
                content = f"Binary file: {file_path.suffix}"

            # AI Analysis with unified engine (no simulated scores allowed)
            if self.ai_engine and AI_SERVICES_AVAILABLE:
                try:
                    engine_result = self.ai_engine.process_document_intelligent(
                        str(file_path),
                        run_mode="medium",
                    )
                    analysis_result['ai_analysis_status'] = 'complete'
                    analysis_result['engine_result'] = engine_result
                except Exception as e:
                    print(f"⚠️ AI analysis failed for {file_path}: {e}")
                    analysis_result['ai_analysis_status'] = 'error'
                    analysis_result['error'] = str(e)
            else:
                analysis_result['ai_analysis_status'] = 'unavailable'
                analysis_result['error'] = 'AI services not available'

            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            analysis_result['processing_time'] = processing_time

            return analysis_result

        except Exception as e:
            print(f"❌ Error processing file {file_path}: {e}")
            return {
                'file_path': str(file_path),
                'error': str(e),
                'status': 'failed'
            }

    def _calculate_data_quality_score(self, analysis_results: List[Dict[str, Any]]) -> float:
        """Calculate overall data quality score"""
        if not analysis_results:
            return 0.0

        scores = []
        for result in analysis_results:
            engine_result = result.get('engine_result')
            if isinstance(engine_result, dict):
                score = engine_result.get('combined_score')
                if isinstance(score, (int, float)):
                    scores.append(float(score))

        return sum(scores) / len(scores) if scores else 0.0

    def _generate_recommendations(self, screening_results: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on screening results"""
        recommendations = []

        files_processed = screening_results['files_processed']
        data_quality_score = screening_results['data_quality_score']

        if files_processed == 0:
            recommendations.append("📤 Upload CV/Resume files for AI analysis")
            recommendations.append("📝 Complete profile information for better matching")
        elif files_processed < 3:
            recommendations.append("📄 Consider uploading additional documents for comprehensive analysis")

        if data_quality_score < 0.6:
            recommendations.append("⚠️ Data quality could be improved - consider updating documents")
            recommendations.append("🔧 Review and enhance existing files for better AI processing")
        elif data_quality_score > 0.8:
            recommendations.append("✅ Excellent data quality - ready for advanced AI matching")
            recommendations.append("🎯 Enable premium AI features for enhanced job recommendations")

        # Check for specific issues
        ai_failures = sum(1 for r in screening_results['ai_analysis_results'] if 'error' in r)
        if ai_failures > 0:
            recommendations.append(f"🔧 {ai_failures} files had processing issues - consider file format conversion")

        return recommendations

    def _save_screening_results(self, user_id: str, results: Dict[str, Any]):
        """Save screening results for the user"""
        results_dir = Path('ai_data_system/screening_results')
        results_dir.mkdir(parents=True, exist_ok=True)

        results_file = results_dir / f"{user_id}_screening.json"
        try:
            with open(results_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"✅ Screening results saved for user {user_id}")
        except Exception as e:
            print(f"❌ Error saving screening results: {e}")

    def get_user_screening_status(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get the latest screening status for a user"""
        results_file = Path(f'ai_data_system/screening_results/{user_id}_screening.json')
        if results_file.exists():
            try:
                with open(results_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"❌ Error loading screening status: {e}")
        return None

    def get_system_statistics(self) -> Dict[str, Any]:
        """Get overall system screening statistics"""
        return {
            'total_users_screened': self.stats['users_screened'],
            'total_files_processed': self.stats['files_processed'],
            'total_ai_analyses': self.stats['ai_analyses_completed'],
            'average_data_quality': sum(self.stats['data_quality_scores']) / len(self.stats['data_quality_scores']) if self.stats['data_quality_scores'] else 0,
            'last_screening_time': self.stats['last_screening_time'],
            'ai_services_available': AI_SERVICES_AVAILABLE
        }

    def screen_all_existing_users(self) -> Dict[str, Any]:
        """Screen all existing users in the system"""
        print("🔍 Starting batch screening of all existing users...")

        batch_results = {
            'start_time': datetime.now().isoformat(),
            'users_processed': 0,
            'total_files_processed': 0,
            'errors': [],
            'completion_status': 'in_progress'
        }

        # Find all user registration files
        user_reg_dir = Path('data/user_registrations')
        if user_reg_dir.exists():
            for user_file in user_reg_dir.glob('*.json'):
                try:
                    user_id = user_file.stem
                    print(f"Processing user: {user_id}")

                    screening_result = self.screen_user_on_login(user_id)
                    batch_results['users_processed'] += 1
                    batch_results['total_files_processed'] += screening_result.get('files_processed', 0)

                except Exception as e:
                    error_msg = f"Error processing user {user_file}: {e}"
                    print(f"❌ {error_msg}")
                    batch_results['errors'].append(error_msg)

        batch_results['completion_status'] = 'completed'
        batch_results['end_time'] = datetime.now().isoformat()

        print(f"✅ Batch screening completed: {batch_results['users_processed']} users processed")
        return batch_results

# Global instance
_auto_screen_system = None

def get_auto_screen_system() -> IntelliCVAutoScreenSystem:
    """Get global auto-screen system instance"""
    global _auto_screen_system
    if _auto_screen_system is None:
        _auto_screen_system = IntelliCVAutoScreenSystem()
    return _auto_screen_system

def auto_screen_user(user_id: str, user_data: Dict[str, Any] = None) -> Dict[str, Any]:
    """Convenience function to screen a user automatically"""
    system = get_auto_screen_system()
    return system.screen_user_on_login(user_id, user_data)

def get_screening_statistics() -> Dict[str, Any]:
    """Get overall screening system statistics"""
    system = get_auto_screen_system()
    return system.get_system_statistics()

if __name__ == "__main__":
    # Test the auto-screen system
    system = get_auto_screen_system()
    print("🔍 IntelliCV Auto-Screen System Test")
    print("=" * 40)

    # Test with a sample user
    test_results = system.screen_user_on_login("test_user_001")
    print(f"Test Results: {json.dumps(test_results, indent=2, default=str)}")

    # Show system statistics
    stats = system.get_system_statistics()
    print(f"System Statistics: {json.dumps(stats, indent=2, default=str)}")
