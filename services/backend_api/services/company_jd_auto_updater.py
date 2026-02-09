"""
company_jd_auto_updater.py
===========================
Automated 180-Day Company Job Description Update System

Monitors user employment history and company database to:
1. Check if companies were searched in last 180 days
2. Auto-search dormant companies when users login/relog
3. Bulk update feature for admin-initiated searches
4. Store JD history for speculative applications

Author: IntelliCV Platform
Created: November 17, 2025
"""

import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class CompanyJDAutoUpdater:
    """Manages automated job description updates with 180-day tracking"""

    def __init__(self, db_path: str = None, jd_storage_path: str = None):
        """
        Initialize the auto-updater

        Args:
            db_path: Path to company tracking database
            jd_storage_path: Path to store job descriptions
        """
        base_path = Path(__file__).parent.parent.parent

        # Database for tracking searches
        if db_path is None:
            db_path = base_path / "admin_portal" / "db" / "company_search_tracker.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        # Storage for job descriptions
        if jd_storage_path is None:
            jd_storage_path = base_path / "ai_data_final" / "job_descriptions"
        self.jd_storage_path = Path(jd_storage_path)
        self.jd_storage_path.mkdir(parents=True, exist_ok=True)

        # Initialize database
        self._initialize_database()

        # 180-day threshold
        self.dormancy_threshold_days = 180

    def _initialize_database(self):
        """Create tracking tables if they don't exist"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Company search history table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS company_search_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT NOT NULL,
                    company_domain TEXT,
                    search_date TIMESTAMP NOT NULL,
                    search_source TEXT,
                    jd_count INTEGER DEFAULT 0,
                    search_method TEXT,
                    success BOOLEAN DEFAULT 1,
                    notes TEXT
                )
            """)

            # Company status tracking
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS company_status (
                    company_name TEXT PRIMARY KEY,
                    company_domain TEXT,
                    last_search_date TIMESTAMP,
                    total_searches INTEGER DEFAULT 0,
                    user_count INTEGER DEFAULT 0,
                    is_dormant BOOLEAN DEFAULT 0,
                    priority_score REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # User company associations (from employment history)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL,
                    company_name TEXT NOT NULL,
                    start_date TEXT,
                    end_date TEXT,
                    job_title TEXT,
                    detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(username, company_name)
                )
            """)

            # Job descriptions archive
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS job_descriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    company_name TEXT NOT NULL,
                    job_title TEXT NOT NULL,
                    job_url TEXT,
                    description_text TEXT,
                    required_skills TEXT,
                    nice_to_have TEXT,
                    tech_stack TEXT,
                    collected_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    source TEXT,
                    is_active BOOLEAN DEFAULT 1
                )
            """)

            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_company_name ON company_status(company_name)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_last_search ON company_status(last_search_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_dormant ON company_status(is_dormant)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_user_company ON user_companies(username, company_name)")

            conn.commit()
            conn.close()
            logger.info("✅ Company JD tracker database initialized")
        except Exception as e:
            logger.error(f"❌ Failed to initialize database: {e}")
            raise

    def check_user_login_trigger(self, username: str, user_profile: Dict) -> List[str]:
        """
        Check if user login should trigger company searches

        Returns list of companies that need updating
        """
        try:
            companies_to_update = []

            # Extract companies from user profile/CV
            user_companies = self._extract_companies_from_profile(user_profile)

            if not user_companies:
                return []

            # Store user-company associations
            self._store_user_companies(username, user_companies)

            # Check which companies need updates
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            threshold_date = datetime.now() - timedelta(days=self.dormancy_threshold_days)

            for company in user_companies:
                company_name = company['name']

                # Check last search date
                cursor.execute("""
                    SELECT last_search_date FROM company_status
                    WHERE company_name = ?
                """, (company_name,))

                result = cursor.fetchone()

                if result is None:
                    # Never searched - high priority
                    companies_to_update.append(company_name)
                    self._update_company_status(company_name, None)
                elif result[0]:
                    last_search = datetime.fromisoformat(result[0])
                    if last_search < threshold_date:
                        # Dormant - needs update
                        companies_to_update.append(company_name)
                else:
                    # No search date - add to queue
                    companies_to_update.append(company_name)

            conn.close()

            if companies_to_update:
                logger.info(f"🔄 User {username} login triggered {len(companies_to_update)} company updates")

            return companies_to_update

        except Exception as e:
            logger.error(f"❌ Error checking user login trigger: {e}")
            return []

    def _extract_companies_from_profile(self, user_profile: Dict) -> List[Dict]:
        """Extract company names from user profile/CV"""
        companies = []

        try:
            # Check different possible locations for employment history
            employment_history = user_profile.get('employment_history', [])

            if not employment_history:
                # Try parsing from parsed_data
                parsed_data = user_profile.get('parsed_data', {})
                if isinstance(parsed_data, str):
                    parsed_data = json.loads(parsed_data)
                employment_history = parsed_data.get('employment_history', [])

            for job in employment_history:
                if isinstance(job, dict):
                    company_name = job.get('company', job.get('employer', ''))
                    if company_name:
                        companies.append({
                            'name': company_name.strip(),
                            'start_date': job.get('start_date', ''),
                            'end_date': job.get('end_date', ''),
                            'job_title': job.get('title', job.get('role', ''))
                        })

            return companies
        except Exception as e:
            logger.error(f"Error extracting companies: {e}")
            return []

    def _store_user_companies(self, username: str, companies: List[Dict]):
        """Store user-company associations"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            for company in companies:
                cursor.execute("""
                    INSERT OR IGNORE INTO user_companies
                    (username, company_name, start_date, end_date, job_title)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    username,
                    company['name'],
                    company.get('start_date', ''),
                    company.get('end_date', ''),
                    company.get('job_title', '')
                ))

                # Update user count for company
                cursor.execute("""
                    UPDATE company_status
                    SET user_count = (
                        SELECT COUNT(DISTINCT username)
                        FROM user_companies
                        WHERE company_name = ?
                    ),
                    updated_at = CURRENT_TIMESTAMP
                    WHERE company_name = ?
                """, (company['name'], company['name']))

            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error storing user companies: {e}")

    def _update_company_status(self, company_name: str, domain: Optional[str] = None):
        """Update or create company status record"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT OR IGNORE INTO company_status (company_name, company_domain)
                VALUES (?, ?)
            """, (company_name, domain))

            # Calculate priority score (based on user count and dormancy)
            cursor.execute("""
                UPDATE company_status
                SET priority_score = user_count * 10 +
                    CASE
                        WHEN last_search_date IS NULL THEN 100
                        WHEN julianday('now') - julianday(last_search_date) > 180 THEN 50
                        ELSE 0
                    END,
                    is_dormant = CASE
                        WHEN last_search_date IS NULL THEN 1
                        WHEN julianday('now') - julianday(last_search_date) > 180 THEN 1
                        ELSE 0
                    END,
                    updated_at = CURRENT_TIMESTAMP
                WHERE company_name = ?
            """, (company_name,))

            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error updating company status: {e}")

    def get_dormant_companies(self, limit: Optional[int] = None, min_user_count: int = 0) -> List[Dict]:
        """
        Get list of dormant companies (not searched in 180 days)

        Args:
            limit: Maximum number to return (None = all)
            min_user_count: Minimum number of users who worked there

        Returns:
            List of dormant companies with metadata
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            query = """
                SELECT
                    company_name,
                    company_domain,
                    last_search_date,
                    total_searches,
                    user_count,
                    priority_score,
                    julianday('now') - julianday(COALESCE(last_search_date, '2000-01-01')) as days_since_search
                FROM company_status
                WHERE is_dormant = 1
                AND user_count >= ?
                ORDER BY priority_score DESC, user_count DESC
            """

            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query, (min_user_count,))
            rows = cursor.fetchall()

            companies = []
            for row in rows:
                companies.append({
                    'company_name': row[0],
                    'company_domain': row[1],
                    'last_search_date': row[2],
                    'total_searches': row[3],
                    'user_count': row[4],
                    'priority_score': row[5],
                    'days_since_search': int(row[6]) if row[6] else 9999
                })

            conn.close()
            return companies

        except Exception as e:
            logger.error(f"Error getting dormant companies: {e}")
            return []

    def record_search_completed(self, company_name: str, jd_count: int,
                               search_method: str = "auto", notes: str = "") -> bool:
        """Record that a company search was completed"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Record in history
            cursor.execute("""
                INSERT INTO company_search_history
                (company_name, search_date, jd_count, search_method, notes)
                VALUES (?, CURRENT_TIMESTAMP, ?, ?, ?)
            """, (company_name, jd_count, search_method, notes))

            # Update company status
            cursor.execute("""
                UPDATE company_status
                SET last_search_date = CURRENT_TIMESTAMP,
                    total_searches = total_searches + 1,
                    is_dormant = 0,
                    priority_score = user_count * 10,
                    updated_at = CURRENT_TIMESTAMP
                WHERE company_name = ?
            """, (company_name,))

            conn.commit()
            conn.close()

            logger.info(f"✅ Recorded search for {company_name}: {jd_count} JDs")
            return True

        except Exception as e:
            logger.error(f"❌ Error recording search: {e}")
            return False

    def store_job_description(self, company_name: str, job_title: str,
                              description_text: str, metadata: Dict) -> bool:
        """Store a scraped job description"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO job_descriptions
                (company_name, job_title, job_url, description_text,
                 required_skills, nice_to_have, tech_stack, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                company_name,
                job_title,
                metadata.get('url', ''),
                description_text,
                json.dumps(metadata.get('required_skills', [])),
                json.dumps(metadata.get('nice_to_have', [])),
                json.dumps(metadata.get('tech_stack', [])),
                metadata.get('source', 'auto_scrape')
            ))

            conn.commit()
            conn.close()

            # Also save to file system
            self._save_jd_to_file(company_name, job_title, description_text, metadata)

            return True

        except Exception as e:
            logger.error(f"Error storing JD: {e}")
            return False

    def _save_jd_to_file(self, company_name: str, job_title: str,
                         description_text: str, metadata: Dict):
        """Save JD to filesystem for AI model access"""
        try:
            # Create company directory
            company_dir = self.jd_storage_path / company_name.replace('/', '_')
            company_dir.mkdir(parents=True, exist_ok=True)

            # Create filename
            safe_title = job_title.replace('/', '_').replace('\\', '_')
            timestamp = datetime.now().strftime('%Y%m%d')
            filename = f"{safe_title}_{timestamp}.json"

            jd_data = {
                'company_name': company_name,
                'job_title': job_title,
                'description': description_text,
                'metadata': metadata,
                'collected_date': datetime.now().isoformat()
            }

            filepath = company_dir / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(jd_data, f, indent=2, ensure_ascii=False)

            logger.info(f"💾 Saved JD to file: {filepath}")

        except Exception as e:
            logger.error(f"Error saving JD to file: {e}")

    def get_company_jd_history(self, company_name: str) -> List[Dict]:
        """Get all stored job descriptions for a company"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                SELECT job_title, description_text, required_skills,
                       nice_to_have, tech_stack, collected_date, job_url
                FROM job_descriptions
                WHERE company_name = ?
                AND is_active = 1
                ORDER BY collected_date DESC
            """, (company_name,))

            rows = cursor.fetchall()
            conn.close()

            jds = []
            for row in rows:
                jds.append({
                    'job_title': row[0],
                    'description': row[1],
                    'required_skills': json.loads(row[2]) if row[2] else [],
                    'nice_to_have': json.loads(row[3]) if row[3] else [],
                    'tech_stack': json.loads(row[4]) if row[4] else [],
                    'collected_date': row[5],
                    'job_url': row[6]
                })

            return jds

        except Exception as e:
            logger.error(f"Error getting JD history: {e}")
            return []

    def get_statistics(self) -> Dict:
        """Get updater statistics"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Total companies tracked
            cursor.execute("SELECT COUNT(*) FROM company_status")
            total_companies = cursor.fetchone()[0]

            # Dormant companies
            cursor.execute("SELECT COUNT(*) FROM company_status WHERE is_dormant = 1")
            dormant_count = cursor.fetchone()[0]

            # Total JDs collected
            cursor.execute("SELECT COUNT(*) FROM job_descriptions WHERE is_active = 1")
            total_jds = cursor.fetchone()[0]

            # Companies with users
            cursor.execute("SELECT COUNT(*) FROM company_status WHERE user_count > 0")
            companies_with_users = cursor.fetchone()[0]

            # Recent searches (last 7 days)
            cursor.execute("""
                SELECT COUNT(*) FROM company_search_history
                WHERE julianday('now') - julianday(search_date) <= 7
            """)
            recent_searches = cursor.fetchone()[0]

            conn.close()

            return {
                'total_companies': total_companies,
                'dormant_companies': dormant_count,
                'active_companies': total_companies - dormant_count,
                'total_job_descriptions': total_jds,
                'companies_with_users': companies_with_users,
                'recent_searches_7d': recent_searches,
                'dormant_percentage': (dormant_count / total_companies * 100) if total_companies > 0 else 0
            }

        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}


# Singleton instance
_auto_updater_instance = None

def get_company_jd_updater() -> CompanyJDAutoUpdater:
    """Get singleton instance of the auto updater"""
    global _auto_updater_instance
    if _auto_updater_instance is None:
        _auto_updater_instance = CompanyJDAutoUpdater()
    return _auto_updater_instance
